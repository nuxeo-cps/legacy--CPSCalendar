##parameters=event_dict, calendar_url, calendar_title, event_title, mail_from, mails, new_event

mcat = context.portal_messages
request = event_dict['request']
confirm_url = '%s/calendar_pending_events?event_id=%s' % (calendar_url, event_dict['id'])

calendar_title = mcat(calendar_title)
event_title = mcat(event_title)

header = """\
From: %s
To: %s
Subject: [CAL] %s
Content-Type: text/plain; charset=ISO-8859-15
Mime-Version: 1.0
""" % (mail_from, ', '.join(mails), event_title)

if request == 'request':
    if new_event:
        message = """
%(calendar_title)s received a request for event "%(event_title)s".
"""
    else:
        message = """
%(calendar_title)s received an update for event "%(event_title)s".
"""
    message = message % {
        'calendar_title': calendar_title,
        'event_title': event_title,
    }
    comment = event_dict['event']['comment'].strip()
    if comment:
        message += """
Comment:
%(comment)s""" % {'comment': comment}
elif request == 'status':
    attendees = event_dict['change']
    message = """
Calendar for %(calendar_title)s received a status update for event "%(event_title)s":""" % {
        'calendar_title': calendar_title,
        'event_title': event_title,
    }
    for att in attendees:
        message += ("\n  - %s (%s)" % (att.get('cn', att['attendee']), att['status']))
        comment = att['comment'].strip()
        if comment:
            message += """
Comment:
%(comment)s""" % {'comment': comment}

message += """
Please confirm/commit by using this URL:
%s""" % (confirm_url, )

return header+message
