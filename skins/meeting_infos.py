##parameters=request

meeting = request.SESSION['meeting']
args = meeting['args']

time = int(request.form['time'])
from_date = DateTime(time)

from_date_hour = from_date.hour()
from_date_minute = from_date.minute()

window = int(request.form['window'])

duration_hour = args['duration_hour']
duration_minute = args['duration_minute']
duration = duration_hour * 60 + duration_minute

interval = 15*60

from_oks = []
for i in range(0, window - duration + 15, 15):
    from_oks.append({
        'hour': from_date_hour,
        'minute': from_date_minute or '00',
        'time': time,
    })
    time += interval
    from_date_minute += 15
    if from_date_minute > 59:
        from_date_minute -= 60
        from_date_hour += 1

cal_users = meeting['freebusy_infos']['cal_users']
cal_ids = meeting['display_ids']

return {
  'from_date': from_date,
  'duration_hour': duration_hour,
  'duration_minute': duration_minute,
  'duration': duration,
  'from_oks': from_oks,
  'cal_users': cal_users,
  'cal_ids': cal_ids,
}
