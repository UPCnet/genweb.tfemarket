# -*- coding: utf-8 -*-

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.testing import z2

import genweb.tfemarket


class GenwebTfemarketLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=genweb.tfemarket)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'genweb.tfemarket:default')


GENWEB_TFEMARKET_FIXTURE = GenwebTfemarketLayer()


GENWEB_TFEMARKET_INTEGRATION_TESTING = IntegrationTesting(
    bases=(GENWEB_TFEMARKET_FIXTURE,),
    name='GenwebTfemarketLayer:IntegrationTesting'
)


GENWEB_TFEMARKET_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(GENWEB_TFEMARKET_FIXTURE,),
    name='GenwebTfemarketLayer:FunctionalTesting'
)


GENWEB_TFEMARKET_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        GENWEB_TFEMARKET_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='GenwebTfemarketLayer:AcceptanceTesting'
)
