##parameters=cal_ids=[], REQUEST=None

try:
    meeting = REQUEST.SESSION['meeting']
except KeyError:
    return context.calendar_meeting_expired()

if not cal_ids:
    return context.calendar_meeting_empty()

meeting['display_ids'] = cal_ids

meeting['busy_infos']  = context.listFreeSlots(
    with_free=1, *(cals + [mask_cal]))

meeting = caltool.getFreeBusy(cal_ids, from_date, to_date, from_date_hour, from_date_minute,
    to_date_hour, to_date_minute)
        
if REQUEST is not None:
    REQUEST.SESSION['meeting'] = meeting
    REQUEST.RESPONSE.redirect(
        '%s/calendar_freebusy' % (context.absolute_url(), ))

