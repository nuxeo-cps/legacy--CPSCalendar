##parameters=cal_ids=[], REQUEST=None

context.setAdditionalCalendars(cal_ids)

if REQUEST:
    REQUEST.RESPONSE.redirect(context.absolute_url())
