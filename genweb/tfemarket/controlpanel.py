# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from five import grok
from plone.app.registry.browser import controlpanel
from plone.autoform import directives
from plone.directives import form
from plone.supermodel import model
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory

from genweb.tfemarket import _


class ITableTitulacions(form.Schema):

    codi_prisma = schema.TextLine(
        title=_(u'PRISMA code'),
        required=False,
        description=_(u'Degree code at PRISMA')
    )

    progam_type = schema.TextLine(
        title=_(u'Program type'),
        required=False
    )

    codi_mec = schema.TextLine(
        title=_(u'MEC code'),
        required=False,
        description=_(u'MEC degree code')
    )

    plan_year = schema.TextLine(
        title=_(u'Plan year'),
        required=False,
    )

    titulacio_es = schema.TextLine(
        title=_(u'Titulacions ES'),
        description=_(u''),
        required=False
    )

    titulacio_ca = schema.TextLine(
        title=_(u'Titulacions CA'),
        description=_(u''),
        required=False
    )

    titulacio_en = schema.TextLine(
        title=_(u'Titulacions EN'),
        description=_(u''),
        required=False
    )


class EnrollVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        types = []
        types.append(SimpleVocabulary.createTerm(u'I', 'I', _(u'Enroll')))
        types.append(SimpleVocabulary.createTerm(u'R', 'R', _(u'Register')))
        return SimpleVocabulary(types)


grok.global_utility(EnrollVocabulary, name=u"genweb.tfemarket.Enrolls")


class AllLanguageVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        languages = []
        languages.append(SimpleVocabulary.createTerm(u'CA', 'CA', _(u'CA')))
        languages.append(SimpleVocabulary.createTerm(u'ES', 'ES', _(u'ES')))
        languages.append(SimpleVocabulary.createTerm(u'EN', 'EN', _(u'EN')))
        languages.append(SimpleVocabulary.createTerm(u'FR', 'FR', _(u'FR')))
        return SimpleVocabulary(languages)


grok.global_utility(AllLanguageVocabulary, name=u"genweb.tfemarket.AllLanguages")


class ITfemarketSettings(model.Schema):
    """ Global TFE Market settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    model.fieldset(
        'Settings',
        _(u'Settings'),
        fields=['center_code', 'center_name', 'review_state', 'enroll_type'],
    )

    model.fieldset(
        'Titulacions',
        _(u'Titulacions'),
        fields=['titulacions_table'],
    )

    model.fieldset(
        'Ofertes',
        _(u'Ofertes'),
        fields=['life_period', 'import_offers', 'count_offers']
    )

    model.fieldset(
        'TopicTFE',
        _(u'classifications'),
        fields=['topics', 'tags', 'languages'],
    )

    # SETTINGS

    center_code = schema.Int(
        title=_(u'Center code'),
        required=False,
        description=_(u'Center code')
    )

    center_name = schema.TextLine(
        title=_(u"Name center"),
        required=False,
    )

    review_state = schema.Bool(
        title=_(u"Review State"),
        default=False,
        description=_(u'Select if you want to add "Reviewer" role'),
        required=False,
    )

    enroll_type = schema.Choice(
        title=_(u'Enroll type '),
        description=_('Parameter to post the student enroll'),
        vocabulary=u"genweb.tfemarket.Enrolls",
        default=u'I',
        required=True)

    # CLASSIFICATIONS

    topics = schema.Text(
        title=_(u"Topics of the TFE"),
        description=_(u'Add topics one per line'),
        required=False,
    )

    tags = schema.Text(
        title=_(u"Tags"),
        description=_(u'Add tags one per line'),
        required=False,
    )

    form.widget(languages=CheckBoxFieldWidget)
    languages = schema.List(
        title=_(u"Development languages"),
        description=_(u'Add languages one per line'),
        value_type=schema.Choice(source=u"genweb.tfemarket.AllLanguages"),
        required=False,
    )

    # TITULACIONS

    form.widget(titulacions_table=DataGridFieldFactory)
    titulacions_table = schema.List(title=_(u'Titulacions'),
                                    description=_(u'help_titulacions_table',
                                    default=u'Imported dades from csv'),
                                    value_type=DictRow(title=_(u'titulacionstable'),
                                                       schema=ITableTitulacions),
                                    required=False
                                    )

    # OFERTES

    life_period = schema.Int(
        title=_(u'Months until expiration'),
        description=_('Months until the offer expires automatically'),
        required=True,
        default=12,
    )

    directives.mode(import_offers="display")
    import_offers = schema.Text(
        title=_(u"Import offers"),
        description=_(u'To import the offers access the following <a href=\"import_ofertes\">link</a>.'),
        required=False,
    )

    directives.mode(count_offers="display")
    count_offers = schema.Int(
        title=_(u"Number of offers created"),
        description=_(u'To reset the counter access the following <a href=\"reset_offers_counter\">link</a>.'),
        required=False,
        default=0,
    )


class TfemarketSettingsEditForm(controlpanel.RegistryEditForm):

    schema = ITfemarketSettings
    label = _(u'UPC Mercat TFE')


class TfemarketSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = TfemarketSettingsEditForm


class IBUSSOASettings(model.Schema):
    """ Global BUS SOA TFE Market settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """
    # BUS SOA

    bus_url = schema.TextLine(
        title=_(u'URL'),
        description=_(u'URL to access the bus'),
        required=False)

    bus_user = schema.TextLine(
        title=_(u'User'),
        description=_('User to connect to the bus'),
        required=False)

    bus_password = schema.Password(
        title=_(u'Password'),
        required=False)

    bus_apikey = schema.Password(
        title=_(u'APIKEY'),
        required=False)


class BUSSOASettingsEditForm(controlpanel.RegistryEditForm):

    schema = IBUSSOASettings
    label = _(u'BUS SOA TFE')


class BUSSOASettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = BUSSOASettingsEditForm
