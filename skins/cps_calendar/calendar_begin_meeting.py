##parameters=cal_ids=[], REQUEST=None, **kw

# $Id$

from zLOG import LOG

caltool = context.portal_cpscalendar
errors = []
locale = context.Localizer.default.get_selected_language()

pr = errors.append

if REQUEST:
    kw.update(REQUEST.form)

if not cal_ids:
    return context.calendar_meeting_empty()

from_date_string = kw.get('from_date','')

if locale in ('en', 'hu', ):
    from_date_month, from_date_day, from_date_year = from_date_string.split('/')
else:
    from_date_day, from_date_month, from_date_year = from_date_string.split('/')

from_date_day = int(from_date_day)
from_date_month = int(from_date_month)
from_date_year = int(from_date_year)
from_date = DateTime(from_date_year, from_date_month, from_date_day)

to_date_string = kw.get('to_date','')
if locale in ('en', 'hu', ):
    to_date_month, to_date_day, to_date_year = to_date_string.split('/')
else:
    to_date_day, to_date_month, to_date_year = to_date_string.split('/')

to_date_day = int(to_date_day)
to_date_month = int(to_date_month)
to_date_year = int(to_date_year)
to_date = DateTime(to_date_year, to_date_month, to_date_day)

if not errors:
    days = from_date - to_date
    if abs(days) > 32:
        pr('cpscalendar_interval_month')

if errors:
    return context.calendar_meeting_error(errors=errors)

from_date_hour = int(kw['from_date_hour'])
from_date_minute = int(kw['from_date_minute'])
to_date_hour = int(kw['to_date_hour'])
to_date_minute = int(kw['to_date_minute'])


meeting = caltool.getFreeBusy(cal_ids, from_date, to_date, from_date_hour, from_date_minute,
    to_date_hour, to_date_minute)
meeting['args'] = kw
REQUEST.SESSION['freebusy_start'] = 0

if REQUEST is not None:
    REQUEST.SESSION['meeting'] = meeting
    REQUEST.RESPONSE.redirect('%s/calendar_freebusy' % context.absolute_url())

