##parameters=date=None,input_id=None,date_disp_id=None,other_input=None

mcat = context.Localizer.cpscalendar
base_url = 'day_selector?input_id=%s&date_disp_id=%s&other_input=%s&date:int='\
    % (input_id, date_disp_id, other_input)

date = DateTime(date)
year = date.year()
month = date.month()
curr_date = DateTime(year, month, 1)
next_date = curr_date + 32
prev_date = curr_date - 1
prev_url = base_url + str(int(prev_date))
next_url = base_url + str(int(next_date))
base_disp = mcat('_cal_Month%s' % (month, )) + ' ' + str(year)
base_js = "javascript:select_day('%%s', '%(month)s', '%(year)s', '%%s %(base_disp)s')" % {'month': month, 'year': year, 'base_disp': base_disp}
dow = curr_date.dow()
lines = []
days_in_month = (month in [1, 3, 5, 7, 8, 10, 12] and 31) or \
    (month in [4, 6, 9, 11] and 30) or \
    (curr_date.isLeapYear() and 29 or 28)
if dow == 0: dow = 7
current_line = [None]*(dow-1)
lines = [current_line]
for day in range(1, days_in_month+1):
    if dow == 8:
        dow = 1
        current_line = []
        lines.append(current_line)
    day_str = mcat('_cal_Day_long%s' % (dow%7, )) + ' ' + str(day)
    js = base_js % (day, day_str)
    current_line.append({
      'js': js,
      'day': day,
    })
    dow += 1

return {
  'prev_url': prev_url,
  'next_url': next_url,
  'base_disp': base_disp,
  'lines': lines,
}
