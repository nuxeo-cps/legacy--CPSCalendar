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

cal_users = meeting['cal_users']
cal_ids = cal_users.keys()

return {
  'from_date': from_date,
  'from_date_hour': from_date_hour,
  'from_date_minute': from_date_minute,
  'window': window,
  'duration_hour': duration_hour,
  'duration_minute': duration_minute,
  'duration': duration,
  'cal_users': cal_users,
  'cal_ids': cal_ids,
}
