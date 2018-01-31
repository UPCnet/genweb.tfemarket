# -*- coding: utf-8 -*-

from zope import schema
from z3c.form import button
from plone.supermodel import model
from plone.app.registry.browser import controlpanel
from Products.statusmessages.interfaces import IStatusMessage

from genweb.tfemarket import _


class ITfemarketSettings(model.Schema):
    """ Global TFE Market settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    model.fieldset(
        'Titulacions',
        _(u'Titulacions'),
        fields=['field1'],
    )

    model.fieldset(
        'Professors',
        _(u'Professors'),
        fields=['field2'],
    )

    model.fieldset(
        'Temes',
        _(u'Temes'),
        fields=['field3'],
    )

    field1 = schema.TextLine(
        title=_(u"URL del servei web"),
        required=False,
    )

    field2 = schema.TextLine(
        title=_(u"URL del servei web"),
        required=False,
    )

    field3 = schema.TextLine(
        title=_(u"URL del servei web"),
        required=False,
    )


class TfemarketSettingsEditForm(controlpanel.RegistryEditForm):

    schema = ITfemarketSettings
    label = _(u'Paràmetres de configuració de Genweb Mercat TFE')

    def updateFields(self):
        super(TfemarketSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(TfemarketSettingsEditForm, self).updateWidgets()

    def fix_password_fields(self, data):
        """
        Keep the stored value for the password fields not updated in the
        current request, i.e. those containing a None value.
        This method is needed since the password fields are not filled with
        their stored value when the edit form is loaded.
        """
        if not data['ws_key']:
            data['ws_key'] = self.getContent().ws_key

    @button.buttonAndHandler(_('Save'), name=None)
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.fix_password_fields(data)
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(
            _(u'Changes saved'), 'info')
        self.context.REQUEST.RESPONSE.redirect('@@rectorat-settings')

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(
            _(u'Edit cancelled'), 'info')
        self.request.response.redirect(
            '%s/%s' % (self.context.absolute_url(), self.control_panel_view))


class TfemarketSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = TfemarketSettingsEditForm
