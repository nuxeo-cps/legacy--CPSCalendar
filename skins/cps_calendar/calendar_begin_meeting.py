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

from_date_string = kw.get('from_date_string')
from_date = caltool.stringToDateTime(from_date_string, locale)
from_date_day = from_date.day()
from_date_month = from_date.month()
from_date_year = from_date.year()
from_date_hour = kw.get('from_date_hour','')
from_date_minute = kw.get('from_date_minute','')
to_date_string = kw.get('to_date_string')
to_date = caltool.stringToDateTime(to_date_string, locale)
to_date_day = to_date.day()
to_date_month = to_date.month()
to_date_year = to_date.year()
to_date_hour = kw.get('to_date_hour','')
to_date_minute = kw.get('to_date_minute','')

if from_date > to_date:
    from_date, to_date = to_date, from_date

if not errors:
    days = from_date - to_date
    if abs(days) > 32:
        pr('cpscalendar_interval_month')

if errors:
    return context.calendar_meeting_error(errors=errors)

meeting = caltool.getFreeBusy(cal_ids, from_date, to_date, from_date_hour, from_date_minute,
    to_date_hour, to_date_minute)
meeting['args'] = kw
REQUEST.SESSION['freebusy_start'] = 0

if REQUEST is not None:
    REQUEST.SESSION['meeting'] = meeting
    REQUEST.RESPONSE.redirect('%s/calendar_freebusy' % context.absolute_url())

