##parameters=ids=None, id=None, REQUEST=None

if ids is None:
    ids = []

if id is not None:
    ids.append(id)

attendees = context.attendees

attendees_ids = [att['id'] for att in attendees]

add_ids = [id for id in ids if id not in attendees_ids]

try:
    new_attendees = [context.getAttendeeInfo(id, 1) for id in add_ids]
except AttributeError:
    new_attendees = []


if new_attendees:
    attendees = list(attendees)
    attendees.extend(new_attendees)

    context.setAttendees(attendees)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect('%s/calendar_attendees_form' % (context.absolute_url(), ))
