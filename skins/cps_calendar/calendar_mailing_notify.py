##parameters=event_dict, calendar_url, calendar_title, event_title, new_event

mcat = context.Localizer.cpscalendar
request = event_dict['request']
confirm_url = '%s/calendar_pending_events?event_id=%s' % (calendar_url, event_dict['id'])

# Personal calendars have a tendency to have titles ending in the ordinal 160.
# That doesn't work.
if ord(calendar_title[-1]) == 160:
    calendar_title = calendar_title[:-1]
else:
    calendar_title = mcat(calendar_title.strip())
event_title = mcat(event_title)

header = """\
Content-Type: text/plain; charset=ISO-8859-15
Mime-Version: 1.0

"""

if request == 'request':
    if new_event:
        message = mcat('cpscalendar_mailnotify_request').encode("ISO-8859-15", 'ignore')
    else:
        message = mcat('cpscalendar_mailnotify_update').encode("ISO-8859-15", 'ignore')

    message = message % {
        'calendar_title': calendar_title,
        'event_title': event_title,
    }
    comment = event_dict['event']['comment'].strip()
    if comment:
        message += '\n' + mcat('cpscalendar_mailnotify_comment').encode("ISO-8859-15", 'ignore') + '\n' + comment

elif request == 'status':
    attendees = event_dict['change']
    message = mcat('cpscalendar_mailnotify_status_update').encode("ISO-8859-15", 'ignore')
    message = message % {
        'calendar_title': calendar_title,
        'event_title': event_title,
    }
    for att in attendees:
        message += ("\n  - %s (%s)" % (att.get('cn', att['attendee']), att['status']))
        comment = att['comment'].strip()
        if comment:
            message += '\n' + mcat('cpscalendar_mailnotify_comment').encode("ISO-8859-15", 'ignore') + '\n' + comment

message += '\n' + mcat('cpscalendar_mailnotify_confirm_here').encode("ISO-8859-15", 'ignore') + '\n' + confirm_url

return header+str(message)
