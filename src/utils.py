import datetime
from html.parser import HTMLParser
import re
white_space_regex = re.compile(r'\s+')

def date_string_to_datetime(ds):
  '''
  format should be: yyyy-mm-dd
  '''
  return datetime.datetime.strptime(ds, '%Y-%m-%d')
  
def datetime_to_human_readable_form(d):
  return d.strftime("%a %d-%m-%Y")

def datetime_to_date_string(d):
  return d.strftime("%Y-%m-%d")

def human_readable_form_to_datetime(hrd):
  return datetime.datetime.strptime(hrd, "%a %d-%m-%Y")

def hours_to_seconds(hours):
  return hours * 60 * 60

def seconds_to_hours(seconds):
  return seconds / float(60 * 60)

class MLStripper(HTMLParser):
  def __init__(self):
    super().__init__()
    self.reset()
    self.fed = []
  def handle_data(self, d):
    self.fed.append(d)
  def get_data(self):
    return self.fed

def strip_tags(html):
  s = MLStripper()
  s.feed(html)
  data_list = s.get_data()
  data_string = ''.join(data_list)
  data_string = white_space_regex.sub(' ', data_string) 
  return data_string

def remove_excess_spaces(txt): 
  return  ''.join(white_space_regex.sub(" ", txt).splitlines()).strip()

  