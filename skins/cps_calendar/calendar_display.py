##parameters=cal_ids=[], REQUEST=None

context.setAdditionalCalendars(cal_ids)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(context.absolute_url())
