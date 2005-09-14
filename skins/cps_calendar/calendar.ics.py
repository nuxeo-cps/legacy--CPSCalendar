##parameters=redirect=0, REQUEST=None

#mcat = context.Localizer.cpscalendar
def mcat(s):
    return context.translation_service.translate('cpscalendar', s)

if not int(redirect):
    if REQUEST:
        REQUEST = context.REQUEST

    mtool = context.portal_membership
    if not mtool.checkPermission('View', context):
        # Not authorized but we don't want to raise this error
        # since CMF will redirect it to the login form
        # and we want basic HTTP auth here
        RESPONSE = REQUEST.RESPONSE
        realm = RESPONSE.realm
        RESPONSE.setStatus(401)
        RESPONSE.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)
        RESPONSE.setBody("""<html>
<head><title>Unauthorized</title></head>
<body>
You are not authorized to access this ressource
</body>
</html>""")
        return

ical_conv = '%Y%m%dT%H%M%S'
ical_date_conv = '%Y%m%d'

def icalvalue(s):
    return unicode('\\,'.join(s.split(',')), 'latin1').encode('UTF-8')

def attendee2ical(attendee):
    if same_type(attendee, 'lkj'):
        raise "lhlj", str(attendee)

    cutype = attendee.get('usertype', 'member').upper()
    if  cutype == 'MEMBER': 
        cid = attendee['id']
        mail = event.getMemberEmail(cid)
        message = '' # People is the default CUTYPE (INDIVIDUAL).
    else:
        if cutype not in ('GROUP', 'RESOURCE', 'ROOM'):
            # Mostly to handle the special "Workspace" type.
            cutype = 'X-' + cutype
        message = 'CUTYPE=%s;' % cutype
        cid = attendee['rpath']
        mail = 'nomail@nohost.no'

    status = attendee.get('status')
    if status == 'unconfirmed':
        status = 'NEEDS-ACTION'
    elif status == 'confirmed':
        status = 'ACCEPTED'
    elif status == 'tentative':
        status = 'TENTATIVE'
    elif status == 'decline':
        status = 'DECLINED'
    else:
        status = None
    if status is not None:
        message += 'PARTSTAT=%s;' % status
        
    # iCalendar identifies calendars by email adress, which is nonsensical.
    # We therefore add X-CID (Calendar ID) which contains the id, so that
    # we at least understand what we are talking about.
    message += 'X-CID=%s:MAILTO:%s\n' % (cid, mail)
    
    return message


header = """BEGIN:VCALENDAR
CALSCALE:GREGORIAN
X-WR-TIMEZONE;VALUE=TEXT:Europe/Paris
PRODID:-//Nuxeo//CPSCalendar 0.1//EN
X-WR-CALNAME;VALUE=TEXT:%s
X-WR-RELCALID;VALUE=TEXT:%s
VERSION:2.0
""" % (icalvalue(mcat(context.title_or_id())), context.absolute_url())

footer = """\
END:VCALENDAR
"""

message = header

events = context.objectValues('Event')
dtstamp = DateTime('UTC')
timezone = dtstamp.localZone()

event_header = """\
BEGIN:VEVENT
DTSTAMP:%s
""" % (dtstamp.strftime(ical_conv), )

event_footer = """\
END:VEVENT
"""

for event in events:
    eventfrom = event.from_date.toZone('UTC').strftime(ical_conv)
    eventto = event.to_date.toZone('UTC').strftime(ical_conv)
    
    message += event_header

    message += 'SUMMARY:%s\n' % icalvalue(mcat(event.title_or_id()))
    message += 'UID:%s\n' % event.getId()
    message += 'DESCRIPTION:%s\n' % event.description
    if event.location:
        message += 'LOCATION:%s\n'% icalvalue(event.location)
    if event.document:
        message += 'ATTACH:%s\n'% icalvalue(event.document)
    # The missspelling 'canceled' is used for cancelled status...
    message += 'STATUS:%s\n' % ('canceled' and 'CANCELLED' or status.upper())
    # This defaults to OPAQUE, so we only include it when not:
    if event.transparent:
        message += 'TRANSP:TRANSPARENT\n'
    # This defaults to PUBLIC
    if event.category == 'private':
        message += 'CLASS:PRIVATE\n'
        
    if event.event_type == 'event_allday':
        message += 'DTSTART;VALUE=DATE:%s\n' % event.from_date.strftime(ical_date_conv)
        message += 'DTEND;VALUE=DATE:%s\n' % (event.to_date+1).strftime(ical_date_conv)
    else:
        message += 'DTSTART:%s\n' % eventfrom
        message += 'DTEND:%s\n' % eventto

    # Organizer (Yes, it should be a semicolon):
    if event.organizer:
        message += 'ORGANIZER;' + attendee2ical(event.organizer)
    
    for each in event.attendees:
        message += 'ATTENDEE;' + attendee2ical(each)

    if event.event_type == 'event_recurring':
        message += 'RRULE:FREQ='
        if event.recurrence_period == 'period_daily':
            message += 'DAILY'
        elif event.recurrence_period == 'period_weekly':
            message += 'WEEKLY'
        elif event.recurrence_period == 'period_monthly':
            message += 'MONTHLY'
        elif event.recurrence_period == 'period_quarterly':
            message += 'MONTHLY;INTERVAL=3'
        elif event.recurrence_period == 'period_yearly':
            message += 'YEARLY'
        else:
            raise 'Unknown recurrance period', event.recurrence_period
        message += '\n'
    message += event_footer

message += footer

#OK, it seems to have worked fine. Set the content type and return
if REQUEST is not None:
    REQUEST.RESPONSE.setHeader('Content-Type', 'text/calendar')

return message
