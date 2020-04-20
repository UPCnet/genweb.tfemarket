# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

from cgi import escape
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from operator import itemgetter
from plone import api
from plone.app.content.browser.folderfactories import _allowedTypes
from plone.memoize import ram
from plone.registry.interfaces import IRegistry
from time import time
from zope.component import queryUtility
from zope.security import checkPermission

from genweb.tfemarket import _
from genweb.tfemarket.controlpanel import IBUSSOASettings
from genweb.tfemarket.controlpanel import IIdentitatDigitalSettings
from genweb.tfemarket.controlpanel import ITfemarketSettings

import json
import requests


# @ram.cache(lambda *args: time() // (60 * 60))
def getTokenIdentitatDigital():
    registry = queryUtility(IRegistry)
    identitat_digital_tool = registry.forInterface(IIdentitatDigitalSettings)
    urlGetToken = identitat_digital_tool.identitat_url + '/gcontrol/rest/acls/processos?idProces='
    idProces = identitat_digital_tool.identitat_apikey
    return requests.post(urlGetToken + idProces)


def getDadesEst(self, cn, token):
    registry = queryUtility(IRegistry)
    identitat_digital_tool = registry.forInterface(IIdentitatDigitalSettings)
    urlGetPerson = identitat_digital_tool.identitat_url + '/gcontrol/rest/externs/persones/' + cn.id + '/cn'
    headers = {'TOKEN': token}
    return requests.get(urlGetPerson, headers=headers)


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

    if 'TFE Manager' in roles or 'TFE Teacher' in roles:
        if errors:
            self.context.plone_utils.addPortalMessage(_(u"You don't have permission for create a application."), 'error')
        return False

    wf_tool = getToolByName(context, 'portal_workflow')
    offer_workflow = wf_tool.getWorkflowsFor(context)[0].id
    offer_status = wf_tool.getStatusOf(offer_workflow, context)

    if 'Anonymous' in roles and offer_status['review_state'] == 'public':
        return True

    return checkPermissionCreateObject(self, context, 'genweb.tfemarket.application')


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


def checkOfferhasAssign(offer):
    confirmed = False
    wf_tool = getToolByName(offer, 'portal_workflow')
    for item in getApplicationsFromContent(offer):
        application_workflow = wf_tool.getWorkflowsFor(item)[0].id
        application_status = wf_tool.getStatusOf(application_workflow, item)
        if application_status['review_state'] == 'accepted' or application_status['review_state'] == 'requested':
            return False
        elif application_status['review_state'] == 'confirmed':
            confirmed = True
    return confirmed


def checkOfferhasConfirmedApplications(offer):
    for item in getAllApplicationsFromOffer(offer):
        if item.review_state == 'confirmed':
            return True
    return False


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


def isManager():
    user = api.user.get_current()
    user_roles = user.getRoles()
    return user.id == 'admin' or 'Manager' in user_roles or 'TFE Manager' in user_roles


def getStudentData(self, item, user):

    if not checkPermissionCreateApplications(self, item, True):
        return None

    result = getTokenIdentitatDigital()
    if result.status_code == 201:
        token = json.loads(result.content)['tokenAcl']

        result = getDadesEst(self, user, token)
        if result.status_code == 200:
            est = json.loads(result.content)
            est_colectius = est['uePerfil']

            for col in est_colectius:
                if col['perfilId'] in ['EST', 'ESTMASTER']:
                    student_data = {
                        'offer_id': item.offer_id,
                        'offer_title': item.title,
                        'dni': str(est['document']),
                        'email': str(est['emailPreferent']),
                        'idPrisma': str(col['idOrigen']),
                        'degrees': []
                    }

                    if 'cognom2' in est:
                        fullname = str(est['nom']) + ' ' + str(est['cognom1']) + ' ' + str(est['cognom2'])
                        student_data.update({'fullname': fullname})

                    else:
                        fullname = str(est['nom']) + ' ' + str(est['cognom1'])
                        student_data.update({'fullname': fullname})

                    id_prisma = student_data['idPrisma']
                    numDocument = student_data['dni']

                    registry = queryUtility(IRegistry)
                    bussoa_tool = registry.forInterface(IBUSSOASettings)
                    tfe_tool = registry.forInterface(ITfemarketSettings)
                    bussoa_url = bussoa_tool.bus_url
                    bussoa_user = bussoa_tool.bus_user
                    bussoa_pass = bussoa_tool.bus_password
                    bussoa_apikey = bussoa_tool.bus_apikey
                    tipus_alta = tfe_tool.enroll_type

                    res_data = requests.get(bussoa_url + "/%s" % id_prisma + '?tipusAltaTFE=' + "%s" % tipus_alta + '&numDocument=' + "%s" % numDocument, headers={'apikey': bussoa_apikey}, auth=(bussoa_user, bussoa_pass))

                    data = res_data.json()
                    if res_data.ok:

                        llistat_expedients = data['llistatExpedients']

                        catalog = api.portal.get_tool(name='portal_catalog')
                        from genweb.tfemarket.content.application import IApplication
                        items = catalog(object_provides=IApplication.__identifier__,
                                        Creator=api.user.get_current().id)

                        llistat_solicituds_actives_usuari = []
                        for useritem in items:
                            if useritem.review_state not in ['cancelled', 'rejected', 'renounced']:
                                llistat_solicituds_actives_usuari.append(useritem.getObject().degree_id)

                        for expedient in llistat_expedients:

                            if expedient['codiMecPrograma'] in item.degree and expedient['potMatricularTFE'] == 'S' and expedient['codiMecPrograma'] not in llistat_solicituds_actives_usuari:
                                student_data['degrees'].append({
                                    'degree_id': expedient['codiMecPrograma'],
                                    'degree_title': getDegreeLiteralFromId(expedient['codiMecPrograma']),
                                    'codi_expedient': expedient['codiExpedient']})

                                return student_data

                        self.context.plone_utils.addPortalMessage(_(u"El treball que vols sol·licitar no està ofertat per a la titulació que curses o ja has sol·licitat una amb aquesta mateixa titulació. Contacta amb la secretaria del teu centre."), 'error')
                        return None
                    else:
                        reason = data['resultat']
                        self.context.plone_utils.addPortalMessage(_(u"PRISMA: %s" % reason), 'error')
                        return None

            self.context.plone_utils.addPortalMessage(_(u"VINCULACIÓ: No hem trobat la teva vinculació com a d'ESTUDIANT. Contacta amb la teva secretaria."), 'error')
            return None
        else:
            self.context.plone_utils.addPortalMessage(_(u"DIRECTORI: Usuari no trobat en al directori"), 'error')
            return None
    else:
        self.context.plone_utils.addPortalMessage(_(u"IDENTITAT DIGITAL: %s" % result.status_code), 'error')
        return None
