##parameters=all_day, REQUEST=None

if not all_day:
    context.edit(all_day=0, to_date=context.from_date+0.084)
else:
    context.edit(all_day=1)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect('%s/calendar_editevent_form' % (context.absolute_url(), ))
