##parameters=REQUEST=None, **kw
# $Id$

from random import randrange
locale = context.Localizer.default.get_selected_language()

if REQUEST is not None:
    kw.update(REQUEST.form)

here = context.this()
id = str(int(DateTime())) + str(randrange(1000, 10000)) + ('-%s' % (here.id))

event_type = kw.get('event_type')
from_date_string = kw.get('from_date','')
to_date_string = kw.get('to_date','')
if locale in ('en', 'hu', ):
    from_date_month, from_date_day, from_date_year = from_date_string.split('/')
    to_date_month, to_date_day, to_date_year = to_date_string.split('/')
else:
    from_date_day, from_date_month, from_date_year = from_date_string.split('/')
    to_date_day, to_date_month, to_date_year = to_date_string.split('/')

# we are creating an event from a form
from_date_day = int(from_date_day)
from_date_month = int(from_date_month)
from_date_year = int(from_date_year)
from_date_hour = int(kw.get('from_date_hour'))
from_date_minute = int(kw.get('from_date_minute'))
to_date_day = int(to_date_day)
to_date_month = int(to_date_month)
to_date_year = int(to_date_year)
to_date_hour = int(kw.get('to_date_hour'))
to_date_minute = int(kw.get('to_date_minute'))

if event_type == 'event_allday':
    from_date = DateTime(from_date_year, from_date_month, from_date_day, 0, 0)
    to_date = DateTime(to_date_year, to_date_month, to_date_day, 23, 59)
else:
    from_date = DateTime(from_date_year, from_date_month, from_date_day,
                        from_date_hour, from_date_minute)
    to_date = DateTime(from_date_year, from_date_month, from_date_day,
                        to_date_hour, to_date_minute)

kw['from_date'] = from_date
kw['to_date'] = to_date

# if we are called by a form request, we have to be sure that
# from_date < to_date.

if from_date <= to_date:
    here.invokeFactory('Event', id, **kw)

    if REQUEST is not None:
        REQUEST.SESSION['calendar_viewed'] = from_date
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
