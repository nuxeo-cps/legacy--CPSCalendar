##parameters=datetime

s = datetime.strftime('%d,%m,%Y,%H,%M')

(day, month, year, hour, minute) = s.split(',')

return {
  'day': int(day),
  'month': int(month),
  'year': int(year),
  'hour': int(hour),
  'minute': int(minute),
}
