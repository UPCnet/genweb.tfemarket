from plone import api
from Products.PluggableAuthService.interfaces.plugins import IUserAdderPlugin
from Products.PlonePAS.interfaces.group import IGroupManagement

from genweb.tfemarket.interfaces import IGenwebTfemarketLayer

from five import grok
import pkg_resources
try:
    pkg_resources.get_distribution('Products.PloneLDAP')
except pkg_resources.DistributionNotFound:
    HAS_LDAP = False
else:
    HAS_LDAP = True
    from Products.LDAPUserFolder.LDAPUserFolder import LDAPUserFolder


class setupLDAPUPCMarket(grok.View):
    """ Configure LDAPUPC for TFEMARKET instance """
    grok.context(IGenwebTfemarketLayer)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = api.portal()
        ldap_name = self.request.form.get('ldap_name', 'ldap')
        ldap_acl_users = getattr(portal.acl_users, ldap_name).acl_users

        # Add schema properties

        LDAPUserFolder.manage_addLDAPSchemaItem(ldap_acl_users, ldap_name='unit', friendly_name='Unit', public_name='unit', multi_value=True)
        LDAPUserFolder.manage_addLDAPSchemaItem(ldap_acl_users, ldap_name='segmentation', friendly_name='Segmentation',public_name='segmentation', multi_value=True)
