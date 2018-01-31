# -*- coding: utf-8 -*-

from plone.directives import form
from zope import schema

from genweb.tfemarket import _


class IOffer(form.Schema):
    """ Folder that contains all request to a TFE
    """
    id_offer = schema.TextLine(
        title=_(u'idoffer'),
        required=True,
    )

    features = schema.TextLine(
        title=_(u'offer_features'),
        required=True,
    )

    topic = schema.TextLine(
        title=_(u'offer_topic'),
        required=True,
    )

    keys = schema.TextLine(
        title=_(u'keys'),
        required=True,
    )

    requirements = schema.TextLine(
        title=_(u'requirements'),
        required=True,
    )

    lang = schema.TextLine(
        title=_(u'tfe_lang'),
        required=True,
    )

    grant = schema.TextLine(
        title=_(u'grant'),
        required=True,
    )

    center = schema.TextLine(
        title=_(u'offer_center'),
        required=True,
    )

    degree = schema.TextLine(
        title=_(u'degree'),
        required=True,
    )

    modality = schema.TextLine(
        title=_(u'modality'),
        required=True,
    )

    teacher_manager = schema.TextLine(
        title=_(u'TFEteacher'),
        required=True,
    )

    company = schema.TextLine(
        title=_(u'company'),
        required=True,
    )

    company_contact = schema.TextLine(
        title=_(u'Company Contact'),
        required=True,
    )

    num_students = schema.TextLine(
        title=_(u'Number of students'),
        required=True,
    )

    entry_date = schema.TextLine(
        title=_(u'Entry date'),
        required=True,
    )

    confidential = schema.TextLine(
        title=_(u'confidential'),
        required=True,
    )
