##parameters=ids=None, REQUEST=None

attendees = context.attendees

if ids is not None:
    context.removeAttendees(ids)

if REQUEST:
    REQUEST.RESPONSE.redirect('%s/calendar_attendees_form' % (context.absolute_url(), ))
