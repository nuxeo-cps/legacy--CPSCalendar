##parameters=REQUEST=None, **kw

locale = context.Localizer.default.get_selected_language()

if REQUEST is not None:
    kw.update(REQUEST.form)

here = context.this()

all_day = kw.get('all_day', 0)

from_date_string = kw.get('from_date','')
if locale in ('en', 'hu', ):
    from_date_month, from_date_day, from_date_year = from_date_string.split('/')
else:
    from_date_day, from_date_month, from_date_year = from_date_string.split('/')

from_date_day = int(from_date_day)
from_date_month = int(from_date_month)
from_date_year = int(from_date_year)
from_date_hour = int(kw.get('from_date_hour'))
from_date_minute = int(kw.get('from_date_minute'))

from_date = DateTime(from_date_year, from_date_month, from_date_day,
                     from_date_hour, from_date_minute)
kw['from_date'] = from_date
del kw['from_date_hour']
del kw['from_date_minute']

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

# This code seems supposed to change a not all_day event in an all_day
# event in the case of its from_date being the same as its to_date.
# But since the comparison is only made on the year, month and day, it
# changes every not all_day events. This is a bug.
# This code will stay commented out until it proves really useless or
# until it gets improved.
# 
## if not all_day:
##     if (from_date_day == int(kw.get('to_date_day'))
##         and from_date_month == int(kw.get('to_date_month'))
##         and from_date_year == int(kw.get('to_date_year'))):

##         all_day = 1
##         kw['all_day'] = all_day

##         to_date_day = from_date_day
##         to_date_month = from_date_month
##         to_date_year = from_date_year

if not all_day and (from_date > to_date):
    to_date = DateTime(from_date_year, from_date_month, from_date_day) + 1
    to_date_day = to_date.day()
    to_date_month = to_date.month()
    to_date_year = to_date.year()

to_date = DateTime(to_date_year, to_date_month, to_date_day,
                   to_date_hour, to_date_minute)
kw['to_date'] = to_date
del kw['to_date_hour']
del kw['to_date_minute']

here.edit(**kw)

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(here.absolute_url())

