##parameters=ids, REQUEST=None

attendees = context.attendees

context.removeAttendees(ids)

if REQUEST:
    REQUEST.RESPONSE.redirect('%s/calendar_attendees_form' % (context.absolute_url(), ))
