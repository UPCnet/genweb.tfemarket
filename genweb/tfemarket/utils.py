# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from operator import itemgetter
from plone import api
from plone.app.content.browser.folderfactories import _allowedTypes
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.security import checkPermission

from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket import _


def sendMessage(context, fromMsg, toMsg, subject, message):
    context = aq_inner(context)
    mailhost = getToolByName(context, 'MailHost')

    msg = MIMEMultipart()
    msg['From'] = fromMsg
    msg['To'] = toMsg
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))
    mailhost.send(msg)


def getLdapUserData(user):
    """Create a new gengrup user by email. You have to call
       updateUserSitesCatalog to get the new user into the
       user_sites_catalog.
    """

    acl_users = api.portal.get_tool(name='acl_users')
    search_result = acl_users.searchUsers(id=user, exactMatch=True)
    return search_result


def checkPermissionCreateApplications(self, context):
    roles = api.user.get_roles()
    if 'Market Manager' not in roles and 'Manager' not in roles:
        if checkPermissionCreateObject(self, context, 'genweb.tfemarket.application'):
            catalog = api.portal.get_tool(name='portal_catalog')
            from genweb.tfemarket.content.application import IApplication
            items = catalog(object_provides=IApplication.__identifier__,
                            Creator=api.user.get_current().id)

            results = []
            for item in items:
                if item.review_state not in ['cancelled', 'rejected']:
                    results.append(item)

            if len(results) > 0:
                return False
            else:
                return True
        else:
            return False
    else:
        return True


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
