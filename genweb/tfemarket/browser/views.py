# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from five import grok
from plone import api
from plone.memoize import ram
from plone.registry.interfaces import IRegistry
from scss import Scss
from zope.i18n import translate
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.interface import Interface

from genweb.core.utils import genweb_config
from genweb.theme.browser.views import _render_cachekey

from genweb.tfemarket import _
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.controlpanel import ITfemarketSettings, IBUSSOASettings
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from genweb.tfemarket.utils import getLdapExactUserData
from genweb.tfemarket.utils import getLdapUserData
from genweb.tfemarket.utils import LDAPSearch
from genweb.tfemarket.utils import offerIsFromTheTeacher

import json
import pkg_resources
import transaction
import requests


def redirectAfterChangeActualState(self):
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
    """ Es fa servir a la vista sessio i presentacio. No cal fer reload perque
        es mostra el nou valor per JS
    """

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
            if currentItem and (offerIsFromTheTeacher(currentItem.getParentNode()) or isCreator):
                if currentItem.portal_type == 'genweb.tfemarket.offer':
                    wf_tool = getToolByName(self.context, 'portal_workflow')
                    tools = getMultiAdapter((self.context, self.request), name='plone_tools')
                    market = currentItem.getParentNode()
                    marketWorkflow = tools.workflow().getWorkflowsFor(market)[0]
                    marketStatus = wf_tool.getStatusOf(marketWorkflow.id, market)
                    marketState = marketWorkflow['states'][marketStatus['review_state']]

                    if (marketState.id == 'published' and estat == 'publicaalintranet') or (marketState.id == 'intranet' and estat == 'publicaloferta'):
                        self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
                        redirectAfterChangeActualState(self)
                        return None

                wftool = getToolByName(self.context, 'portal_workflow')
                wftool.doActionFor(currentItem, estat)
                redirectAfterChangeActualState(self)
            else:
                self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
                redirectAfterChangeActualState(self)

        except:
            self.context.plone_utils.addPortalMessage(_(u'Error you can\'t perform the action.'), 'error')
            redirectAfterChangeActualState(self)


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
                        'fullname': teacher['sn'],
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
                'fullname': teacher['sn'],
                'dept': teacherDept
            }
            return json.dumps(data)
        else:
            return None


class getInfoCreateApplication(grok.View):
    grok.context(IOffer)
    grok.name('getInfoCreateApplication')
    grok.require('cmf.AddPortalContent')
    grok.layer(IGenwebTfemarketLayer)

    def getDadesStudent(self, cn):
        registry = queryUtility(IRegistry)
        bussoa_tool = registry.forInterface(IBUSSOASettings)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        bussoa_url = bussoa_tool.bus_url
        bussoa_user = bussoa_tool.bus_user
        bussoa_pass = bussoa_tool.bus_password
        bussoa_apikey = bussoa_tool.bus_apikey
        tipus_alta = 'I' # tfe_tool.enroll_type

        student_data = {}
        keys = ['segmentation', 'unit', 'typology', 'idorigen']
        vinculacio = []
        result = LDAPSearch(self, cn)
        if result['ok']:
            user = result['content'][0]
            student_data = {
                'offer_id': self.context.offer_id,
                'offer_title': self.context.title,
                'fullname': user['fullname'],
                'dni': user['dni'],
                'email': user['email'],
            }
            if 'telephoneNumber' in user:
                student_data.update({'phone': user['phone']})

            # COMENTADO PARA DEMO

            # for key in keys:
            #     for ind, i in enumerate(user[key]):
            #         try:
            #             vinculacio[ind].update({key: i})
            #         except IndexError:
            #             vinculacio.append({key: i})

            # isStudent = (True for item in vinculacio if item['typology'] == 'EST')
            # if True not in isStudent:
            #     self.context.plone_utils.addPortalMessage(_(u"No tens viculació d'ESTUDIANT"), 'error')
            # else:
            #     for item in vinculacio:
            #         if item['typology'] == 'EST':
            #             id_prisma = item['idorigen']
            #             student_data.update({'idPrisma': id_prisma})
            #             break

            # ONLY FOR TRY #####################

            list_test = [{'id_prisma': '2866124', 'numDocument': '44522242S'},
                         {'id_prisma': '2708530', 'numDocument': '47405847H'},
                         {'id_prisma': '2708479', 'numDocument': '41747970A'},
                         {'id_prisma': '2707723', 'numDocument': '18079004S'},
                         {'id_prisma': '2706798', 'numDocument': '48085070M'},
                         {'id_prisma': '2554111', 'numDocument': '53870113L'},
                         {'id_prisma': '2553255', 'numDocument': '39934092C'},
                         {'id_prisma': '2553249', 'numDocument': '53835514N'},
                         {'id_prisma': '2553092', 'numDocument': '26063484E'},
                         {'id_prisma': '2552221', 'numDocument': '21798723J'},
                         {'id_prisma': '2551839', 'numDocument': 'X2756193B'},
                         {'id_prisma': '2551740', 'numDocument': '73461145L'},
                         {'id_prisma': '2551700', 'numDocument': '41578237X'},
                         {'id_prisma': '2551388', 'numDocument': '47238061V'},
                         {'id_prisma': '2550963', 'numDocument': '48031179A'},
                         {'id_prisma': '2550923', 'numDocument': '79272419K'},
                         {'id_prisma': '2550789', 'numDocument': '53316254T'},
                         {'id_prisma': '2438885', 'numDocument': 'Y3346939Q'},
                         {'id_prisma': '2433865', 'numDocument': '70077461A'},
                         {'id_prisma': '2407950', 'numDocument': '05315643K'},
                         {'id_prisma': '2407902', 'numDocument': '41574784F'},
                         {'id_prisma': '2401711', 'numDocument': '47322096X'},
                         {'id_prisma': '2401541', 'numDocument': '77624311R'},
                         {'id_prisma': '2400827', 'numDocument': '17765920F'},
                         {'id_prisma': '2400653', 'numDocument': '47835848B'},
                         {'id_prisma': '2400648', 'numDocument': '48032008G'},
                         {'id_prisma': '2400208', 'numDocument': '39936041Z'},
                         {'id_prisma': '2400053', 'numDocument': '48037883Z'},
                         {'id_prisma': '2399504', 'numDocument': '25624813F'},
                         {'id_prisma': '2399333', 'numDocument': '45126841J'},
                         {'id_prisma': '2399207', 'numDocument': '47332956Z'},
                         {'id_prisma': '2399205', 'numDocument': '41597001Y'},
                         {'id_prisma': '2399187', 'numDocument': 'Y3541903D'},
                         {'id_prisma': '2398864', 'numDocument': '48037052B'},
                         {'id_prisma': '2398761', 'numDocument': '43575236B'},
                         {'id_prisma': '2398743', 'numDocument': '05458237S'},
                         {'id_prisma': '2398335', 'numDocument': '53292318F'},
                         {'id_prisma': '2398310', 'numDocument': '48090627L'},
                         {'id_prisma': '2398303', 'numDocument': '46414025W'},
                         {'id_prisma': '2398292', 'numDocument': '21780110F'},
                         {'id_prisma': '2398291', 'numDocument': '53869317M'},
                         {'id_prisma': '2398187', 'numDocument': '48019958Y'},
                         {'id_prisma': '2398145', 'numDocument': '47838860X'},
                         {'id_prisma': '2398058', 'numDocument': '48099790M'},
                         {'id_prisma': '2397841', 'numDocument': '23878574C'},
                         {'id_prisma': '2397674', 'numDocument': '47592922B'},
                         {'id_prisma': '2397654', 'numDocument': '43460008J'},
                         {'id_prisma': '2397644', 'numDocument': '48026090C'},
                         {'id_prisma': '2397485', 'numDocument': '43570423M'},
                         {'id_prisma': '2381463', 'numDocument': '47838895E'},
                         {'id_prisma': '2201379', 'numDocument': '41586362Q'},
                         {'id_prisma': '2195877', 'numDocument': '49876030R'},
                         {'id_prisma': '2184958', 'numDocument': '24412328J'},
                         {'id_prisma': '2174310', 'numDocument': '41549964G'},
                         {'id_prisma': '2174137', 'numDocument': '41583105W'},
                         {'id_prisma': '2173869', 'numDocument': '47962264L'},
                         {'id_prisma': '2173315', 'numDocument': '53399800X'},
                         {'id_prisma': '2167398', 'numDocument': '41577897S'},
                         {'id_prisma': '2167393', 'numDocument': '41645490B'},
                         {'id_prisma': '2166968', 'numDocument': '43230795H'},
                         {'id_prisma': '2166671', 'numDocument': '73221885M'},
                         {'id_prisma': '2166442', 'numDocument': '47929763V'},
                         {'id_prisma': '2166329', 'numDocument': '23821903K'},
                         {'id_prisma': '2166157', 'numDocument': '41600603C'},
                         {'id_prisma': '2166145', 'numDocument': '48036709J'},
                         {'id_prisma': '2166067', 'numDocument': '48270505Z'},
                         {'id_prisma': '2166005', 'numDocument': '39406537Q'},
                         {'id_prisma': '2165889', 'numDocument': '53866745D'},
                         {'id_prisma': '2165617', 'numDocument': '49285361H'},
                         {'id_prisma': '2165370', 'numDocument': '48138659G'},
                         {'id_prisma': '2164977', 'numDocument': '43636007Q'},
                         {'id_prisma': '2164887', 'numDocument': '48022181K'},
                         {'id_prisma': '2164805', 'numDocument': '39391127Q'},
                         {'id_prisma': '2164558', 'numDocument': '48097958J'},
                         {'id_prisma': '2164458', 'numDocument': '43205827M'},
                         {'id_prisma': '2164383', 'numDocument': '23821727Y'},
                         {'id_prisma': '2164117', 'numDocument': '46494260J'},
                         {'id_prisma': '2164001', 'numDocument': '45648881E'},
                         {'id_prisma': '2163975', 'numDocument': '45790582C'},
                         {'id_prisma': '2163779', 'numDocument': '23302009L'},
                         {'id_prisma': '2163595', 'numDocument': '47894493Y'},
                         {'id_prisma': '1953736', 'numDocument': 'Y0725916G'},
                         {'id_prisma': '1920503', 'numDocument': '47852616N'},
                         {'id_prisma': '1908655', 'numDocument': '47691604T'},
                         {'id_prisma': '1908273', 'numDocument': '48103682X'},
                         {'id_prisma': '1907783', 'numDocument': '39409440K'},
                         {'id_prisma': '1907709', 'numDocument': '48235146Y'},
                         {'id_prisma': '1907406', 'numDocument': '47276068M'},
                         {'id_prisma': '1907372', 'numDocument': '45832949K'}]

            from random import randint
            test_user = list_test[randint(0, len(list_test) - 1)]
            id_prisma = test_user['id_prisma']
            numDocument = test_user['numDocument']

            res_data = requests.get(bussoa_url + "%s" % id_prisma + '?tipusAltaTFE=' + "%s" % tipus_alta + '&numDocument=' + "%s" % numDocument, headers={'apikey': bussoa_apikey}, auth=(bussoa_user, bussoa_pass))

            if res_data.ok:
                data = res_data.json()
                num_expedients = data['llistatExpedients']

                if num_expedients:
                    student_data.update({'llista_expedients': num_expedients})
                else:
                    self.context.plone_utils.addPortalMessage(_(u"No tens número d'expedient a Prisma"), 'error')

            else:
                status_code = res_data.status_code
                reason = res_data.reason
                self.context.plone_utils.addPortalMessage(_(u"PRISMA id not found at PRISMA. %s" % (str(status_code) + ' ' + reason)), 'error')

        else:
            self.context.plone_utils.addPortalMessage(_(u"Usuari no trobat en el Ldap"), 'error')
        return student_data

    def render(self):
        current = api.user.get_current()
        data = self.getDadesStudent(current)
        return json.dumps(data)


class resetCountOffers(grok.View):
    grok.name('reset_count_offers')
    grok.context(Interface)
    grok.require('cmf.ManagePortal')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        if 'confirm' in self.request.form:
            registry = queryUtility(IRegistry)
            bussoa_tool = registry.forInterface(ITfemarketSettings)
            bussoa_tool.count_offers = 0
            transaction.commit()
            self.request.response.redirect(self.context.absolute_url() + "/tfemarket-settings#fieldsetlegend-2")
        else:
            current = api.user.get_current()
            lang = current.language
            if lang or lang == '':
                portal_state = self.context.unrestrictedTraverse("@@plone_portal_state")
                lang = portal_state.default_language()
            value = _(u'If you are doing the next action, it is because you have eliminated all the offers from the markets. Click on the following <a href=\"reset_count_offers?confirm\">link</a> to confirm the reset of the offers counter.')
            return translate(msgid=value, domain='genweb.tfemarket', target_language=lang)


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
