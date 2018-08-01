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


def checkPermissionCreateApplications(self, context):
    roles = api.user.get_roles()

    if 'Market Manager' in roles or 'Manager' in roles or 'Teacher' in roles:
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
            return False
        else:
            return True
    else:
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

            result.append({'id': item['codi_prisma'], 'lit': titulacio})

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


def offerIsFromTheTeacher(offer):
    user = api.user.get_current()
    user_roles = user.getRoles()
    if 'Manager' in user_roles or 'Market Manager' in user_roles:
        return True
    else:
        if 'Teacher' in user_roles:
            if user.id in offer.creators:
                return True
    return False
