##parameters=cal_ids=[], REQUEST=None

try:
    meeting = REQUEST.SESSION['meeting']
except KeyError:
    return context.calendar_meeting_expired()

if not cal_ids:
    return context.calendar_meeting_empty()

meeting['display_ids'] = cal_ids
freebusy_infos = meeting['freebusy_infos']
cals_dict = freebusy_infos['cals_dict']
mask_cal = freebusy_infos['mask_cal']
cals = [cals_dict[id] for id in cal_ids]

meeting['busy_infos']  = context.listFreeSlots(
    with_free=1, *(cals + [mask_cal]))

if REQUEST is not None:
    REQUEST.SESSION['meeting'] = meeting
    REQUEST.RESPONSE.redirect(
        '%s/calendar_freebusy' % (context.absolute_url(), ))

