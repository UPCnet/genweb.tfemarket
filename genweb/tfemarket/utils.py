from Acquisition import aq_inner
from plone import api
from Products.CMFCore.utils import getToolByName
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zope.component import getMultiAdapter


def sendMessage(context, fromMsg, toMsg, subject, message):
    context = aq_inner(context)
    mailhost = getToolByName(context, 'MailHost')

    msg = MIMEMultipart()
    msg['From'] = fromMsg
    msg['To'] = toMsg
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))
    mailhost.send(msg)


def canDoAction(self, context, action):
    context_state = getMultiAdapter((context, self.request), name=u'plone_context_state')
    actions = context_state.actions('object')

    for item in actions:
        if item['id'] == action and item['visible'] and item['allowed']:
            return True

    return False


def getLdapUserData(director):
    """Create a new gengrup user by email. You have to call
       updateUserSitesCatalog to get the new user into the
       user_sites_catalog.
    """

    acl_users = api.portal.get_tool(name='acl_users')

    import ipdb; ipdb.set_trace()

    search_result = acl_users.searchUsers(id=director, exactMatch=True)

    return search_result
