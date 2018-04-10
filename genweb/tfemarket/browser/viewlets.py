# -*- coding: utf-8 -*-
from five import grok
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from zope.interface import Interface

from plone import api
from plone.app.layout.viewlets.interfaces import IAboveContent

from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from genweb.tfemarket.content.application import IApplication


class errorCreateApplication(grok.Viewlet):
    grok.viewletmanager(IAboveContent)
    grok.context(Interface)
    grok.template('errorCreateApplication')
    grok.require('cmf.ManagePortal')
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
