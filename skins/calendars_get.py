##parameters

here = context.this()

all_calendars = here.objectIds()
mtool = context.portal_membership
mcat = context.portal_messages

calendars = { 'private': [], 'others': [], 'rooms': [], 'ressources': [] }
isAnon = mtool.isAnonymousUser()
user_id = mtool.getAuthenticatedMember().getUserName()
has_private = 0

for calid in all_calendars:
    ok = 0
    type = 'ressources'
    try:
        cal = getattr(here, calid)
        if mtool.checkPermission('View', cal):
            ok = 1
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
    else:
        type = 'ressources'
    calendars[type].append({
        'id': calid,
        'title': mcat(cal.title_or_id()),
        'url': cal.absolute_url(),
    })

if not has_private and not isAnon:
    calendars['private'].append({
        'id': user_id,
        'title': 'Calendar of %s' % (user_id, ),
        'url': '%s/%s' % (here.absolute_url(), user_id),
    })

return calendars
