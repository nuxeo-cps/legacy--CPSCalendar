##parameters=REQUEST=None, **kw
# $Id$

locale = context.Localizer.default.get_selected_language()
ctool = context.portal_cpscalendar

if REQUEST:
    kw.update(REQUEST.form)

here = context.this()

event_type = kw.get('event_type')

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
del kw['from_date_hour']
del kw['from_date_minute']
del kw['to_date_hour']
del kw['to_date_minute']

here.edit(**kw)

if REQUEST:
    REQUEST.RESPONSE.redirect(here.absolute_url())

