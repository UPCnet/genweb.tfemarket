# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five import grok
from plone import api
from plone.app.layout.viewlets.interfaces import IAboveContent
from plone.app.layout.viewlets.interfaces import IAboveContentTitle
from plone.app.layout.viewlets.interfaces import IPortalTop
from zope.component import getMultiAdapter
from zope.interface import Interface

from genweb.theme.browser.viewlets import gwPersonalBarViewlet

from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer


class genwebTfemarketPersonalBarViewlet(gwPersonalBarViewlet):
    """ Done without jbot as it was failing sometimes randomly """
    grok.name('genweb.personalbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTfemarketLayer)

    index = ViewPageTemplateFile('viewlets_templates/personal_bar.pt')


class infoTfemarket(grok.Viewlet):
    grok.viewletmanager(IAboveContentTitle)
    grok.context(Interface)
    grok.name('genweb.tfemarket.info')
    grok.template('infoTfemarket')
    grok.layer(IGenwebTfemarketLayer)

    def viewInfoTfeMarket(self):
        validTypes = ['genweb.tfemarket.market',
                      'genweb.tfemarket.offer',
                      'genweb.tfemarket.application']
        if self.context.portal_type in validTypes:
            return True
        return False

    def urlInfo(self):
        url = ""
        portal_type = self.context.portal_type
        if portal_type == 'genweb.tfemarket.market':
            url = self.context.absolute_url() + "/manual-dus"
        elif portal_type == 'genweb.tfemarket.offer':
            url = self.context.getParentNode().absolute_url() + "/manual-dus"
        elif portal_type == 'genweb.tfemarket.application':
            url = self.context.getParentNode().getParentNode().absolute_url() + "/manual-dus"
        return url
