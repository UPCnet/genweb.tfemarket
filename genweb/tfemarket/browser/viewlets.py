# -*- coding: utf-8 -*-

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five import grok
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
        return self.canManageTFE() or self.canManageSite()

    def canManageTFE(self):
        return checkPermission("genweb.tfemarket.controlpanel", self)
