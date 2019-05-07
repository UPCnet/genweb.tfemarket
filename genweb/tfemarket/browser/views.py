# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from StringIO import StringIO

from five import grok
from plone import api
from plone.dexterity.utils import createContentInContainer
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
from genweb.tfemarket.utils import checkOfferhasAssign
from genweb.tfemarket.utils import checkOfferhasValidApplications
from genweb.tfemarket.utils import getApplicationsFromContent
from genweb.tfemarket.utils import getDegrees
from genweb.tfemarket.utils import getLdapExactUserData
from genweb.tfemarket.utils import getLdapUserData
from genweb.tfemarket.utils import getStudentData
from genweb.tfemarket.utils import isTeachersOffer

import csv
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
                    if estat in ['assign', 'assignalofertaintranet']:
                        if not checkOfferhasAssign(currentItem):
                            self.context.plone_utils.addPortalMessage(_(u"The offer can't be assign. There must be at least one confirmed application and the others cancelled, rejected or renounced"), 'error')
                            redirectToMarket(self)
                            return None

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
                        'fullname': teacher['sn1'] + ' ' + teacher['sn2'] + ', ' + teacher['givenName'] if 'sn2' in teacher else teacher['sn1'] + ', ' + teacher['givenName'],
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
        # teacher = getLdapExactUserData(api.user.get_current().id, typology='PERSONAL')
        teacher = getLdapExactUserData(api.user.get_current().id)
        if teacher:
            teacherDept = teacher['unitCode'] + "-" + teacher['unit']
            data = {
                'user': teacher['id'],
                'email': teacher['mail'],
                'fullname': teacher['sn1'] + ' ' + teacher['sn2'] + ', ' + teacher['givenName'] if 'sn2' in teacher else teacher['sn1'] + ', ' + teacher['givenName'],
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


class getInfoRenameOffer(grok.View):
    grok.context(Interface)
    grok.name('getInfoRenameOffer')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        pc = api.portal.get_tool('portal_catalog')
        offer = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                  'UID': self.request.form['UID']})
        if len(offer) > 0:
            offer = offer[0]
            return json.dumps({'title': offer.Title, 'shortname': offer.id})


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


class tfemarketUtils(grok.View):
    grok.context(Interface)
    grok.name('tfemarket-utils')
    grok.template('tfemarket_utils')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getTFEs(self):
        return getUrlAllTFE(self)


class tfemarketUtilsCopyOffer(grok.View):
    grok.context(Interface)
    grok.name('tfemarket-utils-copy-offer')
    grok.template('tfemarket_utils_copy_offer')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getTFEs(self):
        return getUrlAllTFE(self)

    def getOffers(self):
        return getAllOffers(self)

    def update(self):
        if 'submit' in self.request.form:
            pc = api.portal.get_tool('portal_catalog')
            offer = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                      'UID': self.request.form['offer']})
            if len(offer) > 0:
                offer = offer[0].getObject()
                market = offer.getParentNode()
                try:
                    data = {
                        'title': 'Copy of ' + offer.title,
                        'description': offer.description,
                        'topic': offer.topic,
                        'offer_type': offer.offer_type if 'offer_type' in offer else _(u'Project'),
                        'degree': offer.degree,
                        'keys': offer.keys,
                        'teacher_manager': offer.teacher_manager,
                        'teacher_fullname': offer.teacher_fullname,
                        'teacher_email': offer.teacher_email,
                        'dept': offer.dept,
                        'codirector': offer.codirector,
                        'num_students': offer.num_students,
                        'workload': offer.workload,
                        'targets': offer.targets,
                        'features': offer.features,
                        'requirements': offer.requirements,
                        'lang': offer.lang,
                        'modality': offer.modality,
                        'co_manager': offer.co_manager,
                        'company': offer.company,
                        'company_contact': offer.company_contact,
                        'company_email': offer.company_email,
                        'grant': offer.grant,
                        'confidential': offer.confidential,
                        'environmental_theme': offer.environmental_theme,
                        'scope_cooperation': offer.scope_cooperation,
                        'tfgm': offer.tfgm,
                    }
                    copyOffer = createContentInContainer(market, "genweb.tfemarket.offer", **data)
                    copyOffer.setEffectiveDate(offer.effective_date)
                    copyOffer.setExpirationDate(offer.expiration_date)
                    copyOffer.reindexObject()

                    IStatusMessage(self.request).addStatusMessage(_(u"The offer has been copied."), 'info')
                    self.request.response.redirect(self.context.absolute_url() + "/@@tfemarket-utils-rename-offer?offer=" + copyOffer.UID())
                except:
                    IStatusMessage(self.request).addStatusMessage(_(u"The offer could not be copied."), 'error')
            else:
                IStatusMessage(self.request).addStatusMessage(_(u"The offer could not be copied."), 'error')


class tfemarketUtilsRenameOffer(grok.View):
    grok.context(Interface)
    grok.name('tfemarket-utils-rename-offer')
    grok.template('tfemarket_utils_rename_offer')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getTFEs(self):
        return getUrlAllTFE(self)

    def getOffers(self):
        return getAllOffers(self)

    def update(self):
        if 'submit' in self.request.form:
            pc = api.portal.get_tool('portal_catalog')
            offer = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                      'UID': self.request.form['offer']})
            if len(offer) > 0:
                offer = offer[0].getObject()
                offer.title = self.request.form['newTitle']
                parent = offer.getParentNode()
                try:
                    parent.manage_renameObject(offer.id, self.request.form['newShortname'])
                    offer.reindexObject()

                    for application in getApplicationsFromContent(offer):
                        application.offer_title = self.request.form['newTitle']
                        application.reindexObject()
                    IStatusMessage(self.request).addStatusMessage(_(u"The offer has been modified."), 'info')
                except:
                    IStatusMessage(self.request).addStatusMessage(_(u"Error the identifier exists."), 'error')
            else:
                IStatusMessage(self.request).addStatusMessage(_(u"Error the identifier exists."), 'error')


class tfemarketUtilsDeleteOffer(grok.View):
    grok.context(Interface)
    grok.name('tfemarket-utils-delete-offer')
    grok.template('tfemarket_utils_delete_offer')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getTFEs(self):
        return getUrlAllTFE(self)

    def getOffers(self):
        pc = api.portal.get_tool('portal_catalog')
        filters = {'portal_type': 'genweb.tfemarket.offer',
                   'review_state': ('intranet', 'offered', 'public', 'pending'),
                   'sort_on': 'sortable_title',
                   'sort_order': 'ascending'}

        if 'TFE Teacher' in api.user.get_current().getRoles() and api.user.get_current().id != "admin":
            filters.update({'Creator': api.user.get_current().id})

        offers = pc.searchResults(**filters)
        res = {'ok': [], 'ko': []}
        for offer in offers:
            data = {'UID': offer.UID,
                    'Title': offer.Title,
                    'offer_id': offer.getObject().offer_id}

            if checkOfferhasValidApplications(offer.getObject()):
                res['ko'].append(data)
            else:
                res['ok'].append(data)
        return res

    def update(self):
        if 'submit' in self.request.form:
            pc = api.portal.get_tool('portal_catalog')
            offer = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                      'UID': self.request.form['offer']})
            if len(offer) > 0:
                offer = offer[0]
                parent = offer.getObject().aq_parent
                try:
                    parent.manage_delObjects([offer.id])
                    IStatusMessage(self.request).addStatusMessage(_(u"The offer has been removed."), 'info')
                except:
                    IStatusMessage(self.request).addStatusMessage(_(u"The offer could not be removed."), 'error')
            else:
                IStatusMessage(self.request).addStatusMessage(_(u"The offer could not be removed."), 'error')


class tfemarketUtilsStats(grok.View):
    grok.context(Interface)
    grok.name('tfemarket-utils-stats')
    grok.template('tfemarket_utils_stats')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getTFEs(self):
        return getUrlAllTFE(self)

    def getStates(self):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        review_state = tfe_tool.review_state

        results = []
        results.append({'id': 'offered', 'lit': 'Proposta'})

        if review_state:
            results.append({'id': 'pending', 'lit': 'En revisió'})

        results.append({'id': 'public', 'lit': 'Pública'})
        results.append({'id': 'intranet', 'lit': 'Intranet'})
        results.append({'id': 'assigned', 'lit': 'Assignada'})
        results.append({'id': 'assignadaintranet', 'lit': 'Assignada (intranet)'})
        results.append({'id': 'registered', 'lit': 'Inscrita'})
        results.append({'id': 'inscritaintranet', 'lit': 'Inscrita (intranet)'})
        results.append({'id': 'expired', 'lit': 'Caducada'})
        return results

    def getDegreesInfo(self):
        pc = api.portal.get_tool('portal_catalog')
        res = []
        for degree in getDegrees():
            if degree['id'] != 'a':
                info = {'id': degree['id'], 'title': degree['lit']}
                for state in self.getStates():
                    data = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                             'TFEdegree': degree['id'],
                                             'review_state': state['id']})
                    info.update({state['id']: len(data)})

                data = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                         'TFEdegree': degree['id']})
                info.update({'total': len(data)})
                res.append(info)

        return res

    def getTotalInfo(self):
        pc = api.portal.get_tool('portal_catalog')
        info = {'title': u"Total"}
        for state in self.getStates():
            data = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                     'review_state': state['id']})
            info.update({state['id']: len(data)})

        data = pc.searchResults({'portal_type': 'genweb.tfemarket.offer'})
        info.update({'total': len(data)})

        return info


class tfemarketUtilsDownloadCSV(grok.View):
    grok.context(Interface)
    grok.name('tfemarket-utils-download-csv')
    grok.template('tfemarket_utils_download_csv')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getTFEs(self):
        return getUrlAllTFE(self)


class tfemarketUtilsExportCSV(grok.View):
    grok.context(Interface)
    grok.name('tfemarket-utils-export-csv')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')

        output_file = StringIO()
        writer = csv.writer(output_file, delimiter=',')

        pc = api.portal.get_tool('portal_catalog')
        market = pc.searchResults({'portal_type': 'genweb.tfemarket.market',
                                   'UID': self.request.form['UID']})[0]

        if 'submit_offers' in self.request.form:
            registry = queryUtility(IRegistry)
            tfe_tool = registry.forInterface(ITfemarketSettings)

            if tfe_tool.view_num_students:
                data_header = ['Offer ID', 'Title', 'Description', 'Topic', 'Type', 'TFG/TFM', 'Degrees', 'Keys',
                               'Teacher ID', 'Teacher fullname', 'Teacher email', 'University department',
                               'Codirector', 'Number of students', 'Workload', 'Targets', 'Features',
                               'Requirements', 'Languages', 'Modality', 'CoManager', 'Company',
                               'Company contact', 'Company email', 'Possibility of scholarship',
                               'Confidential', 'Environmental theme', 'Scope of cooperation',
                               'Publication date', 'Expiration date', 'Expired', 'State']
            else:  # Omit Num Students
                data_header = ['Offer ID', 'Title', 'Description', 'Topic', 'Type', 'TFG/TFM', 'Degrees', 'Keys',
                               'Teacher ID', 'Teacher fullname', 'Teacher email', 'University department',
                               'Codirector', 'Workload', 'Targets', 'Features',
                               'Requirements', 'Languages', 'Modality', 'CoManager', 'Company',
                               'Company contact', 'Company email', 'Possibility of scholarship',
                               'Confidential', 'Environmental theme', 'Scope of cooperation',
                               'Publication date', 'Expiration date', 'Expired', 'State']

            writer.writerow(data_header)

            offers = pc.searchResults({'portal_type': 'genweb.tfemarket.offer',
                                       'path': {"query": market.getPath()}})

            for data in offers:
                offer = data.getObject()

                offerWorkflow = tools.workflow().getWorkflowsFor(offer)[0]
                offerStatus = wf_tool.getStatusOf(offerWorkflow.id, offer)
                offerState = offerWorkflow['states'][offerStatus['review_state']]

                if tfe_tool.view_num_students:
                    writer.writerow([
                        offer.offer_id.encode('utf-8'),
                        offer.title.encode('utf-8'),
                        offer.description.encode('utf-8'),
                        offer.topic.encode('utf-8') if offer.topic else "",
                        offer.offer_type.encode('utf-8') if offer.offer_type else "",
                        '\n'.join(offer.tfgm) if offer.tfgm else "",
                        '\n'.join(offer.degree) if offer.degree else "",
                        '\n'.join(offer.keys) if offer.keys else "",
                        offer.teacher_manager.encode('utf-8'),
                        offer.teacher_fullname.encode('utf-8'),
                        offer.teacher_email.encode('utf-8'),
                        offer.dept.encode('utf-8'),
                        offer.codirector.encode('utf-8') if offer.codirector else "",
                        offer.num_students or "",
                        offer.workload.encode('utf-8') if offer.workload else "",
                        offer.targets.encode('utf-8') if offer.targets else "",
                        offer.features.encode('utf-8') if offer.features else "",
                        offer.requirements.encode('utf-8') if offer.requirements else "",
                        '\n'.join(offer.lang) if offer.lang else "",
                        offer.modality.encode('utf-8'),
                        offer.co_manager.encode('utf-8') if offer.co_manager else "",
                        offer.company.encode('utf-8') if offer.company else "",
                        offer.company_contact.encode('utf-8') if offer.company_contact else "",
                        offer.company_email.encode('utf-8') if offer.company_email else "",
                        'Yes' if offer.grant else 'No',
                        'Yes' if offer.confidential else 'No',
                        'Yes' if offer.environmental_theme else 'No',
                        'Yes' if offer.scope_cooperation else 'No',
                        offer.effective_date.strftime('%d/%m/%Y') if offer.effective_date else "",
                        offer.expiration_date.strftime('%d/%m/%Y') if offer.expiration_date else "",
                        'Yes' if offer.isExpired() else 'No',
                        offerState.title.encode('utf-8')])
                else:  # Omit Num Students
                    writer.writerow([
                        offer.offer_id.encode('utf-8'),
                        offer.title.encode('utf-8'),
                        offer.description.encode('utf-8'),
                        offer.topic.encode('utf-8') if offer.topic else "",
                        offer.offer_type.encode('utf-8') if offer.offer_type else "",
                        '\n'.join(offer.tfgm) if offer.tfgm else "",
                        '\n'.join(offer.degree) if offer.degree else "",
                        '\n'.join(offer.keys) if offer.keys else "",
                        offer.teacher_manager.encode('utf-8'),
                        offer.teacher_fullname.encode('utf-8'),
                        offer.teacher_email.encode('utf-8'),
                        offer.dept.encode('utf-8'),
                        offer.codirector.encode('utf-8') if offer.codirector else "",
                        offer.workload.encode('utf-8') if offer.workload else "",
                        offer.targets.encode('utf-8') if offer.targets else "",
                        offer.features.encode('utf-8') if offer.features else "",
                        offer.requirements.encode('utf-8') if offer.requirements else "",
                        '\n'.join(offer.lang) if offer.lang else "",
                        offer.modality.encode('utf-8'),
                        offer.co_manager.encode('utf-8') if offer.co_manager else "",
                        offer.company.encode('utf-8') if offer.company else "",
                        offer.company_contact.encode('utf-8') if offer.company_contact else "",
                        offer.company_email.encode('utf-8') if offer.company_email else "",
                        'Yes' if offer.grant else 'No',
                        'Yes' if offer.confidential else 'No',
                        'Yes' if offer.environmental_theme else 'No',
                        'Yes' if offer.scope_cooperation else 'No',
                        offer.effective_date.strftime('%d/%m/%Y') if offer.effective_date else "",
                        offer.expiration_date.strftime('%d/%m/%Y') if offer.expiration_date else "",
                        'Yes' if offer.isExpired() else 'No',
                        offerState.title.encode('utf-8')])

            filename = market.id + "-offers.csv"
        else:
            data_header = ['Offer ID', 'Degree ID', 'DNI', 'Fullname', 'Telephone', 'Email',
                           'PRISMA ID', 'Expedient ID', 'Body', 'State']

            writer.writerow(data_header)

            requests = pc.searchResults({'portal_type': 'genweb.tfemarket.application',
                                         'path': {"query": market.getPath()}})

            for data in requests:
                app = data.getObject()

                appWorkflow = tools.workflow().getWorkflowsFor(app)[0]
                appStatus = wf_tool.getStatusOf(appWorkflow.id, app)
                appState = appWorkflow['states'][appStatus['review_state']]

                writer.writerow([
                    app.offer_id.encode('utf-8'),
                    app.degree_id.encode('utf-8'),
                    app.dni.encode('utf-8'),
                    app.title.encode('utf-8'),
                    app.phone.encode('utf-8') if app.phone else "",
                    app.email.encode('utf-8'),
                    app.prisma_id.encode('utf-8') if app.prisma_id else "",
                    app.codi_expedient.encode('utf-8') if app.codi_expedient else "",
                    app.body.encode('utf-8') if app.body else "",
                    appState.title.encode('utf-8')])

            filename = market.id + "-applications.csv"

        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % filename)
        return output_file.getvalue()


def getUrlAllTFE(self):
    pc = api.portal.get_tool('portal_catalog')
    return pc.searchResults({'portal_type': 'genweb.tfemarket.market'})


def getAllOffers(self):
    pc = api.portal.get_tool('portal_catalog')
    filters = {'portal_type': 'genweb.tfemarket.offer',
               'sort_on': 'sortable_title',
               'sort_order': 'ascending'}
    if 'TFE Teacher' in api.user.get_current().getRoles() and api.user.get_current().id != "admin":
        filters.update({'Creator': api.user.get_current().id})

    offers = pc.searchResults(**filters)
    res = []
    for offer in offers:
        res.append({'UID': offer.UID,
                    'Title': offer.Title,
                    'offer_id': offer.getObject().offer_id})
    return res


class fillEmptyTFGMOffers(grok.View):
    grok.context(Interface)
    grok.name('fillEmptyTFGMOffers')
    grok.require('zope2.View')
    grok.layer(IGenwebTfemarketLayer)

    def getDegreesProgramType(self):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)

        result = {}
        if tfe_tool.titulacions_table:
            for item in tfe_tool.titulacions_table:
                result.update({item['codi_mec']: item['progam_type']})

        return result

    def render(self):
        degrees = self.getDegreesProgramType()

        pc = api.portal.get_tool('portal_catalog')
        offers = pc.searchResults({'portal_type': 'genweb.tfemarket.offer'})
        for data in offers:
            offer = data.getObject()
            if not offer.tfgm:
                tfgm = []
                for degree in offer.degree:
                    if degree in degrees:
                        if degrees[degree] == 'MA' and 'TFM' not in tfgm:
                            tfgm.append('TFM')
                        elif degrees[degree] == 'GR' and 'TFG' not in tfgm:
                            tfgm.append('TFG')
            offer.tfgm = tfgm
            offer.reindexObject()

        return 'Finished'
