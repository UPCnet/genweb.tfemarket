# -*- coding: utf-8 -*-
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from genweb.tfemarket.interfaces import IProposal
from genweb.tfemarket.testing import GENWEB_TFEMARKET_INTEGRATION_TESTING  # noqa
from zope.component import createObject
from zope.component import queryUtility

import unittest


class ProposalIntegrationTest(unittest.TestCase):

    layer = GENWEB_TFEMARKET_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_schema(self):
        fti = queryUtility(IDexterityFTI, name='Proposal')
        schema = fti.lookupSchema()
        self.assertEqual(IProposal, schema)

    def test_fti(self):
        fti = queryUtility(IDexterityFTI, name='Proposal')
        self.assertTrue(fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI, name='Proposal')
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(IProposal.providedBy(obj))

    def test_adding(self):
        obj = api.content.create(
            container=self.portal,
            type='Proposal',
            id='Proposal',
        )
        self.assertTrue(IProposal.providedBy(obj))
