##parameters=comment=None, notify=None, REQUEST=None

event = context

if comment is not None:
    calendar = event.getCalendar()
    if notify == 'decline':
        event.setMyStatus('decline', comment)
    elif notify == 'cancel':
        event.setEventStatus('cancelled')
        event.updateAttendeesCalendars(comment=comment)
    calendar.manage_delObjects([event.id])
else:
    noconfirm_cancel = (not event.attendees) or \
        (not event.canEditThisEvent()) or \
        (event.event_status == 'cancelled' and not event.isdirty) or \
        (not [att for att in event.attendees if att['status'] != 'decline'])
    confirm_decline = (not event.canEditThisEvent()) and \
        event.getMyStatus() != 'decline' and \
        event.event_status != 'cancelled'
    if confirm_decline:
        return event.calendar_confirmdelevent(notify='decline')
    if not noconfirm_cancel:
        return event.calendar_confirmdelevent(notify='cancel')
    calendar = event.getCalendar()
    calendar.manage_delObjects([event.id])

if REQUEST:
    REQUEST.RESPONSE.redirect(calendar.absolute_url())
