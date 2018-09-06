# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from collections import OrderedDict
from datetime import date
from datetime import datetime
from five import grok
from plone import api
from plone.directives import form
from plone.portlets.constants import CONTEXT_CATEGORY
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.interfaces import IPortletManager
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.security import checkPermission
from zope.sequencesort.ssort import sort

from genweb.tfemarket import _
from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.controlpanel import IBUSSOASettings
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.utils import checkOfferhasConfirmedApplications
from genweb.tfemarket.utils import checkPermissionCreateApplications as CPCreateApplications
from genweb.tfemarket.utils import checkPermissionCreateOffers as CPCreateOffers
from genweb.tfemarket.utils import getDegreeLiteralFromId
from genweb.tfemarket.utils import getDegrees
from genweb.tfemarket.utils import offerIsFromTheTeacher

import ast
import unicodedata
import urllib


grok.templatedir("templates")


class IMarket(form.Schema):
    """ Folder that contains all the TFE's
    """


@grok.subscribe(IMarket, IObjectAddedEvent)
def disablePortlets(market, event):
    for column in [u"plone.leftcolumn", u"plone.rightcolumn"]:
        manager = getUtility(IPortletManager, name=column)
        blacklist = getMultiAdapter((market, manager), ILocalPortletAssignmentManager)
        blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)


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

            # Filter teacher
            if filters['teacher'] != 'a' and ('teacher_manager' not in item or filters['teacher'] != item['teacher_manager']):
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
            if filters['date'] != 'a':
                if 'effective_date' in item and item['effective_date']:
                    today = date.today()
                    effective_date = datetime.strptime(item['effective_date'], '%d/%m/%Y').date()
                    diff_days = today - effective_date
                    diff_days = diff_days.days
                    if filters['date'] == 'w' and diff_days > 7 \
                       or filters['date'] == 'm' and diff_days > 30:
                        delete.append(index)
                        continue
                else:
                    delete.append(index)
                    continue

            # Filters status
            if filters['state'] != 'a' and filters['state'] != item['state_id']:
                delete.append(index)
                continue

            # Filters keys
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

        if self.checkPermissionCreateOffers() or self.request.form != {} and 'form.button.confirm' not in self.request.form:
            wf_tool = getToolByName(self.context, 'portal_workflow')
            tools = getMultiAdapter((self.context, self.request), name='plone_tools')

            filters = {'portal_type': 'genweb.tfemarket.offer'}
            if self.checkPermissionCreateOffers() and api.user.get_current().id != "admin":
                if 'search' not in self.request.form and 'allOffers' not in self.request.form:
                    filters.update({'Creator': api.user.get_current().id})

            values = self.context.contentValues(filters)
            values = sort(values, sort=(
                ('Date', 'cmp', 'desc'),
                ('Title', 'cmp', 'asc')
            ))

            results = []
            for offer in values:
                if checkPermission('zope2.View', offer):
                    workflowActions = wf_tool.listActionInfos(object=offer)
                    offerWorkflow = tools.workflow().getWorkflowsFor(offer)[0]
                    offerStatus = wf_tool.getStatusOf(offerWorkflow.id, offer)
                    offerState = offerWorkflow['states'][offerStatus['review_state']]

                    if offerState.id == 'offered':
                        registry = queryUtility(IRegistry)
                        tfe_tool = registry.forInterface(ITfemarketSettings)
                        review_state = tfe_tool.review_state
                        if review_state:
                            workflowActions = [x for x in workflowActions if x.get('id') == 'sendtoreview']
                        else:
                            workflowActions = [x for x in workflowActions if x.get('id') != 'sendtoreview']

                    if offerState.id == 'pending' and self.currentUserIsAloneTeacher():
                        workflowActions = []

                    market = offer.getParentNode()
                    marketWorkflow = tools.workflow().getWorkflowsFor(market)[0]
                    marketStatus = wf_tool.getStatusOf(marketWorkflow.id, market)
                    marketState = marketWorkflow['states'][marketStatus['review_state']]

                    if marketState.id == 'published':
                        workflowActions = [x for x in workflowActions if x.get('id') != 'publicaalintranet']
                    elif marketState.id == 'intranet':
                        workflowActions = [x for x in workflowActions if x.get('id') != 'publicaloferta']

                    results.append(dict(title=offer.title,
                                        state=offerState.title,
                                        state_id=offerState.id,
                                        url=offer.absolute_url(),
                                        path='/'.join(offer.getPhysicalPath()),
                                        item_path='/'.join(offer.getPhysicalPath()[2:]),
                                        dept=offer.dept,
                                        company=offer.company,
                                        effective_date=offer.effective_date.strftime('%d/%m/%Y') if offer.effective_date else None,
                                        expiration_date=offer.expiration_date.strftime('%d/%m/%Y') if offer.expiration_date else None,
                                        teacher_manager=offer.teacher_manager,
                                        teacher_fullname=offer.teacher_fullname,
                                        teacher_email=offer.teacher_email,
                                        codirector=offer.codirector,
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
                                        num_students=offer.num_students,
                                        workload=offer.workload,
                                        targets=offer.targets,
                                        features=offer.features,
                                        requirements=offer.requirements,
                                        co_manager=offer.co_manager,
                                        company_contact=offer.company_contact,
                                        company_email=offer.company_email,
                                        confidential=offer.confidential,
                                        scope_cooperation=offer.scope_cooperation,
                                        topic=offer.topic,
                                        if_propietary=offerIsFromTheTeacher(offer),
                                        assign_offer=self.assignOffer(offer, offerState.id)
                                        ))

            if 'search' in self.request.form or 'searchFilters' in self.request.form:
                results = self.filterResults(results)
                self.request.response.setCookie('MERCAT_TFE', self.clearFiltersCookie(), path='/')

            if 'searchOffer' in self.request.form and 'offer' in self.request.form:
                for offer in results:
                    if offer['offer_id'] == self.request.form['offer']:
                        return [offer, ]

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

                results.append(dict(UID=item.UID,
                                    title=item.Title,
                                    state=workflows['states'][item.review_state].title,
                                    url=item.getURL(),
                                    item_path='/'.join(application.getPhysicalPath()[2:]),
                                    dni=application.dni,
                                    name=application.title,
                                    email=application.email,
                                    phone=application.phone,
                                    offer_id=application.offer_id,
                                    offer_title=application.offer_title,
                                    body=application.body,
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
            workflowActions = wf_tool.listActionInfos(object=application) if offer['if_propietary'] else []
            workflows = tools.workflow().getWorkflowsFor(application)[0]

            results.append(dict(UID=item.UID,
                                title=item.Title,
                                state=workflows['states'][item.review_state].title,
                                url=item.getURL(),
                                item_path='/'.join(application.getPhysicalPath()[2:]),
                                dni=application.dni,
                                name=application.title,
                                email=application.email,
                                phone=application.phone,
                                offer_id=application.offer_id,
                                offer_title=application.offer_title,
                                body=application.body,
                                workflows=workflowActions,
                                can_change_workflows=True,
                                can_edit=checkPermission('cmf.ModifyPortalContent', application) and not self.currentUserIsAloneTeacher(),
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
                {'id': 'w', 'lit': _(u"Last week")},
                {'id': 'm', 'lit': _(u"Last month")}]

    def getDegrees(self):
        return getDegrees()

    def getDegreeLiteralFromId(self, id):
        return getDegreeLiteralFromId(id)

    def getAllOffers(self):
        return self.context.contentValues({'portal_type': 'genweb.tfemarket.offer'})

    def getTeachers(self):
        results = []
        for offer in self.getAllOffers():
            if checkPermission('zope2.View', offer) and offer.teacher_manager:
                teacherNotInList = True
                for teacher in results:
                    if teacher['id'] == offer.teacher_manager:
                        teacherNotInList = False
                        break
                if teacherNotInList:
                    results.append({'id': offer.teacher_manager, 'lit': offer.teacher_fullname + " (" + offer.teacher_manager + ")"})

        return sorted(list(results))

    def getDepartaments(self):
        results = []
        for offer in self.getAllOffers():
            if checkPermission('zope2.View', offer) and offer.dept:
                results.append(offer.dept)

        return sorted(list(OrderedDict.fromkeys(results)))

    def getCompanys(self):
        results = []
        for offer in self.getAllOffers():
            if checkPermission('zope2.View', offer) and offer.company:
                results.append(offer.company)

        return sorted(list(OrderedDict.fromkeys(results)))

    def getStates(self):
        results = []
        wf_tool = getToolByName(self, 'portal_workflow')
        states = wf_tool.tfemarket_offer_workflow.states._mapping
        user_roles = api.user.get_current().getRoles()
        for state in states.keys():
            permissions = states[state].permission_roles['View']
            for role in user_roles:
                if role in permissions:
                    results.append({'id': state, 'lit': states[state].title})
                    break
        return sorted(results, key=lambda x: x['lit'])

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
        if self.checkPermissionCreateOffers():
            return True
        return False

    def getActualView(self):
        if 'allOffers' in self.request.form:
            return '&allOffers'
        elif 'search' in self.request.form:
            return '&search'
        else:
            return ''

    def classViewSearch(self):
        if self.checkPermissionCreateOffers() and self.request.form == {}:
            return {'collapse': ' hide', 'expand': ''}
        else:
            return {'collapse': '', 'expand': ' hide'}

    def assignOffer(self, offer, state):
        if checkPermission('cmf.RequestReview', offer) and checkOfferhasConfirmedApplications(offer):
            if state == 'intranet':
                return 'assignalofertaintranet'
            elif state == 'public':
                return 'assign'
        return False

    def currentUserIsAloneTeacher(self):
        user_roles = api.user.get_current().getRoles()
        if 'Teacher' in user_roles:
            if 'Manager' in user_roles or 'Market Manager' in user_roles:
                return False
            else:
                return True
        else:
            return False

    def showErrorBusSOA(self):
        user_roles = api.user.get_current().getRoles()
        if 'Manager' in user_roles or 'Market Manager' in user_roles:
            registry = queryUtility(IRegistry)
            bussoa_tool = registry.forInterface(IBUSSOASettings)
            if bussoa_tool.bus_url and bussoa_tool.bus_user and bussoa_tool.bus_password and bussoa_tool.bus_apikey:
                return False
            return True
        return False
