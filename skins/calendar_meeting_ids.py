##parameters=cal_ids=[], REQUEST=None

if not cal_ids:
    return context.calendar_meeting_empty()

meeting = REQUEST.SESSION['meeting']
meeting['display_ids'] = cal_ids
freebusy_infos = meeting['freebusy_infos']
cals_dict = freebusy_infos['cals_dict']
mask_cal = freebusy_infos['mask_cal']
cals = [cals_dict[id] for id in cal_ids]
busy_infos = context.unionCals(
  *(cals + [mask_cal]),
  **{'with_free': 1}
)
meeting['busy_infos'] = busy_infos

REQUEST.SESSION['meeting'] = meeting

REQUEST.RESPONSE.redirect('%s/calendar_freebusy' % (context.absolute_url(), ))
