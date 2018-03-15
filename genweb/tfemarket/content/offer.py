# -*- coding: utf-8 -*-

from five import grok
from operator import itemgetter
from plone import api
from plone.app.textfield import RichText as RichTextField
from plone.autoform import directives
from plone.directives import form, dexterity
from plone.supermodel.directives import fieldset
from plone.registry.interfaces import IRegistry
from zope import schema
from zope.component import queryUtility
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from genweb.tfemarket import _
from genweb.tfemarket.controlpanel import ITfemarketSettings

from zope.schema import ValidationError
from Products.CMFDefault.utils import checkEmailAddress
from Products.CMFDefault.exceptions import EmailAddressInvalid

grok.templatedir("templates")


class InvalidEmailAddress(ValidationError):
    "Invalid email address"


class KeysVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        topics = SimpleVocabulary([SimpleTerm(value=u'Bill', title=(u'A')),
                                   SimpleTerm(value=u'Bob', title=(u'B')),
                                   SimpleTerm(value=u'Jim', title=(u'C'))
                                   ])
        return topics


grok.global_utility(KeysVocabulary, name=u"genweb.tfemarket.Keys")


@grok.provider(IContextSourceBinder)
def possibleTopics(context):
    topics = SimpleVocabulary([SimpleTerm(value=u'Bill', title=(u'uno')),
                               SimpleTerm(value=u'Bob', title=(u'dos')),
                               SimpleTerm(value=u'Jim', title=(u'tres'))
                               ])
    return topics


@grok.provider(IContextSourceBinder)
def possibleDegrees(context):
    registry = queryUtility(IRegistry)
    tfe_tool = registry.forInterface(ITfemarketSettings)
    current_language = api.portal.get_current_language()

    result = []
    for item in tfe_tool.titulacions_table:
        titulacio = str(item['plan_year']) + " - "
        if current_language == 'ca':
            titulacio += item['titulacio_ca']
        elif current_language == 'es':
            titulacio += item['titulacio_es']
        else:
            titulacio += item['titulacio_en']

        result.append({'id': item['codi_prisma'], 'lit': titulacio})

    result = sorted(result, key=itemgetter('lit'))

    titulacions = []
    for item in result:
        titulacions.append(SimpleTerm(value=item['id'], title=item['lit']))

    return SimpleVocabulary(titulacions)


def validateaddress(value):
    try:
        checkEmailAddress(value)
    except EmailAddressInvalid:
        raise InvalidEmailAddress(value)
    return True


class IOffer(form.Schema):
    """ Folder that contains information about a TFE and its applications
    """

    # fieldset('data',
    #          label=_(u''),
    #          fields=['degree', 'offer_id', 'title', 'description', 'targets', 'workload', 'features', 'topic']
    #          )

    fieldset('direccio',
             label=_(u''),
             fields=['teacher_manager', 'dept']
             )

    fieldset('requisits',
             label=_(u''),
             fields=['requirements', 'lang', 'num_students']
             )

    fieldset('options',
             label=_(u''),
             fields=['grant', 'modality', 'confidential', 'environmental_theme', 'scope_cooperation', 'keys']
             )

    fieldset('modalitat',
             label=_(u''),
             fields=['modality', 'co_manager', 'company', 'company_contact', 'company_email']
             )

    form.mode(center='hidden')
    center = schema.TextLine(
        title=_(u'offer_center'),
        default=u"el centro",
        required=False,
    )

    directives.mode(offer_id="hidden")
    offer_id = schema.TextLine(
        title=_(u'Offer id'),
        required=False,
    )

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        required=False,
    )

    targets = RichTextField(
        title=_(u'offer_targets'),
        required=False,
    )

    workload = schema.Text(
        title=_(u'offer_workload'),
        required=False,
    )

    features = RichTextField(
        title=_(u'offer_features'),
        required=False,
    )

    topic = schema.Choice(
        title=_(u'offer_topic'),
        source=possibleTopics,
        required=False
    )

    requirements = RichTextField(
        title=_(u'requirements'),
        required=False,
    )

    lang = schema.Choice(
        title=_(u'tfe_lang'),
        values=[_(u"Catalan"),
                _(u"Spanish"),
                _(u"English")],
        required=False,
    )

    grant = schema.Bool(
        title=_(u'grant'),
        required=False,
        default=False,
    )

    degree = schema.Choice(
        title=_(u'degree'),
        source=possibleDegrees,
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

    co_manager = schema.TextLine(
        title=_(u'CoManager'),
        required=False,
    )

    company = schema.TextLine(
        title=_(u'Company'),
        required=False,
    )

    company_contact = schema.TextLine(
        title=_(u'Company Contact'),
        required=False,
    )

    company_email = schema.TextLine(
        title=_(u'Company Email'),
        required=False,
        constraint=validateaddress,
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

    environmental_theme = schema.Bool(
        title=_(u'Environmental Theme'),
        default=False,
        required=False,
    )

    scope_cooperation = schema.Bool(
        title=_(u'Scope of cooperation'),
        default=False,
        required=False,
    )

    keys = schema.Choice(
        title=_(u'keys'),
        vocabulary=u"genweb.tfemarket.Keys",
        required=False,
    )


class View(dexterity.DisplayForm):
    """The view. May will a template from <modulename>_templates/view.pt,
    and will be called 'view' unless otherwise stated.
    """
    grok.require('zope2.View')
    grok.context(IOffer)
    grok.template('offer_view')


class AddForm(dexterity.AddForm):
    grok.context(IOffer)
    grok.name('offer')
