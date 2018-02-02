# -*- coding: utf-8 -*-

from five import grok
from plone.directives import form
from zope import schema

from genweb.tfemarket import _

from zope.schema.interfaces import IContextSourceBinder
from plone.app.textfield import RichText as RichTextField
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from zope.schema.interfaces import IVocabularyFactory


class KeysVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        topics = SimpleVocabulary([SimpleTerm(value=u'Bill', title=_(u'A')),
                                   SimpleTerm(value=u'Bob', title=_(u'B')),
                                   SimpleTerm(value=u'Jim', title=_(u'C'))
                                   ])
        return topics


grok.global_utility(KeysVocabulary, name=u"genweb.tfemarket.Keys")


@grok.provider(IContextSourceBinder)
def possibleTopics(context):
    topics = SimpleVocabulary([SimpleTerm(value=u'Bill', title=_(u'uno')),
                               SimpleTerm(value=u'Bob', title=_(u'dos')),
                               SimpleTerm(value=u'Jim', title=_(u'tres'))
                               ])
    return topics


class IOffer(form.Schema):
    """ Folder that contains information about a TFE and its applications
    """
    id_offer = schema.TextLine(
        title=_(u'idoffer'),
        required=False,
    )

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = RichTextField(
        title=_(u'Description'),
        required=False,
    )

    features = RichTextField(
        title=_(u'offer_features'),
        required=False,
    )

    topic = schema.Choice(
        title=_(u'offer_topic'),
        source=possibleTopics,
        required=False)

    keys = schema.Choice(
        title=_(u'keys'),
        vocabulary=u"genweb.tfemarket.Keys",
        required=False,
    )

    requirements = schema.TextLine(
        title=_(u'requirements'),
        required=False,
    )

    lang = schema.TextLine(
        title=_(u'tfe_lang'),
        required=False,
    )

    grant = schema.TextLine(
        title=_(u'grant'),
        required=False,
    )

    center = schema.TextLine(
        title=_(u'offer_center'),
        required=False,
    )

    degree = schema.TextLine(
        title=_(u'degree'),
        required=False,
    )

    modality = schema.TextLine(
        title=_(u'modality'),
        required=False,
    )

    teacher_manager = schema.TextLine(
        title=_(u'TFEteacher'),
        required=False,
    )

    company = schema.TextLine(
        title=_(u'company'),
        required=False,
    )

    company_contact = schema.TextLine(
        title=_(u'Company Contact'),
        required=False,
    )

    num_students = schema.TextLine(
        title=_(u'Number of students'),
        required=False,
    )

    entry_date = schema.TextLine(
        title=_(u'Entry date'),
        required=False,
    )

    confidential = schema.TextLine(
        title=_(u'confidential'),
        required=False,
    )
