##parameters=ids, comment=None, notify=[], REQUEST=None

event_ids = context.objectIds('Event')
if comment is not None:
    notify = [id for id in notify if id in event_ids]
    events = [getattr(context, id) for id in notify]
    for event in events:
        event.setEventStatus('cancelled')
        event.updateAttendeesCalendars(comment=comment)
    context.manage_delObjects(ids)
else:
    events = [getattr(context, id) for id in ids if id in event_ids]

    noconfirm_ids = [event.id for event in events if (not event.attendees) or
        (not event.canEditThisEvent()) or
        (event.event_status == 'cancelled' and not event.isdirty)]
    confirm_events = [event for event in events if event.id not in noconfirm_ids]

    context.manage_delObjects(noconfirm_ids)

    if confirm_events:
        return context.calendar_confirmdelevents(events=confirm_events)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(context.absolute_url())
