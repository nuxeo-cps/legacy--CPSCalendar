##parameters=ids=None, id=None, REQUEST=None

# $Id$

rpaths = ids

if rpaths is None:
    rpaths = []

if id is not None:
    rpaths.append(id)

caltool = context.portal_cpscalendar

attendees = context.attendees
attendees_rpaths = [att['rpath'] for att in attendees]

add_rpaths = [rpath for rpath in rpaths if rpath not in attendees_rpaths]

try:
    new_attendees = [caltool.getAttendeeInfo(rpath, 1) for rpath in add_rpaths]
except AttributeError:
    new_attendees = []

if new_attendees:
    attendees = list(attendees)
    attendees.extend(new_attendees)
    context.setAttendees(attendees)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(
        '%s/calendar_attendees_form' % context.absolute_url())
