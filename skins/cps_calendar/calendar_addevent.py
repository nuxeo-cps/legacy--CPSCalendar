##parameters=REQUEST=None, **kw
# $Id$

from random import randrange
locale = context.Localizer.default.get_selected_language()
ctool = context.portal_cpscalendar
if REQUEST is not None:
    kw.update(REQUEST.form)

event_type = kw.get('event_type')
cal_ids = kw.get('cal_ids', [])
attendees = [ctool.getAttendeeInfo(id, 1) for id in cal_ids]
kw['attendees'] = attendees

here = context.this()
id = str(int(DateTime())) + str(randrange(1000, 10000)) + ('-%s' % (here.id))

from_date_string = kw.get('from_date','')
from_date_hour = kw.get('from_date_hour')
from_date_minute = kw.get('from_date_minute')

to_date_string = kw.get('to_date','')
to_date_hour = kw.get('to_date_hour')
to_date_minute = kw.get('to_date_minute')

if event_type == 'event_allday':
    to_date_string += ' 23:59'
else:
    from_date_string += ' %s:%s' %(from_date_hour,from_date_minute)
    to_date_string += ' %s:%s' %(to_date_hour,to_date_minute)
from_date = ctool.stringToDateTime(from_date_string, locale)
to_date = ctool.stringToDateTime(to_date_string, locale)
kw['from_date'] = from_date
kw['to_date'] = to_date

# if we are called by a form request, we have to be sure that
# from_date < to_date.

if from_date <= to_date:
    event = here.invokeFactory('Event', id, **kw)

    if REQUEST is not None:
        REQUEST.SESSION['calendar_viewed'] = from_date
        REQUEST.SESSION['meeting'] = None
        REQUEST.RESPONSE.redirect('%s/%s' % (here.absolute_url(), id))
    else:
        return id
else:
    # The date entries are incorrect (from_date > to_date)
    # Return to the confirm screen, but with times flipped.
    kw['from_date'] = to_date
    kw['to_date'] = from_date
    kw['from_date_hour'] = to_date_hour
    kw['from_date_minute'] = to_date_minute
    kw['to_date_hour'] = from_date_hour
    kw['to_date_minute'] = from_date_minute
    return context.calendar_confirmaddevent_form(**kw)
