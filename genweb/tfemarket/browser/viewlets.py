# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from five import grok
from plone import api
from plone.app.layout.viewlets.interfaces import IAboveContent
from plone.app.layout.viewlets.interfaces import IAboveContentTitle
from zope.component import getMultiAdapter
from zope.interface import Interface

from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer


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
        return "https://serveistic.upc.edu/ca"


class errorCreateApplication(grok.Viewlet):
    grok.viewletmanager(IAboveContent)
    grok.context(Interface)
    grok.name('genweb.tfemarket.errorcreateapplication')
    grok.template('errorCreateApplication')
    grok.layer(IGenwebTfemarketLayer)

    def getApplicationUrl(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        results = []
        values = catalog(object_provides=IApplication.__identifier__,
                         Creator=api.user.get_current().id)

        for item in values:
            if item.review_state not in ['cancelled', 'rejected']:
                return item.getURL()

        return ""
