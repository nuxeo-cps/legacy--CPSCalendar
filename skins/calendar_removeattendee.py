##parameters=ids, REQUEST=None

attendees = context.attendees

attendees = [att for att in attendees if att['id'] not in ids]

context.setAttendees(attendees)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect('%s/calendar_attendees_form' % (context.absolute_url(), ))
