# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from five import grok
from plone import api
from plone.registry.interfaces import IRegistry
from zope.i18n import translate
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.interface import Interface

from genweb.tfemarket import _
from genweb.tfemarket.content.offer import IOffer
from genweb.tfemarket.controlpanel import ITfemarketSettings
from genweb.tfemarket.interfaces import IGenwebTfemarketLayer
from genweb.tfemarket.utils import getLdapExactUserData
from genweb.tfemarket.utils import getLdapUserData

import json
import transaction
import requests
import ldap


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
            currentitem = portal.unrestrictedTraverse(itemid)
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
    # grok.require('zope2.View')
    grok.require('cmf.AddPortalContent')
    grok.layer(IGenwebTfemarketLayer)

    def getIdPrisma(self, cn):
        prisma_id = ('836')
        results = self.LDAPSearch(cn)
        results['content'][0].update({'union': zip(*[results['content'][0][field].split(' // ')
                                      for field in ['segmentation', 'unit', 'typology', 'idorigen']])})
        import ipdb; ipdb.set_trace()
        return (prisma_id, results)

    def LDAPSearch(self, query, isQueryAlreadyMade=False):
        def return_dict(ok, content):
            return {'ok': ok, 'content': content}

        def create_query(query):
            fields = ['sn', 'cn']
            return '(|' + ''.join('(%s=*%s*)' % (fieldname, query) for fieldname in fields) + ')'

        if not query:
            return return_dict(False, 'Query should not be empty')

        result_set = []
        acl_users = getToolByName(self.context, 'acl_users').ldapUPC.acl_users
        ldap_pwd = acl_users._bindpwd
        ldap_binduid = acl_users._binduid
        ldap_server = acl_users.getServers()[0]
        server = "%s://%s:%s" % (ldap_server['protocol'], ldap_server['host'], ldap_server['port'])
        try:
            ldapservice = ldap.initialize(server)
            ldapservice.simple_bind_s(ldap_binduid, ldap_pwd)
            ldapservice.protocol_version = ldap.VERSION3
            ldapservice.op_timeout = ldap_server['op_timeout']
            ldap_result_id = ldapservice.search(
                acl_users.users_base,
                acl_users.users_scope,
                query if isQueryAlreadyMade else create_query(query),
                None
            )
            while True:
                result_type, result_data = ldapservice.result(ldap_result_id, 0)
                if result_data == []:
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        person_info = result_data[0][1]
                        returnfields = [
                            ('username', 'cn'),
                            ('givenName', 'givenName'),
                            ('firstSurname', 'sn1'),
                            ('secondSurname', 'sn2'),
                            ('dni', 'DNIpassport'),
                            ('segmentation', 'segmentation'),
                            ('typology', 'typology'),
                            ('unit', 'unit'),
                            ('idorigen', 'idorigen')
                        ]
                        result_set.append({key: ' // '.join(person_info.get(value, [''])) for key, value in returnfields})

        except ldap.LDAPError as e:
            return return_dict(False, e[0])
        else:
            return return_dict(True, result_set)
        finally:
            ldapservice.unbind_s()

    def render(self):
        current = api.user.get_current()
        user = getLdapExactUserData(current.id)
        data = {}
        if user and 'sn' in user:
            data = {
                'offer_id': self.context.offer_id,
                'offer_title': self.context.title,
                'fullname': user['sn'],
                'dni': user['DNIpassport'],
                'email': user['mail']
            }

            if 'telephoneNumber' in user:
                data.update({'phone': user['telephoneNumber']})

        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        id_prisma = self.getIdPrisma('corina.riba')

        bussoa_url = tfe_tool.bus_url
        bussoa_user = tfe_tool.bus_user
        bussoa_pass = tfe_tool.bus_password
        bussoa_apikey = tfe_tool.bus_apikey

        res_data = requests.get(bussoa_url + "%s" % (id_prisma), headers={'apikey': bussoa_apikey}, auth=(bussoa_user, bussoa_pass))
        student_data = res_data.json()

        if res_data.ok:
            student_data = res_data.json()
            data.update({'llista_expedients': student_data['llistatExpedients']})
        else:
            status_code = res_data.status_code
            reason = res_data.reason
            resultat = student_data['resultat']

            return (status_code, reason, resultat)

        return json.dumps(data)


class resetCountOffers(grok.View):
    grok.name('reset_count_offers')
    grok.context(Interface)
    grok.require('cmf.ManagePortal')
    grok.layer(IGenwebTfemarketLayer)

    def render(self):
        if 'confirm' in self.request.form:
            registry = queryUtility(IRegistry)
            tfe_tool = registry.forInterface(ITfemarketSettings)
            tfe_tool.count_offers = 0
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
