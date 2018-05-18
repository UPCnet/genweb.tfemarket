# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from collections import OrderedDict
from datetime import date
from datetime import datetime
from five import grok
from plone import api
from plone.directives import form
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.security import checkPermission
from zope.sequencesort.ssort import sort

from genweb.tfemarket import _
from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.utils import checkPermissionCreateApplications as CPCreateApplications
from genweb.tfemarket.utils import checkPermissionCreateOffers as CPCreateOffers
from genweb.tfemarket.utils import getDegreeLiteralFromId
from genweb.tfemarket.utils import getDegrees

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


    def clearFiltersCookie(self):
        filters = self.request.form
        filters.pop('estat', None)
        filters.pop('id', None)
        filters.pop('_authenticator', None)
        return filters

    def filterResults(self, results):
        filters = self.saveFilters()
        delete = []

        for index, item in enumerate(results, start=0):

            # Filter text
            if len(filters['title']) > 0 and not filters['title'].lower() in item['title'].lower():
                delete.append(index)
                continue

            # Filter degree
            if filters['degree'] != 'a' and ('degrees' not in item or int(filters['degree']) not in item['degrees']):
                delete.append(index)
                continue

            # Filter departament
            if filters['departament'] != 'a' and ('dept' not in item or filters['departament'] != item['dept']):
                delete.append(index)
                continue

            # Filter company
            if filters['company'] != 'a' and ('company' not in item or filters['company'] != item['company']):
                delete.append(index)
                continue

            # Filter date
            if not filters['date'] == 'a':
                if 'effective_date' in item and item['effective_date']:
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

            if 'key' in filters:
                if 'keywords' in item and item['keywords']:
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
            if 'grant' in filters:
                if not item['grant']:
                    delete.append(index)
                    continue

            # Filter language
            if 'langs' in item:
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
            if 'modality' in item and len(filters['modality']) != 2:
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
            if 'searchFilters' in self.request.form:
                self.request.form = ast.literal_eval(searchMarket)
            else:
                if 'search' not in self.request.form:
                    self.request.response.setCookie('MERCAT_TFE', "", path='/')

        if not self.request.form == {} and 'form.button.confirm' not in self.request.form:
            wf_tool = getToolByName(self.context, 'portal_workflow')
            tools = getMultiAdapter((self.context, self.request), name='plone_tools')

            filters = {'portal_type': 'genweb.tfemarket.offer'}
            if 'allOffersTeacher' in self.request.form:
                filters.update({'listCreators': api.user.get_current().id})

            values = self.context.contentValues(filters)
            values = sort(values, sort=(
                ('Date', 'cmp', 'desc'),
                ('Title', 'cmp', 'asc')
            ))

            results = []
            for offer in values:
                if checkPermission('zope2.View', offer):
                    workflowActions = wf_tool.listActionInfos(object=offer)
                    workflows = tools.workflow().getWorkflowsFor(offer)[0]
                    offer_workflow = wf_tool.getWorkflowsFor(offer)[0].id
                    offer_status = wf_tool.getStatusOf(offer_workflow, offer)
                    state_id = workflows['states'][offer_status['review_state']].title

                    if state_id == 'Proposta':
                        registry = queryUtility(IRegistry)
                        tfe_tool = registry.forInterface(ITfemarketSettings)
                        review_state = tfe_tool.review_state
                        if review_state:
                            workflowActions = [x for x in workflowActions if x.get('id') == 'sendtoreview']
                        else:
                            workflowActions = [x for x in workflowActions if x.get('id') != 'sendtoreview']

                    results.append(dict(title=offer.title,
                                        state=workflows['states'][offer_status['review_state']].title,
                                        url=offer.absolute_url(),
                                        path='/'.join(offer.getPhysicalPath()),
                                        item_path='/'.join(offer.getPhysicalPath()[2:]),
                                        dept=offer.dept,
                                        company=offer.company,
                                        effective_date=offer.effective_date.strftime('%d/%m/%Y') if offer.effective_date else None,
                                        expiration_date=offer.expiration_date.strftime('%d/%m/%Y') if offer.expiration_date else None,
                                        teacher_manager=offer.teacher_manager,
                                        teacher_fullname=offer.teacher_fullname,
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
                                        if_modality_company=True if offer.modality == 'Empresa' else False,
                                        ))

            if 'search' in self.request.form or 'searchFilters' in self.request.form:
                results = self.filterResults(results)
                self.request.response.setCookie('MERCAT_TFE', self.clearFiltersCookie(), path='/')

            return results

    def userApplications(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        results = []
        values = catalog(path={'query': '/'.join(self.context.getPhysicalPath()), 'depth': 3},
                         object_provides=IApplication.__identifier__,
                         Creator=api.user.get_current().id)

        for item in values:
            if item.review_state not in ['cancelled', 'rejected']:
                application = item.getObject()
                workflowActions = wf_tool.listActionInfos(object=application)
                workflows = tools.workflow().getWorkflowsFor(application)[0]

                results.append(dict(title=item.Title,
                                    state=workflows['states'][item.review_state].title,
                                    url=item.getURL(),
                                    item_path='/'.join(application.getPhysicalPath()[2:]),
                                    offer_id=application.offer_id,
                                    offer_title=application.offer_title,
                                    workflows=workflowActions,
                                    can_edit=checkPermission('cmf.ModifyPortalContent', application),
                                    ))
        return results

    def getApplications(self, offer):
        catalog = api.portal.get_tool(name='portal_catalog')
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        results = []
        values = catalog(path={'query': offer['path'], 'depth': 1},
                         object_provides=IApplication.__identifier__)

        for item in values:
            application = item.getObject()
            workflowActions = wf_tool.listActionInfos(object=application)
            workflows = tools.workflow().getWorkflowsFor(application)[0]

            results.append(dict(title=item.Title,
                                state=workflows['states'][item.review_state].title,
                                url=item.getURL(),
                                item_path='/'.join(application.getPhysicalPath()[2:]),
                                dni=application.dni,
                                name=application.title,
                                email=application.email,
                                phone=application.phone,
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
        return [{'id': 'c', 'lit': _(u"Company")},
                {'id': 'u', 'lit': _(u"University")}]

    def getDates(self):
        return [{'id': 'a', 'lit': _(u"All")},
                {'id': 'd', 'lit': _(u"Last day")},
                {'id': 'w', 'lit': _(u"Last week")},
                {'id': 'm', 'lit': _(u"Last month")}]

    def getDegrees(self):
        return getDegrees()

    def getDegreeLiteralFromId(self, id):
        return getDegreeLiteralFromId(id)

    def getAllOffers(self):
        return self.context.contentValues({'portal_type': 'genweb.tfemarket.offer'})

    def getDepartaments(self):
        results = []
        for offer in self.getAllOffers():
            if offer.dept:
                results.append(offer.dept)

        return sorted(list(OrderedDict.fromkeys(results)))

    def getCompanys(self):
        results = []
        for offer in self.getAllOffers():
            if offer.company:
                results.append(offer.company)

        return sorted(list(OrderedDict.fromkeys(results)))

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

        if 'key' in filters:
            filters['key'] = self.flattenedList(filters['key'])

        if 'language' in filters:
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

    def openApplicationsTav(self):
        if 'allOffersTeacher' in self.request.form and self.checkPermissionCreateOffers():
            return True
        return False

    def getActualView(self):
        if 'allOffersTeacher' in self.request.form:
            return '&allOffersTeacher'
        elif 'allOffers' in self.request.form:
            return '&allOffers'
        else:
            return "&search"
