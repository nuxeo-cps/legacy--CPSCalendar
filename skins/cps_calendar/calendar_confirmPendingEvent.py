##parameters=event_id, comment, status, REQUEST=None

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
    event = getattr(context, event_id)
    event.setMyStatus(status, comment=comment)
    if delete:
        context.manage_delObjects([event_id])
        url = context.absolute_url()
    else:
        url = event.absolute_url()

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(url)
