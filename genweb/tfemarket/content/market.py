# -*- coding: utf-8 -*-

from datetime import date
from datetime import datetime
from five import grok
from operator import itemgetter
from plone import api
from plone.directives import form
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.security import checkPermission

from genweb.tfemarket import _
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.utils import checkPermissionCreateOffers as CPCreateOffers
from genweb.tfemarket.utils import checkPermissionCreateApplications as CPCreateApplications
from genweb.tfemarket.utils import getDegrees
from genweb.tfemarket.utils import getDegreeLiteralFromId

import ast
import unicodedata
import urllib


grok.templatedir("templates")


class IMarket(form.Schema):
    """ Folder that contains all the TFE's
    """


class View(grok.View):
    grok.context(IMarket)
    grok.template('market_view')

    def filterResults(self, results):
        filters = self.saveFilters()
        delete = []

        for index, item in enumerate(results, start=0):

            # Filter text
            if len(filters['title']) > 2 and not filters['title'].lower() in item['title'].lower():
               delete.append(index)
               continue

             # Filter degree
            if not filters['degree'] == 'a' and (not item.has_key('degrees') or int(filters['degree']) not in item['degrees']):
                delete.append(index)
                continue

            # Filter departament
            if not filters['departament'] == 'a' and (not item.has_key('dept') or int(filters['departament']) not in item['dept']):
                delete.append(index)
                continue

            # Filter company
            if not filters['company'] == 'a' and (not item.has_key('company') or int(filters['company']) not in item['company']):
                delete.append(index)
                continue

            # Filter date
            if not filters['date'] == 'a':
                if item.has_key('effective_date') and not item['effective_date'] == None:
                    today = date.today()
                    effective_date = datetime.strptime(item['effective_date'], '%d/%m/%Y').date()
                    diff_days = today - effective_date
                    diff_days = diff_days.days
                    if filters['date'] == 'd' and diff_days > 1 \
                    or filters['date'] == 'w' and diff_days > 7 \
                    or filters['date'] == 'm' and diff_days > 30:
                        delete.append(index)
                        continue
                else:
                    delete.append(index)
                    continue

            # Filters Keys
            if filters.has_key('key'):
                if item.has_key('keywords') and not item['keywords'] == None:
                    flattenedKeys = self.flattenedList(item['keywords'])
                    if isinstance(filters['key'], list):
                        deletedItem = True
                        for key in filters['key']:
                            if key in flattenedKeys:
                                deletedItem = False
                                break

                        if deletedItem:
                            delete.append(index)
                            continue
                    else:
                        if filters['key'] not in flattenedKeys:
                            delete.append(index)
                            continue
                else:
                    delete.append(index)
                    continue

            # Filter grant
            if filters.has_key('grant'):
                if not item['grant']:
                    delete.append(index)
                    continue

            # Filter language
            if item.has_key('langs'):
                flattenedListanguages = self.flattenedList(item['langs'])
                if isinstance(filters['language'], list):
                    deletedItem = True
                    for lang in filters['language']:
                        if lang in flattenedListanguages:
                            deletedItem = False

                    if deletedItem:
                        delete.append(index)
                        continue
                else:
                    if filters['language'] not in flattenedListanguages:
                        delete.append(index)
                        continue

            # FIlter modality
            if item.has_key('modality') and len(filters['modality']) != 2:
                if (filters['modality'] == 'u' and item['modality'] != 'Universitat') or (filters['modality'] == 'c' and item['modality'] != 'Empresa'):
                    delete.append(index)
                    continue

        delete.reverse()
        for item in delete:
            results.pop(item)

        return results

    def getOffers(self):
        searchMarket = self.request.cookies.get('MERCAT_TFE')
        if searchMarket and not searchMarket == "":
            self.request.form = ast.literal_eval(searchMarket)
            self.request.response.setCookie('MERCAT_TFE', "", path='/')

        if not self.request.form == {}:
            catalog = api.portal.get_tool(name='portal_catalog')
            wf_tool = getToolByName(self.context, 'portal_workflow')
            tools = getMultiAdapter((self.context, self.request), name='plone_tools')
            path = self.context.getPhysicalPath()
            path = "/".join(path)
            values = catalog(path={'query': path, 'depth': 1},
                             object_provides=IOffer.__identifier__,
                             sort_on='sortable_title',
                             sort_order='ascending')

            results = []
            for item in values:
                offer = item.getObject()
                workflowActions = wf_tool.listActionInfos(object=offer)
                workflows = tools.workflow().getWorkflowsFor(offer)[0]

                results.append(dict(title=item.Title,
                                    state=workflows['states'][item.review_state].title,
                                    url=item.getURL(),
                                    path=item.getPath(),
                                    item_path=offer.absolute_url_path(),
                                    dept=offer.dept,
                                    effective_date=offer.effective_date.strftime('%d/%m/%Y') if offer.effective_date else None,
                                    expiration_date=offer.expiration_date.strftime('%d/%m/%Y') if offer.expiration_date else None,
                                    teacher_manager=offer.teacher_manager,
                                    modality=offer.modality,
                                    description=offer.description,
                                    langs=offer.lang,
                                    multiple_langs=len(offer.lang) > 1,
                                    environmental_theme=offer.environmental_theme,
                                    grant=offer.grant,
                                    degrees=offer.degree,
                                    multiple_degrees=len(offer.degree) > 1,
                                    keywords=offer.keys,
                                    offer_id=offer.offer_id,
                                    center=offer.center,
                                    workflows=workflowActions,
                                    can_edit=checkPermission('cmf.ModifyPortalContent', offer),
                                    can_create_application=CPCreateApplications(self, offer),
                                    ))

                results = self.filterResults(results)

            return results

    def userApplications(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        results = []
        values = catalog(object_provides=IApplication.__identifier__,
                         Creator=api.user.get_current().id)

        for item in values:
            if item.review_state not in ['cancelled', 'rejected']:
                application = item.getObject()
                workflowActions = wf_tool.listActionInfos(object=application)
                workflows = tools.workflow().getWorkflowsFor(application)[0]

                results.append(dict(title=item.Title,
                                    state=workflows['states'][item.review_state].title,
                                    url=item.getURL(),
                                    item_path=application.absolute_url_path(),
                                    dni=application.dni,
                                    name=application.title,
                                    offer_id=application.offer_id,
                                    offer_title=application.offer_title,
                                    workflows=workflowActions,
                                    can_edit=checkPermission('cmf.ModifyPortalContent', application),
                                    ))
        return results

    def getLanguages(self):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        return tfe_tool.languages.split('\r\n')

    def getModalities(self):
        return [{'id' : 'c', 'lit' : _(u"Company")},
                {'id' : 'u', 'lit' : _(u"University")}]

    def getDates(self):
        return [{'id' : 'a', 'lit' : _(u"All")},
                {'id' : 'd', 'lit' : _(u"Last day")},
                {'id' : 'w', 'lit' : _(u"Last week")},
                {'id' : 'm', 'lit' : _(u"Last month")}]

    def getDegrees(self):
        return getDegrees()

    def getDegreeLiteralFromId(self, id):
        return getDegreeLiteralFromId(id)

    def getKeys(self):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        tags = []

        keys = tfe_tool.tags
        if keys:
            tags = keys.split("\r\n")

        tags.sort()
        return tags

    def saveFilters(self):
        filters = self.request.form

        if filters.has_key('key'):
            filters['key'] = self.flattenedList(filters['key'])

        if filters.has_key('language'):
            filters['language'] = self.flattenedList(filters['language'])

        return filters

    def filtersString(self):
        return urllib.urlencode(self.request.form, True)

    def flattenedString(self, item):
        if isinstance(item, str):
            return unicodedata.normalize('NFKD', item.decode('utf-8')).encode('ascii', errors='ignore')
        else:
            return unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')

    def flattenedList(self, listItems):
        if isinstance(listItems, list):
            for index, item in enumerate(listItems, start=0):
                listItems[index] = self.flattenedString(listItems[index])
            return listItems
        else:
            return self.flattenedString(listItems)

    def checkPermissionCreateOffers(self):
        return CPCreateOffers(self, self.context)
