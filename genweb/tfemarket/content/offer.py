# -*- coding: utf-8 -*-

from five import grok
from operator import itemgetter
from plone import api
from plone.app.textfield import RichText as RichTextField
from plone.autoform import directives
from plone.directives import form, dexterity
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.utils import checkEmailAddress
from Products.CMFDefault.exceptions import EmailAddressInvalid
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.schema import ValidationError
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.security import checkPermission

from genweb.tfemarket import _
from genweb.tfemarket.content.application import IApplication
from genweb.tfemarket.controlpanel import ITfemarketSettings

from genweb.tfemarket.utils import checkPermissionCreateApplications as CPCreateApplications

from genweb.tfemarket.utils import getLdapUserData

import unicodedata


grok.templatedir("templates")


class InvalidEmailAddress(ValidationError):
    "Invalid email address"


class LangsVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        results = ()
        languages = []

        langs = tfe_tool.languages
        if langs:
            results = langs.split("\r\n")

        for item in results:
            if isinstance(item, str):
                flattened = unicodedata.normalize('NFKD', item.decode('utf-8')).encode('ascii', errors='ignore')
            else:
                flattened = unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')
            languages.append(SimpleVocabulary.createTerm(item, flattened, item))

        return SimpleVocabulary(languages)


grok.global_utility(LangsVocabulary, name=u"genweb.tfemarket.Langs")


class KeysVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        results = []
        tags = []

        keys = tfe_tool.tags
        if keys:
            results = keys.split("\r\n")

        for item in results:
            if isinstance(item, str):
                flattened = unicodedata.normalize('NFKD', item.decode('utf-8')).encode('ascii', errors='ignore')
            else:
                flattened = unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')
            tags.append(SimpleVocabulary.createTerm(item, flattened, item))

        return SimpleVocabulary(tags)


grok.global_utility(KeysVocabulary, name=u"genweb.tfemarket.Keys")


class TopicsVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        results = []
        topic = []

        topics = tfe_tool.topics
        if topics:
            results = topics.split("\r\n")

        for item in results:
            if isinstance(item, str):
                flattened = unicodedata.normalize('NFKD', item.decode('utf-8')).encode('ascii', errors='ignore')
            else:
                flattened = unicodedata.normalize('NFKD', item).encode('ascii', errors='ignore')
            topic.append(SimpleVocabulary.createTerm(item, flattened, item))

        return SimpleVocabulary(topic)


grok.global_utility(TopicsVocabulary, name=u"genweb.tfemarket.Topics")


class DegreesVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
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


grok.global_utility(DegreesVocabulary, name=u"genweb.tfemarket.Titulacions")


def validateaddress(value):
    try:
        checkEmailAddress(value)
    except EmailAddressInvalid:
        raise InvalidEmailAddress(value)
    return True


class IOffer(form.Schema):
    """ Folder that contains information about a TFE and its applications
    """

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
        vocabulary=u"genweb.tfemarket.Topics",
        required=False
    )

    requirements = RichTextField(
        title=_(u'requirements'),
        required=False,
    )

    form.widget(lang=CheckBoxFieldWidget)
    lang = schema.List(
        value_type=schema.Choice(vocabulary=u"genweb.tfemarket.Langs"),
        title=_(u'tfe_lang'),
        required=False,
    )

    grant = schema.Bool(
        title=_(u'grant'),
        required=False,
        default=False,
    )

    form.widget(degree=CheckBoxFieldWidget)
    degree = schema.List(
        value_type=schema.Choice(source=u"genweb.tfemarket.Titulacions"),
        title=_(u'degree'),
        required=False,
    )

    modality = schema.Choice(
        title=_(u'modality'),
        values=[u'Universitat',
                u'Empresa'],
        default=_(u'Universitat'),
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

    teacher_email = schema.TextLine(
        title=_(u'Teacher Email'),
        required=False,
        constraint=validateaddress,
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

    form.widget(keys=CheckBoxFieldWidget)
    keys = schema.List(
        value_type=schema.Choice(source=u"genweb.tfemarket.Keys"),
        title=_(u'keys'),
        required=False,
    )


@grok.subscribe(IOffer, IObjectAddedEvent)
def numOfferDefaultValue(offer, event):
    total_offers = len(
        api.content.find(
            portal_type='genweb.tfemarket.offer')
    )

    registry = queryUtility(IRegistry)
    tfe_tool = registry.forInterface(ITfemarketSettings)
    center = tfe_tool.center_code
    total = total_offers

    offer.offer_id = str(center) + '-' + str(total).zfill(5)
    offer.reindexObject()


class View(dexterity.DisplayForm):
    """The view. May will a template from <modulename>_templates/view.pt,
    and will be called 'view' unless otherwise stated.
    """
    grok.require('zope2.View')
    grok.context(IOffer)
    grok.template('offer_view')

    def formatDate(self, date):
        return date.strftime('%d/%m/%Y')

    def getDegrees(self):
        registry = queryUtility(IRegistry)
        tfe_tool = registry.forInterface(ITfemarketSettings)
        current_language = api.portal.get_current_language()

        result = []
        if tfe_tool.titulacions_table:
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
        result.insert(0, {'id': 'a', 'lit': _(u"All")})
        return result

    def getDegreeLiteralFromId(self, id):
        degrees = self.getDegrees()
        degree = _(u'Degree deleted')
        result = [item['lit'] for item in degrees if item['id'] == id]
        if result:
            degree = result[0]
        return degree

    def getRaw(self, raw):
        return raw.raw_encoded if hasattr(raw, 'raw_encoded') else None

    def getApplications(self, offer):
        name_teacher = u'esteve.pallares'
        lala = getLdapUserData(name_teacher)
        catalog = api.portal.get_tool(name='portal_catalog')
        wf_tool = getToolByName(self.context, 'portal_workflow')
        tools = getMultiAdapter((self.context, self.request), name='plone_tools')
        results = []
        values = catalog(path={'query': '/'.join(offer.getPhysicalPath()), 'depth': 1},
                         object_provides=IApplication.__identifier__)

        for item in values:
            application = item.getObject()
            workflowActions = wf_tool.listActionInfos(object=application)
            workflows = tools.workflow().getWorkflowsFor(application)[0]

            results.append(dict(title=item.Title,
                                state=workflows['states'][item.review_state].title,
                                url=item.getURL(),
                                item_path=application.absolute_url_path(),
                                dni=application.dni,
                                name=application.title,
                                offer_id=application.offer_id,
                                offer_title=application.offer_title,
                                workflows=workflowActions,
                                can_edit=checkPermission('cmf.ModifyPortalContent', application),
                                ))
        return results

    def checkPermissionCreateApplications(self):
        return CPCreateApplications(self, self.context)


class AddForm(dexterity.AddForm):
    grok.context(IOffer)
    grok.name('offer')
