# -*- coding: utf-8 -*-

import ldap

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from operator import itemgetter
from plone import api
from plone.app.content.browser.folderfactories import _allowedTypes
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.security import checkPermission

from genweb.tfemarket import _
from genweb.tfemarket.controlpanel import ITfemarketSettings
from cgi import escape
from Products.CMFPlone.utils import safe_unicode

from genweb.tfemarket.controlpanel import IBUSSOASettings
import requests


class BusError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def sendMessage(context, fromMsg, toMsg, subject, message, email_charset):
    context = aq_inner(context)
    mailhost = getToolByName(context, 'MailHost')

    msg = MIMEMultipart()
    msg['From'] = fromMsg
    msg['To'] = toMsg
    msg['Subject'] = escape(safe_unicode(subject))
    msg['charset'] = email_charset

    msg.attach(MIMEText(message, 'plain', email_charset))
    mailhost.send(msg)


def getLdapExactUserData(user, typology=None):
    users = getLdapUserData(user, typology)
    for userLDAP in users:
        if userLDAP['id'] == user:
            return userLDAP
    return None


def getLdapUserData(user, typology=None):
    acl_users = api.portal.get_tool(name='acl_users')
    if not typology:
        search_result = acl_users.searchUsers(id=user, exactMatch=True)
    else:
        search_result = acl_users.searchUsers(id=user, exactMatch=True, typology=typology)
    return search_result


def checkPermissionCreateApplications(self, context, errors=False):
    roles = api.user.get_roles()

    if 'TFE Manager' in roles or 'Manager' in roles or 'TFE Teacher' in roles:
        if errors:
            self.context.plone_utils.addPortalMessage(_(u"You don't have permission for create a application."), 'error')
        return False

    wf_tool = getToolByName(context, 'portal_workflow')
    offer_workflow = wf_tool.getWorkflowsFor(context)[0].id
    offer_status = wf_tool.getStatusOf(offer_workflow, context)
    if 'Anonymous' in roles and offer_status['review_state'] == 'public':
        return True

    if checkPermissionCreateObject(self, context, 'genweb.tfemarket.application'):
        catalog = api.portal.get_tool(name='portal_catalog')
        from genweb.tfemarket.content.application import IApplication
        items = catalog(object_provides=IApplication.__identifier__,
                        Creator=api.user.get_current().id)

        results = []
        for item in items:
            if item.review_state not in ['cancelled', 'rejected', 'renounced']:
                results.append(item)

        if len(results) > 0:
            if errors:
                self.context.plone_utils.addPortalMessage(_(u"You have already created an application. You can see it at the top of the market page."), 'error')
            return False
        else:
            return True
    else:
        if errors:
            self.context.plone_utils.addPortalMessage(_(u"You don't have permission for create a application."), 'error')
        return False


def checkPermissionCreateOffers(self, context):
    return checkPermissionCreateObject(self, context, 'genweb.tfemarket.offer')


def checkPermissionCreateObject(self, context, objectID):
    if checkPermission('cmf.AddPortalContent', context):
        for item in _allowedTypes(self.request, context):
            if item.id == objectID:
                return True
    return False


def getDegrees():
    registry = queryUtility(IRegistry)
    tfe_tool = registry.forInterface(ITfemarketSettings)
    current_language = api.portal.get_current_language()

    result = []
    if tfe_tool.titulacions_table:
        for item in tfe_tool.titulacions_table:
            titulacio = str(item['plan_year']) + " - "
            if current_language == 'ca':
                titulacio += item['titulacio_ca']
            elif current_language == 'es':
                titulacio += item['titulacio_es']
            else:
                titulacio += item['titulacio_en']

            result.append({'id': item['codi_mec'], 'lit': titulacio})

    result = sorted(result, key=itemgetter('lit'))
    result.insert(0, {'id': 'a', 'lit': _(u"All")})
    return result


def getDegreeLiteralFromId(id):
    degrees = getDegrees()
    degree = _(u'Degree deleted')
    result = [item['lit'] for item in degrees if item['id'] == id]
    if result:
        degree = result[0]
    return degree


def getAllApplicationsFromOffer(offer):
    from genweb.tfemarket.content.application import IApplication
    catalog = api.portal.get_tool(name='portal_catalog')
    values = catalog(path={'query': '/'.join(offer.getPhysicalPath()), 'depth': 1},
                     object_provides=IApplication.__identifier__)
    return values


def getApplicationsFromContent(content):
    return content.contentValues(filter={'portal_type': 'genweb.tfemarket.application'})


def checkOfferhasValidApplications(offer):
    wf_tool = getToolByName(offer, 'portal_workflow')
    for item in getApplicationsFromContent(offer):
        application_workflow = wf_tool.getWorkflowsFor(item)[0].id
        application_status = wf_tool.getStatusOf(application_workflow, item)
        if application_status['review_state'] != 'cancelled':
            return True
    return False


def checkOfferhasConfirmedApplications(offer):
    for item in getAllApplicationsFromOffer(offer):
        if item.review_state == 'confirmed':
            return True
    return False


def LDAPSearch(self, query, isQueryAlreadyMade=False):
    def return_dict(ok, content):
        return {'ok': ok, 'content': content}

    def create_query(query):
        fields = ['sn', 'cn']
        return '(|' + ''.join('(%s=%s)' % (fieldname, query) for fieldname in fields) + ')'

    if not query:
        return return_dict(False, 'Query should not be empty')

    result_set = []
    acl_users = getToolByName(self.context, 'acl_users').ldapUPC.acl_users
    ldap_pwd = acl_users._bindpwd
    ldap_binduid = acl_users._binduid
    ldap_server = acl_users.getServers()[0]
    server = "%s://%s:%s" % (ldap_server['protocol'], ldap_server['host'], ldap_server['port'])
    try:
        ldapservice = ldap.initialize(server)
        ldapservice.simple_bind_s(ldap_binduid, ldap_pwd)
        ldapservice.protocol_version = ldap.VERSION3
        ldapservice.op_timeout = ldap_server['op_timeout']
        ldap_result_id = ldapservice.search(
            acl_users.users_base,
            acl_users.users_scope,
            query if isQueryAlreadyMade else create_query(query),
            None
        )
        while True:
            result_type, result_data = ldapservice.result(ldap_result_id, 0)
            if result_data == []:
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    person_info = result_data[0][1]
                    returnfields = [
                        ('username', 'cn'),
                        ('dni', 'DNIpassport'),
                        ('segmentation', 'segmentation'),
                        ('typology', 'typology'),
                        ('unit', 'unit'),
                        ('idorigen', 'idorigen'),
                        ('fullname', 'sn'),
                        ('email', 'mail'),
                        ('phone', 'telephoneNumber')
                    ]
                    result_set.append({key: person_info.get(value, ['']) for key, value in returnfields})

    except ldap.LDAPError as e:
        return return_dict(False, e[0])
    else:
        return return_dict(True, result_set)
    finally:
        ldapservice.unbind_s()


def isTeachersOffer(offer):
    user = api.user.get_current()
    user_roles = user.getRoles()
    if 'Manager' in user_roles or 'TFE Manager' in user_roles:
        return True
    else:
        if 'TFE Teacher' in user_roles:
            if user.id in offer.creators:
                return True
    return False


def getStudentData(self, item, user):
    registry = queryUtility(IRegistry)
    bussoa_tool = registry.forInterface(IBUSSOASettings)
    tfe_tool = registry.forInterface(ITfemarketSettings)
    bussoa_url = bussoa_tool.bus_url
    bussoa_user = bussoa_tool.bus_user
    bussoa_pass = bussoa_tool.bus_password
    bussoa_apikey = bussoa_tool.bus_apikey
    tipus_alta = tfe_tool.enroll_type

    student_data = {}

    keys = ['segmentation', 'unit', 'typology', 'idorigen']
    vinculacio = []
    result = LDAPSearch(self, user)

    if result['ok']:

        if not checkPermissionCreateApplications(self, item, True):
            return None

        user = result['content'][0]
        student_data = {
            'offer_id': item.offer_id,
            'offer_title': item.title,
            'fullname': user['fullname'],
            'dni': user['dni'],
            'email': user['email']
        }

        if 'telephoneNumber' in user:
            student_data.update({'phone': user['phone']})

        for key in keys:
            for ind, i in enumerate(user[key]):
                try:
                    vinculacio[ind].update({key: i})
                except IndexError:
                    vinculacio.append({key: i})

        # isStudent = (True for item in vinculacio if item['typology'] == 'EST')

        # if True in isStudent:

        #     for vinc in vinculacio:
        #         if vinc['typology'] == 'EST':
        #             id_prisma = vinc['idorigen']
        #             student_data.update({'idPrisma': id_prisma})
        #             break
        #
        #         id_prisma = student_data['idPrisma']
        #         numDocument = student_data['dni']

        # ##### TEST USERS

        list_test = [{'id_prisma': '2998045', 'numDocument': '8159297'},
                     {'id_prisma': '2982486', 'numDocument': '77622127W'},
                     {'id_prisma': '2967147', 'numDocument': '47938723F'},
                     {'id_prisma': '2961841', 'numDocument': '41563763A'},
                     {'id_prisma': '2961785', 'numDocument': 'AU291007'},
                     {'id_prisma': '2961784', 'numDocument': 'AT568277'},
                     {'id_prisma': '2961767', 'numDocument': 'G25336680'},
                     {'id_prisma': '2961765', 'numDocument': '02740852B'},
                     {'id_prisma': '2961713', 'numDocument': '46627876E'},
                     {'id_prisma': '2961712', 'numDocument': '52886228M'},
                     {'id_prisma': '2951347', 'numDocument': 'L42366646'},
                     {'id_prisma': '2951346', 'numDocument': 'Y5844115J'},
                     {'id_prisma': '2951342', 'numDocument': '46556388H'},
                     {'id_prisma': '2940875', 'numDocument': '39959762E'},
                     {'id_prisma': '2935735', 'numDocument': 'YB0249756'},
                     {'id_prisma': '2935708', 'numDocument': 'Y5556099A'},
                     {'id_prisma': '2930505', 'numDocument': '29206385L'},
                     {'id_prisma': '2930372', 'numDocument': 'E84238756'},
                     {'id_prisma': '2919893', 'numDocument': 'Y5686213Y'},
                     {'id_prisma': '2914799', 'numDocument': 'Y5716521T'},
                     {'id_prisma': '2399710', 'numDocument': '23820394F'},
                     {'id_prisma': '2904226', 'numDocument': '48099022L'},
                     {'id_prisma': '2904225', 'numDocument': '46499140V'},
                     {'id_prisma': '2904224', 'numDocument': 'X3870598C'},
                     {'id_prisma': '2904222', 'numDocument': '49950509Y'},
                     {'id_prisma': '2904221', 'numDocument': '45128621E'},
                     {'id_prisma': '2904219', 'numDocument': 'X7747565S'},
                     {'id_prisma': '2904218', 'numDocument': '48060556D'},
                     {'id_prisma': '2904217', 'numDocument': '41012702E'},
                     {'id_prisma': '2904216', 'numDocument': 'X8639060F'},
                     {'id_prisma': '2904215', 'numDocument': 'X7270981Z'},
                     {'id_prisma': '2904213', 'numDocument': '26296240H'},
                     {'id_prisma': '2904212', 'numDocument': '21785587X'},
                     {'id_prisma': '2904211', 'numDocument': '49896766Z'},
                     {'id_prisma': '2904210', 'numDocument': '49220782T'},
                     {'id_prisma': '2904209', 'numDocument': '43576278H'},
                     {'id_prisma': '2904208', 'numDocument': '53338642D'},
                     {'id_prisma': '2904207', 'numDocument': '47665484P'},
                     {'id_prisma': '2904206', 'numDocument': '39410088W'},
                     {'id_prisma': '2904205', 'numDocument': '21783945R'},
                     {'id_prisma': '2904204', 'numDocument': '49242735B'},
                     {'id_prisma': '2904203', 'numDocument': '49286498M'},
                     {'id_prisma': '2904202', 'numDocument': '47986461C'},
                     {'id_prisma': '2904201', 'numDocument': '23922430S'},
                     {'id_prisma': '2904199', 'numDocument': '49188088N'},
                     {'id_prisma': '2904198', 'numDocument': '49550281R'},
                     {'id_prisma': '2904197', 'numDocument': '46420112V'},
                     {'id_prisma': '2904195', 'numDocument': '53839907N'},
                     {'id_prisma': '2904194', 'numDocument': '26611655B'},
                     {'id_prisma': '2904193', 'numDocument': 'X8793173C'},
                     {'id_prisma': '2904189', 'numDocument': '21776934M'},
                     {'id_prisma': '2904188', 'numDocument': '41015682N'},
                     {'id_prisma': '2904187', 'numDocument': '54805136T'},
                     {'id_prisma': '2904186', 'numDocument': '46489014B'},
                     {'id_prisma': '2904185', 'numDocument': '41015835G'},
                     {'id_prisma': '2898608', 'numDocument': 'L1CC9644G'},
                     {'id_prisma': '2898462', 'numDocument': '110723998'},
                     {'id_prisma': '2898446', 'numDocument': 'AR686284'},
                     {'id_prisma': '2898372', 'numDocument': '49884929E'},
                     {'id_prisma': '2898371', 'numDocument': '77620741L'},
                     {'id_prisma': '2898370', 'numDocument': 'Y4322442C'},
                     {'id_prisma': '2898316', 'numDocument': 'G24908009'},
                     {'id_prisma': '2898315', 'numDocument': 'Y5352690Y'},
                     {'id_prisma': '2898299', 'numDocument': '29219070P'},
                     {'id_prisma': '2898292', 'numDocument': 'L36Y3ZM8P'},
                     {'id_prisma': '2898291', 'numDocument': 'Y5699778R'},
                     {'id_prisma': '2898290', 'numDocument': '70079742F'},
                     {'id_prisma': '2898289', 'numDocument': '43592574F'},
                     {'id_prisma': '2898286', 'numDocument': '34939140'},
                     {'id_prisma': '2898282', 'numDocument': 'X9339129W'},
                     {'id_prisma': '2898281', 'numDocument': '53766960K'},
                     {'id_prisma': '2898280', 'numDocument': '72806060C'},
                     {'id_prisma': '2898277', 'numDocument': 'G24770892'},
                     {'id_prisma': '2399709', 'numDocument': '78102902P'},
                     {'id_prisma': '2399708', 'numDocument': 'X7038956J'},
                     {'id_prisma': '2399705', 'numDocument': '23818976S'},
                     {'id_prisma': '2399704', 'numDocument': '78856215W'},
                     {'id_prisma': '2399702', 'numDocument': '46492011H'},
                     {'id_prisma': '2399698', 'numDocument': '39424479H'},
                     {'id_prisma': '2399697', 'numDocument': '53835049F'},
                     {'id_prisma': '2399696', 'numDocument': '39425307H'},
                     {'id_prisma': '2399695', 'numDocument': '48130820P'},
                     {'id_prisma': '2399694', 'numDocument': '48168326R'},
                     {'id_prisma': '2399693', 'numDocument': '47923214T'}]

        from random import randint
        test_user = list_test[randint(0, len(list_test) - 1)]
        id_prisma = test_user['id_prisma']
        numDocument = test_user['numDocument']

        student_data.update({'idPrisma': id_prisma})
        student_data.update({'dni': numDocument})
        student_data.update({'fullname': 'USUARI DE TEST'})

        # #####

        res_data = requests.get(bussoa_url + "/%s" % id_prisma + '?tipusAltaTFE=' + "%s" % tipus_alta + '&numDocument=' + "%s" % numDocument, headers={'apikey': bussoa_apikey}, auth=(bussoa_user, bussoa_pass))

        if res_data.ok:
            data = res_data.json()
            num_expedients = data['llistatExpedients']

            if num_expedients:
                for exp in num_expedients:
                    if exp['codiMecPrograma'] in item.degree:
                        student_data.update({'degree_id': exp['codiMecPrograma']})
                        student_data.update({'degree_title': getDegreeLiteralFromId(exp['codiMecPrograma'])})

                if 'degree_id' not in student_data.keys():
                    self.context.plone_utils.addPortalMessage("Ninguna de tus titulaciones coincide con la de la oferta", 'error')
                    return None
            else:
                self.context.plone_utils.addPortalMessage(_(u"No tens número d'expedient a Prisma"), 'error')
                return None
        else:
            status_code = res_data.status_code
            reason = res_data.reason
            self.context.plone_utils.addPortalMessage(_(u"PRISMA id not found at PRISMA. %s" % (str(status_code) + ' ' + reason)), 'error')
            return None
        # else:
        #     self.context.plone_utils.addPortalMessage(_(u"No tens viculació d'ESTUDIANT"), 'error')
        #     return None
    else:
        self.context.plone_utils.addPortalMessage(_(u"Usuari no trobat en el Ldap"), 'error')
        return None

    return student_data
