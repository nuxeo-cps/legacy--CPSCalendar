##parameters=create,event=None,REQUEST={}
# $Id$

# Fetches all "to" and "from" fields used for an event from
# the object, the request or defaults.
#
# Also makes sure everything is of the correct type

locale = context.Localizer.default.get_selected_language()

if REQUEST.has_key('from_date_string'):
    #OK, we have a REQUEST that comes from a form
    #Build valid dates from this form
    event_type = REQUEST['event_type']
    from_date_date = context.portal_cpscalendar.stringToDateTime(REQUEST['from_date_string'], locale)    
    if REQUEST.has_key('to_date_string'):
        to_date_date = context.portal_cpscalendar.stringToDateTime(REQUEST['to_date_string'], locale)    
    else:
        to_date_date = from_date_date

    from_date_year = from_date_date.year()
    from_date_month = from_date_date.month()
    from_date_day = from_date_date.day()
    to_date_year = to_date_date.year()
    to_date_month = to_date_date.month()
    to_date_day = to_date_date.day()
    
    #if event_type == 'event_allday':
    #    from_date_hour = 0
    #    from_date_minute = 0
    #    to_date_hour = 23
    #    to_date_minute = 45
    #else:
    from_date_hour = int(REQUEST['from_date_hour'])
    from_date_minute = int(REQUEST['from_date_minute'])
    to_date_hour = int(REQUEST['to_date_hour'])
    to_date_minute = int(REQUEST['to_date_minute'])
        
elif event and not create:
    # Get dates from the event
    from_date = event.from_date
    to_date = event.to_date
    
    from_date_year = from_date.year()
    from_date_month = from_date.month()
    from_date_day = from_date.day()
    from_date_hour = from_date.hour()
    from_date_minute = from_date.minute()
    from_date_date = DateTime(from_date_year, from_date_month, from_date_day)

    to_date_year = to_date.year()
    to_date_month = to_date.month()
    to_date_day = to_date.day()
    to_date_hour = to_date.hour()
    to_date_minute = to_date.minute()
    to_date_date = DateTime(to_date_year, to_date_month, to_date_day)
    
else:
    # No form, no event. This is created by clicking on a add event link.
    if REQUEST.has_key('from_date'):
        from_date = DateTime(int(REQUEST['from_date']))
        from_date_hour = from_date.hour()
        from_date_minute = from_date.minute()
    elif REQUEST.has_key('selected_day'):
        from_date = DateTime(int(REQUEST['selected_day']))
        from_date_hour = DateTime().hour()
        from_date_minute = DateTime().minute() + 30
    else:
        from_date = DateTime() 
        from_date_hour = DateTime().hour()
        from_date_minute = DateTime().minute() + 30

    #if same_type(from_date, 'string'):
    #    from_date = context.portal_cpscalendar.stringToDateTime(from_date)
    #elif not same_type(from_date, DateTime()):
    #    # Should be an int or something else that is convertable
    #    from_date = DateTime(from_date)

    from_date_year = from_date.year()
    from_date_month = from_date.month()
    from_date_day = from_date.day()
    from_date_date = DateTime(from_date_year, from_date_month, from_date_day)

    to_date_year = from_date_year
    to_date_month = from_date_month
    to_date_day = from_date_day
    to_date_hour = from_date_hour + 1
    to_date_minute = from_date_minute
    to_date_date = from_date_date

# Round minutes to nearest quarter
from_date_minute = ((from_date_minute)/15)*15;
if from_date_minute ==60:
    from_date_minute =0
to_date_minute = ((from_date_minute)/15)*15;
if to_date_minute ==60:
    to_date_minute =0

return ({'from_date_year': from_date_year,
         'from_date_month': from_date_month,
         'from_date_day': from_date_day,
         'from_date_hour': from_date_hour,
         'from_date_minute': from_date_minute,
         'from_date_date': from_date_date},
        {'to_date_year': to_date_year,
         'to_date_month': to_date_month,
         'to_date_day': to_date_day,
         'to_date_hour': to_date_hour,
         'to_date_minute': to_date_minute,
         'to_date_date': to_date_date},
        )
