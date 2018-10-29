# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces import INonInstallable
from Products.LDAPUserFolder.LDAPUserFolder import LDAPUserFolder
from zope.interface import implementer


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
    if context.readDataFile('genweb.tfemarket_ldap.txt') is None:
        return

    portal = context.getSite()
    ldap_acl_users = getattr(portal.acl_users, 'ldapUPC').acl_users
    LDAPUserFolder.manage_deleteLDAPSchemaItems(
        ldap_acl_users,
        ldap_names=['sn1', 'sn2', 'aliesnom', 'unit', 'unitCode', 'segmentation', 'typology', 'DNIpassport', 'telephoneNumber', 'mail'],
        REQUEST=None)


def setupLdapMarket(context):
    # Ordinarily, GenericSetup handlers check for the existence of XML files.
    # Here, we are not parsing an XML file, but we use this text file as a
    # flag to check that we actually meant for this import step to be run.
    # The file is found in profiles/default.

    if context.readDataFile('genweb.tfemarket_ldap.txt') is None:
        return

    portal = context.getSite()
    ldap_acl_users = getattr(portal.acl_users, 'ldapUPC').acl_users
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='sn1', friendly_name='Surname 1',
        public_name='sn1', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='sn2', friendly_name='Surname 2',
        public_name='sn2', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='aliesnom', friendly_name='Name',
        public_name='aliesnom', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='unit', friendly_name='Unit',
        public_name='unit', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='unitCode', friendly_name='Unit Code',
        public_name='unitCode', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='segmentation', friendly_name='Segmentation',
        public_name='segmentation', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='typology', friendly_name='Typology',
        public_name='typology', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='DNIpassport', friendly_name='DNI',
        public_name='DNIpassport', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='idorigen', friendly_name='Identifier',
        public_name='Identifier', multivalued=True)
    LDAPUserFolder.manage_addLDAPSchemaItem(
        ldap_acl_users, ldap_name='mail', friendly_name='eMail',
        public_name='mail', multivalued=False)
