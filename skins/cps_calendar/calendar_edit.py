##parameters=REQUEST=None, **kw
# $Id$

locale = context.translation_service.getSelectedLanguage()
ctool = context.portal_cpscalendar

if REQUEST:
    kw.update(REQUEST.form)

here = context.this()
here.manage_changeProperties(**kw)

if REQUEST:
    REQUEST.RESPONSE.redirect( here.absolute_url() + \
       '/calendar_edit_form?portal_status_message=psm_content_changed')

