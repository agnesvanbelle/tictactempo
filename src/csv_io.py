import utils
import io
import csv


class WorkLog(object):
  def __init__(self, issue_id, time_amount, comment):
    self.issue_id = issue_id
    self.time_amount = time_amount
    self.comment = comment  
  
class AbsoluteWorkLog(WorkLog):
  def __init__(self, issue_id, time_hours, date_string_human_readable_format, comment):
    super().__init__(issue_id, utils.hours_to_seconds(time_hours), comment)
    self.has_date = True
    self.date_string = utils.datetime_to_date_string(utils.human_readable_form_to_datetime(date_string_human_readable_format))

  def is_absolute(self):
    return True
  
  def __repr__(self):
    return "issue: {:s} amount: {:1.4f}h comment: \"{:s}\" date:{:s}".format(self.issue_id, utils.seconds_to_hours(self.time_amount), self.comment, 
                                                                 self.date_string if self.has_date else "")
    
class RelativeWorkLog(WorkLog):
  def __init__(self, issue_id, time_amount, comment):
    super().__init__(issue_id, time_amount, comment)
    self.has_date =  False
    
  def is_absolute(self):
    return False
  
  def __repr__(self):
    return "issue: {:s} amount: {:1.2f} comment: {:s}".format(self.issue_id, self.time_amount, self.comment)
  
class TimeRow(object):
  separator = ","
  enter_keyword = "<enter>"
  relative_day_keyword = "(ignored)" #TODO change to: not specified
  
  def __init__(self, day, issue_id, descr, amount, amount_is_in_hours, comment):
    '''
    day should be a string like: yyyy-mm-dd 
    '''
    self.day_as_string = day
    if (self.day_as_string != None):
      self.day_as_datetime = utils.date_string_to_datetime(day)
      self.day_as_human_readable_form = utils.datetime_to_human_readable_form(self.day_as_datetime)
    
    self.issue_id = issue_id
    self.descr = descr
    self.amount = amount
    self.amount_is_in_hours = amount_is_in_hours
    self.comment = comment
  
  @staticmethod
  def to_csv_row(col_values):
    output = io.StringIO()
    my_writer = csv.writer(output, delimiter = TimeRow.separator, quotechar='"', quoting=csv.QUOTE_MINIMAL)
    my_writer.writerow(col_values)
    return output.getvalue().strip()
 
  @staticmethod
  def get_header():
    cols = ["day", "ID", "descr (ignored)", "amount", "in_hours", "comment"]
    return TimeRow.to_csv_row(cols).strip()
  
  @staticmethod
  def datetime_from_row(string_repr):
    my_input = io.StringIO(string_repr)
    my_reader = csv.reader(my_input, delimiter = TimeRow.separator, quotechar='"', quoting=csv.QUOTE_MINIMAL)
    col_values = next(my_reader)
    return utils.human_readable_form_to_datetime(col_values[0]) if col_values[0] != TimeRow.relative_day_keyword else None
  
  @staticmethod
  def worklog_from_row( string_repr):
    my_input = io.StringIO(string_repr)
    my_reader = csv.reader(my_input, delimiter = TimeRow.separator, quotechar='"', quoting=csv.QUOTE_MINIMAL)
     
    col_values = next(my_reader)
    issue_id = col_values[1]
    amount = col_values[3]
    if TimeRow.enter_keyword in [issue_id, amount]:
      return None
    amount = float(amount)
    in_hours = col_values[4] == 'True'
    comment = col_values[5] if col_values[5] != TimeRow.enter_keyword else "Working on issue " + issue_id
    day = col_values[0] if col_values[0] != TimeRow.relative_day_keyword else None
    if in_hours:
      return AbsoluteWorkLog(issue_id, amount, day, comment)
    else:
      return RelativeWorkLog(issue_id, amount, comment)
  
class DayViewAfterInput(TimeRow):
  def __init__(self, day, issue_id, descr, hours, comment):
    TimeRow.__init__(self, day, issue_id, descr, hours, True, comment)
  
  def __repr__(self):
    return TimeRow.to_csv_row([self.day_as_human_readable_form, self.issue_id, self.descr, "{:1.2f}".format(self.amount), 
                           str(True), self.comment])

class DayViewBeforeInput(TimeRow):
  def __init__(self, day):
    TimeRow.__init__(self, day, None, "", 0, True, "")
  
  def __repr__(self):
    return TimeRow.to_csv_row([self.day_as_human_readable_form, TimeRow.enter_keyword, TimeRow.relative_day_keyword, str(8),
                           str(True), TimeRow.enter_keyword])

class IssueViewBeforeInput(TimeRow):
  def __init__(self, issue_id, descr):
    TimeRow.__init__(self, None, issue_id, descr, 0, False, "")
  
  def __repr__(self):
    return TimeRow.to_csv_row([TimeRow.relative_day_keyword, self.issue_id, self.descr, TimeRow.enter_keyword, str(False), TimeRow.enter_keyword])


def read_info_from_csv(inputfile):
  absoluteworklogs = []
  relativeworklogs = []
  
  alldates  = set([])
  with open(inputfile, 'r') as fi:
    fi.readline()
    for line in fi:
      datetime_day = TimeRow.datetime_from_row(line)
      wl = TimeRow.worklog_from_row(line)
      if datetime_day != None:
        alldates.add(datetime_day)
      if wl == None:
        continue
      if (wl.is_absolute()):
        absoluteworklogs.append(wl)
      else:
        relativeworklogs.append(wl)
  return absoluteworklogs, relativeworklogs, list(sorted(alldates))




