##parameters=REQUEST=None, **kw

from random import randrange
locale = context.Localizer.default.get_selected_language()

if REQUEST is not None:
    kw.update(REQUEST.form)

here = context.this()
id = str(int(DateTime()))+str(randrange(1000,10000))+('-%s' % (here.id))

all_day = kw.get('all_day')
from_date_day = kw.get('from_date_day')

from_date_string = kw.get('from_date','')
if locale in ('en', 'hu', ):
    from_date_month, from_date_day, from_date_year = from_date_string.split('/')
else:
    from_date_day, from_date_month, from_date_year = from_date_string.split('/')

# we are creating an event from a form
from_date_day = int(from_date_day)
from_date_month = int(from_date_month)
from_date_year = int(from_date_year)
from_date_hour = int(kw.get('from_date_hour'))
from_date_minute = int(kw.get('from_date_minute'))
from_date = DateTime(from_date_year, from_date_month, from_date_day,
                     from_date_hour, from_date_minute)
kw['from_date'] = from_date

to_date_string = kw.get('to_date','')
if locale in ('en', 'hu', ):
    to_date_month, to_date_day, to_date_year = to_date_string.split('/')
else:
    to_date_day, to_date_month, to_date_year = to_date_string.split('/')

to_date_day = int(to_date_day)
to_date_month = int(to_date_month)
to_date_year = int(to_date_year)
to_date_hour = int(kw.get('to_date_hour'))
to_date_minute = int(kw.get('to_date_minute'))

if not all_day and to_date_hour and to_date_minute:
    # end of event is midnight so automatically sets end date
    # to next day midnight
    to_date = DateTime(to_date_year, to_date_month, to_date_day) + 1
    to_date_year = to_date.year()
    to_date_month = to_date.month()
    to_date_day = to_date.day()
    
to_date = DateTime(to_date_year, to_date_month, to_date_day,
                   to_date_hour, to_date_minute)
kw['to_date'] = to_date

# if we are called by a form request, we have to be sure that
# from_date < to_date. For an all_day event, from_date and to_date
# will be switched

if all_day or from_date <= to_date:
    # TODO: add repeated event add manage
    here.invokeFactory('Event', id, **kw)

    if REQUEST is not None:
        REQUEST.SESSION['calendar_viewed'] = from_date
        REQUEST.RESPONSE.redirect('%s/%s' % (here.absolute_url(), id))
    else:
        return id
else:
    # the date entries are incorrect (from_date > to_date).
    # in a not all_day event, so propose to extend the event
    # to the next day
    to_date = DateTime(to_date_year, to_date_month, to_date_day) + 1
    to_date_year = to_date.year()
    to_date_month = to_date.month()
    to_date_day = to_date.day()
    to_date = DateTime(to_date_year, to_date_month, to_date_day,
        to_date_hour, to_date_minute)
    kw['to_date'] = to_date
    return context.calendar_confirmaddevent_form(**kw)
