# -*- coding: utf-8 -*-

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from five import grok
from plone import api
from plone.app.layout.viewlets.interfaces import IPortalTop
from zope.security import checkPermission

from genweb.theme.browser.viewlets import gwPersonalBarViewlet
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer


class genwebTfemarketPersonalBarViewlet(gwPersonalBarViewlet):

    """ Done without jbot as it was failing sometimes randomly """
    grok.name('genweb.personalbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTfemarketLayer)

    index = ViewPageTemplateFile('viewlets_templates/personal_bar.pt')

    def canManageConfig(self):
        return self.canManageUtilsTFE() or self.canManageTFE() or self.canManageSite()

    def canManageTFE(self):
        return checkPermission("genweb.tfemarket.controlpanel", self)

    def canManageUtilsTFE(self):
        user_roles = api.user.get_current().getRoles()
        return 'Manager' in user_roles or 'TFE Teacher' in user_roles or 'TFE Manager' in user_roles
