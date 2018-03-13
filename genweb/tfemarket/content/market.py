# -*- coding: utf-8 -*-

from plone.directives import form
from plone import api
from five import grok
from genweb.tfemarket import _
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.content.application import IApplication

grok.templatedir("templates")


class IMarket(form.Schema):
    """ Folder that contains all the TFE's
    """


class View(grok.View):
    grok.context(IMarket)
    grok.template('market_view')

    def filterResults(self, results):
        filters = self.request.form
        delete = []
        # import ipdb; ipdb.set_trace()
        for item in results:
            if len(filters['title']) > 2 and not item['title'].lower().startswith(filters['title'].lower()):
               delete.append(item)
               continue

            if not filters['certification'] == 'all' and not filters['certification'] == item:
                delete.append(item)
                continue

        # for item in delete:
        #     results.pop(item)

        return results

    def getOffers(self):
        catalog = api.portal.get_tool(name='portal_catalog')

        path = self.context.getPhysicalPath()
        path = "/".join(path)
        values = catalog(path={'query': path, 'depth': 1},
                         object_provides=IOffer.__identifier__)

        results = []
        for item in values:
            results.append(dict(title=item.Title,
                                state=item.review_state,
                                url=item.getURL(),
                                path=item.getPath(),
                                ))

        if not self.request.form == {}:
            results = self.filterResults(results)

        return results

    def getApplications(self, offer):
        catalog = api.portal.get_tool(name='portal_catalog')
        results = []
        path = offer['path']
        values = catalog(path={'query': path, 'depth': 1},
                         object_provides=IApplication.__identifier__)

        for item in values:
            results.append(dict(title=item.Title,
                                state=item.review_state,
                                url=item.getURL(),
                                ))
        return results

    def getLanguages(self):
        return [_(u"Catalan"), _(u"Spanish"), _(u"English")]

    def getModalities(self):
        return [_(u"University"), _(u"Company")]

    def getDates(self):
        return [_(u"Day"), _(u"Week"), _(u"Month")]
