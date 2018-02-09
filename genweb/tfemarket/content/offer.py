# -*- coding: utf-8 -*-

from five import grok
from plone.directives import form
from zope import schema
from genweb.tfemarket import _
from plone.autoform import directives
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
    directives.mode(offer_id="display")
    offer_id = schema.TextLine(
        title=_(u'Offer id'),
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

    requirements = RichTextField(
        title=_(u'requirements'),
        required=False,
    )

    lang = schema.Choice(
        title=_(u'tfe_lang'),
        values=[u"Català",
                u"Español",
                u"English"],
        required=False,
    )

    grant = schema.Bool(
        title=_(u'grant'),
        required=False,
        default=False,
    )

    form.mode(center='display')
    center = schema.TextLine(
        title=_(u'offer_center'),
        default=u"el centro",
        required=False,
    )

    degree = schema.TextLine(
        title=_(u'degree'),
        required=False,
    )

    modality = schema.Choice(
        title=_(u'modality'),
        values=[u'Universitat',
                u'Empresa'],
        required=False,
    )

    teacher_manager = schema.TextLine(
        title=_(u'TFEteacher'),
        required=False,
    )

    dept = schema.TextLine(
        title=_(u'University department'),
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

    num_students = schema.Int(
        title=_(u'Number of students'),
        description=_(u'Number of students for the TFE (1 to 10)'),
        default=1,
        min=1,
        max=10,
        required=False,
    )

    confidential = schema.Bool(
        title=_(u'confidential'),
        default=False,
        required=False,
    )
