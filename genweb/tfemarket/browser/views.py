# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime
from five import grok
from operator import itemgetter
from plone import api
from plone.directives import form
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.security import checkPermission

from genweb.tfemarket import _
from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.content.market import IMarket
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from genweb.tfemarket.utils import checkPermissionCreateOffers as CPCreateOffers
from genweb.tfemarket.utils import checkPermissionCreateApplications as CPCreateApplications
from genweb.tfemarket.utils import getDegrees
from genweb.tfemarket.utils import getDegreeLiteralFromId
from genweb.tfemarket.utils import getLdapUserData

import json


def redirectAfterChangeActualState(self):
    if self.context.portal_type == 'genweb.tfemarket.offer':
        self.request.response.redirect(self.context.absolute_url() + '#offer-applications')
    elif self.context.portal_type == 'genweb.tfemarket.market':
        if not 'view' in self.request.form:
            self.request.response.setCookie('MERCAT_TFE', clearFiltersCookie(self), path='/')
            self.request.response.redirect(self.context.absolute_url())
        else:
            url = self.context.absolute_url() + "/" + self.request.form.get('view')
            if 'offer' in self.request.form:
                if 'teacher' in self.request.form.get('view'):
                    url = url + "&offer=" + self.request.form.get('offer')
                else:
                    url = url + "?offer=" + self.request.form.get('offer')
            self.request.response.redirect(url)
    else:
        self.request.response.redirect(self.context.absolute_url())


def clearFiltersCookie(self):
    filters = self.request.form
    filters.pop('estat', None)
    filters.pop('id', None)
    filters.pop('_authenticator', None)
    return filters


class changeActualState(BrowserView):
    """ Es fa servir a la vista sessio i presentacio. No cal fer reload perque
        es mostra el nou valor per JS
    """
    def __call__(self):
        portal_catalog = getToolByName(self, 'portal_catalog')
        estat = self.request.form.get('estat')
        itemid = self.request.form.get('id')

        try:
            object_path = '/'.join(self.context.getPhysicalPath())
            item = str(itemid.split('/')[-1:][0])
            currentitem = portal_catalog.searchResults(
                portal_type=['genweb.tfemarket.application', 'genweb.tfemarket.offer'],
                id=item,
                path={'query': object_path})[0].getObject()

            if currentitem:
                wftool = getToolByName(self.context, 'portal_workflow')
                wftool.doActionFor(currentitem, estat)
                redirectAfterChangeActualState(self)
            else:
                self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
                redirectAfterChangeActualState(self)

        except:
            self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
            redirectAfterChangeActualState(self)


class AllOffers(grok.View):
    grok.context(IMarket)
    grok.name('allOffers')
    grok.template("allOffers")
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getOffers(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        path = self.context.getPhysicalPath()
        path = "/".join(path)

        roles = api.user.get_roles()
        if 'teacher' in self.request.form and self.checkPermissionCreateOffers():
            values = catalog(path={'query': path, 'depth': 1},
                             object_provides=IOffer.__identifier__,
                             sort_on='sortable_title',
                             sort_order='ascending',
                             Creator=api.user.get_current().id)
        else:
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
                                company=offer.company,
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

        return results

    def getApplications(self, offer):
        catalog = api.portal.get_tool(name='portal_catalog')
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        results = []
        values = catalog(path={'query': offer['item_path'], 'depth': 1},
                         object_provides=IApplication.__identifier__)

        for item in values:
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

    def getDegrees(self):
        return getDegrees()

    def getDegreeLiteralFromId(self, id):
        return getDegreeLiteralFromId(id)

    def openApplicationsTav(self):
        roles = api.user.get_roles()
        if 'teacher' in self.request.form and self.checkPermissionCreateOffers():
            return True
        return False

    def getActualView(self):
        if 'teacher' in self.request.form and self.checkPermissionCreateOffers():
            return "allOffers?teacher"
        else:
            return "allOffers"

    def checkPermissionCreateOffers(self):
        return CPCreateOffers(self, self.context)


class getTeacher(grok.View):
    grok.context(IOffer)
    grok.name('getTeacher')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        teachers = getLdapUserData(self.request.form['teacher'])
        if len(teachers) > 0:
            listTeachers = []
            for teacher in teachers:
                listTeachers.append({'id' : teacher['id'], 'email' : teacher['id'] + "@gmail.com"})
            return json.dumps(listTeachers[:5])
        else:
            return None


from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from plone.formwidget.recaptcha.interfaces import IReCaptchaSettings
from zope.interface import Interface

import transaction


class recaptchaKeys(grok.View):
    grok.context(Interface)
    grok.require('cmf.ManagePortal')
    grok.name('recaptchaKeys')

    def render(self):
        registry = queryUtility(IRegistry)
        recaptcha_tool = registry.forInterface(IReCaptchaSettings)
        recaptcha_tool.public_key = u'6LcEtjEUAAAAAHVmogdyohPkahy_0MrKsOjKlefn'
        recaptcha_tool.private_key = u'6LcEtjEUAAAAAFoR3rEORJQTzMdQE0y6prqaC0Ta'
        transaction.commit()
