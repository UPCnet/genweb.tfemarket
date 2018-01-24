# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from genweb.tfemarket.testing import GENWEB_TFEMARKET_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that genweb.tfemarket is properly installed."""

    layer = GENWEB_TFEMARKET_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if genweb.tfemarket is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'genweb.tfemarket'))

    def test_browserlayer(self):
        """Test that IGenwebTfemarketLayer is registered."""
        from genweb.tfemarket.interfaces import (
            IGenwebTfemarketLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IGenwebTfemarketLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = GENWEB_TFEMARKET_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['genweb.tfemarket'])

    def test_product_uninstalled(self):
        """Test if genweb.tfemarket is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'genweb.tfemarket'))

    def test_browserlayer_removed(self):
        """Test that IGenwebTfemarketLayer is removed."""
        from genweb.tfemarket.interfaces import \
            IGenwebTfemarketLayer
        from plone.browserlayer import utils
        self.assertNotIn(
           IGenwebTfemarketLayer,
           utils.registered_layers())
