##parameters

here = context.this()

mcat = context.Localizer.cpscalendar
all_calendars = here.objectIds('Calendar')
mtool = context.portal_membership

calendars = { 'private': [], 'others': [], 'rooms': [], 'ressources': [],
    'events_shows': [] }
isAnon = mtool.isAnonymousUser()
user_id = mtool.getAuthenticatedMember().getUserName()
has_private = 0

for calid in all_calendars:
    ok = 0
    ok_pend = 0
    type = 'ressources'
    try:
        cal = getattr(here, calid)
        if mtool.checkPermission('View', cal):
            ok = 1
        if mtool.checkPermission('Add portal content', cal):
            ok_pend = 1
    except:
        # Unauthorized
        continue
    if not ok:
        continue
    if calid == user_id:
        type = 'private'
        has_private = 1
    elif cal.usertype == 'member':
        type = 'others'
    elif cal.usertype == 'room':
        type = 'rooms'
    elif cal.usertype == 'events_show':
        type = 'events_shows'
    else:
        type = 'ressources'
    calendars[type].append({
        'id': calid,
        'title': cal.title_or_id(),
        'url': cal.absolute_url(),
        'pending': ok_pend and cal.getPendingEventsCount(),
    })

if not has_private and not isAnon:
    calendars['private'].append({
        'id': user_id,
        'title': 'Calendar of %s' % (user_id, ),
        'url': '%s/%s' % (here.absolute_url(), user_id),
        'pending': 0,
    })

return calendars
