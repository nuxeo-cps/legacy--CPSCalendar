##parameters=event_type, REQUEST=None

# This skin is no longer used, AFAIK. Keeping it for a while, just in case. /lennart

if event_type != 'event_allday':
    context.edit(event_type=event_type, to_date=context.from_date+0.084)
else:
    context.edit(event_type=event_type)

if REQUEST:
    REQUEST.RESPONSE.redirect('%s/calendar_editevent_form' % (context.absolute_url(), ))
