# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
from plone import api

from Products.LDAPUserFolder.LDAPUserFolder import LDAPUserFolder


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller"""
        return [
            'genweb.tfemarket:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.

def setLdapMerkat(context):
        import ipdb; ipdb.set_trace()
        portal = context.getSite()
        #ldap_name = context.request.form.get('ldap_name', 'ldap')
        ldap_name = 'ldapUPC'

        ldap_acl_users = getattr(portal.acl_users, ldap_name).acl_users

        # Add schema properties

        LDAPUserFolder.manage_addLDAPSchemaItem(ldap_acl_users, ldap_name='unit', friendly_name='Unit', public_name='unit', multi_value=True)
        LDAPUserFolder.manage_addLDAPSchemaItem(ldap_acl_users, ldap_name='segmentation', friendly_name='Segmentation',public_name='segmentation', multi_value=True)
