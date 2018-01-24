# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s genweb.tfemarket -t test_proposal.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src genweb.tfemarket.testing.GENWEB_TFEMARKET_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot src/plonetraining/testing/tests/robot/test_proposal.robot
#
# See the http://docs.plone.org for further details (search for robot
# framework).
#
# ============================================================================

*** Settings *****************************************************************

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***************************************************************

Scenario: As a site administrator I can add a Proposal
  Given a logged-in site administrator
    and an add proposal form
   When I type 'My Proposal' into the title field
    and I submit the form
   Then a proposal with the title 'My Proposal' has been created

Scenario: As a site administrator I can view a Proposal
  Given a logged-in site administrator
    and a proposal 'My Proposal'
   When I go to the proposal view
   Then I can see the proposal title 'My Proposal'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add proposal form
  Go To  ${PLONE_URL}/++add++Proposal

a proposal 'My Proposal'
  Create content  type=Proposal  id=my-proposal  title=My Proposal


# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.title  ${title}

I submit the form
  Click Button  Save

I go to the proposal view
  Go To  ${PLONE_URL}/my-proposal
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a proposal with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the proposal title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
