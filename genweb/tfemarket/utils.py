# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from plone import api
from plone.app.content.browser.folderfactories import _allowedTypes
from Products.CMFCore.utils import getToolByName
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zope.component import getMultiAdapter
from zope.security import checkPermission


def sendMessage(context, fromMsg, toMsg, subject, message):
    context = aq_inner(context)
    mailhost = getToolByName(context, 'MailHost')

    msg = MIMEMultipart()
    msg['From'] = fromMsg
    msg['To'] = toMsg
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))
    mailhost.send(msg)


def getLdapUserData(director):
    """Create a new gengrup user by email. You have to call
       updateUserSitesCatalog to get the new user into the
       user_sites_catalog.
    """

    acl_users = api.portal.get_tool(name='acl_users')

    search_result = acl_users.searchUsers(id=director, exactMatch=True)

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
