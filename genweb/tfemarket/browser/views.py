# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from five import grok
from plone import api
from plone.memoize import ram
from plone.registry.interfaces import IRegistry
from scss import Scss
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.interface import Interface
from zope.interface import alsoProvides

from genweb.core.utils import genweb_config
from genweb.theme.browser.views import _render_cachekey

from genweb.tfemarket import _
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from genweb.tfemarket.utils import BusError
from genweb.tfemarket.utils import getLdapExactUserData
from genweb.tfemarket.utils import getLdapUserData
from genweb.tfemarket.utils import isTeachersOffer
from genweb.tfemarket.utils import getStudentData

import json
import pkg_resources
import transaction


def redirectToMarket(self):
    try:
        from plone.protect.interfaces import IDisableCSRFProtection
        alsoProvides(self.request, IDisableCSRFProtection)
    except:
        pass

    if self.context.portal_type == 'genweb.tfemarket.offer':
        self.request.response.redirect(self.context.absolute_url() + '#offer-applications')
    elif self.context.portal_type == 'genweb.tfemarket.market':
        if 'allOffers' not in self.request.form and 'search' not in self.request.form:
            url = self.context.absolute_url()
            if 'offer' in self.request.form:
                url += "?offer=" + self.request.form.get('offer')
                if 'open' in self.request.form:
                    url += "&open=Y"
            self.request.response.redirect(url)
        else:
            if 'allOffers' in self.request.form:
                url = self.context.absolute_url() + "?allOffers"
            elif 'search' in self.request.form:
                url = self.context.absolute_url() + "?searchFilters"
            if 'offer' in self.request.form:
                url += "&offer=" + self.request.form.get('offer')
                if 'open' in self.request.form:
                    url += "&open=Y"
            self.request.response.redirect(url)
    else:
        self.request.response.redirect(self.context.absolute_url())


class changeActualState(grok.View):
    grok.context(Interface)
    grok.name('changeActualState')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass

        estat = self.request.form.get('estat')
        itemid = self.request.form.get('id')

        try:
            portal = api.portal.get()
            currentItem = portal.unrestrictedTraverse(itemid)
            isCreator = api.user.get_current().id in currentItem.creators
            if currentItem and (isTeachersOffer(currentItem.getParentNode()) or isCreator):
                if currentItem.portal_type == 'genweb.tfemarket.offer':
                    wf_tool = getToolByName(self.context, 'portal_workflow')
                    tools = getMultiAdapter((self.context, self.request), name='plone_tools')
                    market = currentItem.getParentNode()
                    marketWorkflow = tools.workflow().getWorkflowsFor(market)[0]
                    marketStatus = wf_tool.getStatusOf(marketWorkflow.id, market)
                    marketState = marketWorkflow['states'][marketStatus['review_state']]

                    if (marketState.id == 'published' and estat == 'publicaalintranet') or (marketState.id == 'intranet' and estat == 'publicaloferta'):
                        self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
                        redirectToMarket(self)
                        return None

                wftool = getToolByName(self.context, 'portal_workflow')
                wftool.doActionFor(currentItem, estat)
                redirectToMarket(self)
            else:
                self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
                redirectToMarket(self)
        except BusError as err:
            self.context.plone_utils.addPortalMessage(err.value['resultat'], 'error')
            redirectToMarket(self)
        except:
            self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
            redirectToMarket(self)


class getTeacher(grok.View):
    grok.context(Interface)
    grok.name('getTeacher')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        # TODO Cambiar PERSONAL por PDI
        # teachers = getLdapUserData(self.request.form['teacher'], typology='PERSONAL')
        teachers = getLdapUserData(self.request.form['teacher'])
        if len(teachers) > 0:
            listTeachers = []
            for teacher in teachers:
                try:
                    teacherDept = teacher['unitCode'] + "-" + teacher['unit']
                    listTeachers.append({
                        'user': teacher['id'],
                        'email': teacher['mail'],
                        'fullname': teacher['sn1'] + teacher['sn2'] + ', ' + teacher['aliesnom'],
                        'dept': teacherDept
                    })
                except:
                    pass
            return json.dumps(listTeachers)
        else:
            return None


class getExactTeacher(grok.View):
    grok.context(Interface)
    grok.name('getExactTeacher')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        # TODO Cambiar PERSONAL por PDI
        # teacher = getLdapExactUserData(self.request.form['teacher'], typology='PERSONAL')
        teacher = getLdapExactUserData(self.request.form['teacher'])
        if teacher and 'sn' in teacher:
            teacherDept = teacher['unitCode'] + "-" + teacher['unit']
            data = {
                'user': teacher['id'],
                'email': teacher['mail'],
                'fullname': teacher['sn1'] + teacher['sn2'] + ', ' + teacher['aliesnom'],
                'dept': teacherDept
            }
            return json.dumps(data)
        else:
            return None


class requestOffer(grok.View):
    grok.context(Interface)
    grok.name('requestOffer')
    grok.require('genweb.authenticated')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass

        itemid = self.request.form.get('id')
        portal = api.portal.get()
        currentItem = portal.unrestrictedTraverse(itemid)
        currentUser = api.user.get_current()
        data = getStudentData(self, currentItem, currentUser)
        if data:
            self.request.response.setCookie('APPLICATION_DATA', data, path='/')
            self.request.response.redirect(currentItem.absolute_url() + '/++add++genweb.tfemarket.application')
        else:
            redirectToMarket(self)


class getInfoCreateApplication(grok.View):
    grok.context(IOffer)
    grok.name('getInfoCreateApplication')
    grok.require('cmf.AddPortalContent')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        data = self.request.cookies.pop('APPLICATION_DATA')
        return json.dumps(eval(data))


class resetCountOffers(grok.View):
    grok.name('reset_offers_counter')
    grok.context(Interface)
    grok.template('reset_offers_counter')
    grok.require('cmf.ManagePortal')
    grok.layer(IGenwebTfemarketLayer)

    def update(self):
        if 'confirm' in self.request.form:
            registry = queryUtility(IRegistry)
            tfe_tool = registry.forInterface(ITfemarketSettings)
            tfe_tool.count_offers = 0
            transaction.commit()
            self.request.response.redirect(self.context.absolute_url() + "/tfemarket-settings#fieldsetlegend-2")


class dynamicTfeCSS(grok.View):
    grok.name('dynamic_tfe.css')
    grok.context(Interface)
    grok.layer(IGenwebTfemarketLayer)

    def update(self):
        self.especific1 = genweb_config().especific1
        self.especific2 = genweb_config().especific2

    def render(self):
        self.request.response.setHeader('Content-Type', 'text/css')
        self.request.response.addHeader('Cache-Control', 'must-revalidate, max-age=0, no-cache, no-store')
        if self.especific1 and self.especific2:
            return self.compile_scss(especific1=self.especific1, especific2=self.especific2)

    @ram.cache(_render_cachekey)
    def compile_scss(self, **kwargs):
        genwebtfeegg = pkg_resources.get_distribution('genweb.tfemarket')

        scssfile = open('{}/genweb/tfemarket/browser/stylesheets/dynamic_tfe.scss'.format(genwebtfeegg.location))

        settings = dict(especific1=self.especific1,
                        especific2=self.especific2)

        variables_scss = """

        $genwebPrimary: {especific1};
        $genwebTitles: {especific2};

        """.format(**settings)

        css = Scss(scss_opts={
                   'compress': False,
                   'debug_info': False,
                   })

        dynamic_scss = ''.join([variables_scss, scssfile.read()])

        return css.compile(dynamic_scss)
