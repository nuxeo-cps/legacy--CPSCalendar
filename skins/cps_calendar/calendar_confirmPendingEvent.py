##parameters=event_id, comment, status, REQUEST=None

# $Id$

if status == 'decline_and_delete':
    delete = 1
    status = 'decline'
else:
    delete = 0

if status == 'ignore':
    context.cleanPendingEvents(event_id)
    url = context.absolute_url()
else:
    context.confirmPendingEvent(event_id)
    event = getattr(context, event_id, None)
    if event is not None:
        event.setMyStatus(status, comment=comment)
    if delete:
        context.manage_delObjects([event_id])

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(context.absolute_url()+'/calendar_pending_events')
