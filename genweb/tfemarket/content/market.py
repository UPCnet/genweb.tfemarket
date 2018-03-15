# -*- coding: utf-8 -*-

from datetime import date
from datetime import datetime
from five import grok
from operator import itemgetter
from plone import api
from plone.directives import form
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility

from genweb.tfemarket import _
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.controlpanel import ITfemarketSettings


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

        for index, item in enumerate(results, start=0):

            if len(filters['title']) > 2 and not item['title'].lower().startswith(filters['title'].lower()):
               delete.append(index)
               continue

            if not filters['degree'] == 'a' and (not item.has_key('degree') or not item['degree'] == int(filters['degree'])):
                delete.append(index)
                continue

            if not filters['departament'] == 'a' and not item['dept'] == filters['departament']:
                delete.append(index)
                continue

            # if not filters['company'] == 'a' and not filters['company'] in companies:
            #     delete.append(index)
            #     continue

            if not filters['date'] == 'a':
                today = date.today()
                creation_date = datetime.strptime(item['creation_date'], '%Y/%m/%d').date()
                diff_days = today - creation_date
                diff_days = diff_days.days
                if filters['date'] == 'd' and diff_days > 1 \
                or filters['date'] == 'w' and diff_days > 7 \
                or filters['date'] == 'm' and diff_days > 30:
                    delete.append(index)
                    continue

            if filters.has_key('grant'):
                if not item['grant']:
                    delete.append(index)
                    continue

        delete.reverse()
        for item in delete:
            results.pop(item)

        return results

    def getOffers(self):
        catalog = api.portal.get_tool(name='portal_catalog')

        path = self.context.getPhysicalPath()
        path = "/".join(path)
        values = catalog(path={'query': path, 'depth': 1},
                         object_provides=IOffer.__identifier__,
                         sort_on='sortable_title',
                         sort_order='ascending')

        results = []
        for item in values:
            offer = item.getObject()
            results.append(dict(title=item.Title,
                                state=item.review_state,
                                url=item.getURL(),
                                path=item.getPath(),
                                UID=item.UID,
                                dept=offer.dept,
                                creation_date=offer.creation_date.strftime('%Y/%m/%d'),
                                expiration_date=offer.expiration_date.strftime('%Y/%m/%d') if offer.expiration_date else None,
                                teacher_manager=offer.teacher_manager,
                                modality=offer.modality,
                                description=offer.description,
                                features=offer.features.raw if hasattr(offer.features, 'raw') else offer.features,
                                lang=offer.lang,
                                environmental_theme=offer.environmental_theme,
                                requirements=offer.requirements,
                                grant=offer.grant,
                                degree=offer.degree,
                                keywords=offer.keys,
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
        return [{'id' : 'a', 'lit' : _(u"All")},
                {'id' : 'd', 'lit' : _(u"Day")},
                {'id' : 'w', 'lit' : _(u"Week")},
                {'id' : 'm', 'lit' : _(u"Month")}]

    def getDegrees(context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        current_language = api.portal.get_current_language()

        result = []
        for item in tfe_tool.titulacions_table:
            titulacio = str(item['plan_year']) + " - "
            if current_language == 'ca':
                titulacio +=  item['titulacio_ca']
            elif current_language == 'es':
                titulacio += item['titulacio_es']
            else:
                titulacio += item['titulacio_en']

            result.append({'id' : item['codi_prisma'], 'lit' : titulacio})

        result = sorted(result, key=itemgetter('lit'))
        result.insert(0, {'id' : 'a', 'lit' : _(u"All")})
        return result

    def saveFilters(self):
        filters = self.request.form
        return filters
