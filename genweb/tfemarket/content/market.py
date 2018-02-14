# -*- coding: utf-8 -*-

from plone.directives import form
from plone import api
from five import grok
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.content.application import IApplication

grok.templatedir("templates")


class IMarket(form.Schema):
    """ Folder that contains all the TFE's
    """


class View(grok.View):
    grok.context(IMarket)
    grok.template('market_view')

    def getCatalog(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        return catalog

    def getOffers(self):
        catalog = self.getCatalog()

        results = []

        market_path = "/".join(self.context.getPhysicalPath())
        values = catalog(path=market_path, object_provides=IOffer.__identifier__)

        for item in values:
            results.append(dict(title=item.Title,
                                state=item.review_state,
                                path=item.getPhysicalPath))

        return results

    def getApplications(self, offer):
        catalog = self.getCatalog()

        results = []

        offer_path = "/".join(offer.getPhysicalPath())
        values = catalog(path=offer_path, object_provides=IApplication.__identifier__)

        for item in values:
            results.append(dict(title=item.Title,
                                state=item.review_state))

        return results
