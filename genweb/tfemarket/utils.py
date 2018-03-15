from Acquisition import aq_inner
from plone import api
from Products.CMFCore.utils import getToolByName
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sendMessage(context, fromMsg, toMsg, subject, message):
    portal = api.portal
    context = aq_inner(context)
    mailhost = getToolByName(context, 'MailHost')

    msg = MIMEMultipart()
    msg['From'] = fromMsg
    msg['To'] = toMsg
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))
    mailhost.send(msg)
