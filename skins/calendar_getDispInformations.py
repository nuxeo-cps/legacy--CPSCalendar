##parameters=REQUEST

# determine current calendar view
# first from REQUEST.form then from SESSION then default to week view
disp = REQUEST.form.get('disp')
if disp is not None:
    REQUEST.SESSION['calendar_disp'] = disp
else:
    disp = REQUEST.SESSION.get('calendar_disp')
    if disp is None:
        disp = 'week'

if disp == 'week':
    current_action = 'week_view'
elif disp == 'day':
    current_action = 'day_view'
elif disp == 'month':
    current_action = 'month_view'

# determine current selected day
selected_day = REQUEST.form.get('selected_day')
if selected_day is not None:
    selected_day = DateTime(int(selected_day))
    REQUEST.SESSION['calendar_selected'] = selected_day
else:
    selected_day = REQUEST.SESSION.get('calendar_selected')
    if selected_day is None:
        selected_day = DateTime()

# determine current viewed day
viewed_day = REQUEST.form.get('viewed_day')
if viewed_day is not None:
    viewed_day = DateTime(int(viewed_day))
    REQUEST.SESSION['calendar_viewed'] = viewed_day
else:
    viewed_day = REQUEST.SESSION.get('calendar_viewed')
    if viewed_day is None:
        viewed_day = DateTime()


return {
    'disp': disp,
    'current_action': current_action,
    'selected_day': selected_day,
    'viewed_day': viewed_day,
}
