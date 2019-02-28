import datetime
from collections import defaultdict as dd
import utils
import jira_api
import random
import csv_io

class DayBucket(object):
  '''
  Helper class for get method.
  To put hours in a day and get back the amount of overflown hours.
  '''
  def __init__(self, maximum_amount, day):
    self.amount  = 0
    self.maximum_amount = maximum_amount
    self.day = day # datetime
    self.absoluteworklogs = []
  
  def put_absolute(self, absoluteworklog):
    self.amount += absoluteworklog.time_amount
    for awl in self.absoluteworklogs:
      if (awl.issue_id == absoluteworklog.issue_id and awl.comment == absoluteworklog.comment):
        awl.time_amount += absoluteworklog.time_amount
        return
    self.absoluteworklogs.append(absoluteworklog)
  
  def put_relative(self, relativeworklog, add_amount):
    '''
    add_mount is the absolute number of hours
    '''
    if (self.amount + add_amount) >= self.maximum_amount: # check if bucket would overflow
      new_amount = self.maximum_amount - self.amount
      absoluteworklog = csv_io.AbsoluteWorkLog(relativeworklog.issue_id, utils.seconds_to_hours(new_amount), utils.datetime_to_human_readable_form(self.day), relativeworklog.comment)
      self.put_absolute(absoluteworklog)
      return add_amount - new_amount 
    absoluteworklog = csv_io.AbsoluteWorkLog(relativeworklog.issue_id, utils.seconds_to_hours(add_amount), utils.datetime_to_human_readable_form(self.day), relativeworklog.comment)
    self.put_absolute(absoluteworklog)
    return 0
  
  def is_full(self):
    return self.maximum_amount == self.amount
  
  def __repr__(self):
    return "amount={:1.2f},max={:1.1f},day={:s},#worklogs={:d},worklogs=[{:s}]".format(self.amount, self.maximum_amount, 
                                                                  str(self.day).split()[0], len(self.absoluteworklogs),
                                                                  ','.join([str(x) for x in self.absoluteworklogs]))


def put(jira_info, total_hours = None, inputfile = 'workloglog.csv', actually_submit=False):
  
  #read user-edited csv
  absoluteworklogs, relativeworklogs, alldates = csv_io.read_info_from_csv(inputfile)
  
  # make day buckets and put the absolute worklogs in them
  bucket_list = [] # literal bucket list
  for d in alldates:
    this_day_string = utils.datetime_to_date_string(d)
    my_bucket = DayBucket(utils.hours_to_seconds(8), d)
    for absolute_worklog in absoluteworklogs: #TODO return absolute_worklogs in dict to avoid this loop
      if absolute_worklog.date_string == this_day_string:
        my_bucket.put_absolute(absolute_worklog)
    bucket_list.append(my_bucket)
  
  #check if we actually have this many hours available
  #TODO: allow more hours than 8*number_days
  sum_time_over_days = sum([b.amount for b in bucket_list])
  max_time_all_days = sum([b.maximum_amount for b in bucket_list])
  if total_hours == None:
    total_hours = utils.seconds_to_hours(max_time_all_days)
  elif (utils.seconds_to_hours(max_time_all_days) < total_hours):
    raise Exception("Cannot normalize to {:2.2f} hours as there are only {:2.2f} available".format(total_hours, utils.seconds_to_hours(max_time_all_days)))
  total_time_left = utils.hours_to_seconds(total_hours) - sum_time_over_days

  # distribute the relative worklogs over the days
  #TODO: not all spread out over all days?
  total_relative_time = sum([wl.time_amount for wl in relativeworklogs])
  smallest_preferred_time_interval = utils.hours_to_seconds(0.5)
  if total_relative_time > 0:
    scale_factor = total_time_left / float(total_relative_time)
    absolute_time_amount_total = int(round(total_relative_time * scale_factor,2))
    while absolute_time_amount_total > 0:
      for relativeworklog in relativeworklogs:
        absolute_time_amount_this_worklog = int(round(relativeworklog.time_amount * scale_factor,2))
        nr_buckets_for_interval = len(bucket_list)
        interval_amount_this_worklog = -1
        while interval_amount_this_worklog <= smallest_preferred_time_interval and nr_buckets_for_interval >= 1:
          interval_amount_this_worklog = int(round(absolute_time_amount_this_worklog / float(nr_buckets_for_interval),2))
          nr_buckets_for_interval -= 1

        if absolute_time_amount_this_worklog > 0:
          indices_bucket_list = list(range(len(bucket_list)))
          random.shuffle(indices_bucket_list)
          for i in indices_bucket_list:
            b = bucket_list[i]
            if not b.is_full():
              amount_returned = b.put_relative(relativeworklog, interval_amount_this_worklog)
              amount_actually_submitted =  (interval_amount_this_worklog - amount_returned)
              absolute_time_amount_this_worklog -= amount_actually_submitted
              absolute_time_amount_total -= amount_actually_submitted
              interval_amount_this_worklog = min(absolute_time_amount_this_worklog, interval_amount_this_worklog)
              if absolute_time_amount_this_worklog <= 0 or interval_amount_this_worklog <= 0:
                break
        if absolute_time_amount_total <= 0:
          break
  total_seconds_submitted = 0 
  
  print('Going to delete existing worklogs in this sprint and submit this:')
  for b in bucket_list:
    print("day: {:}, total hours: {:2.2f}".format(utils.datetime_to_human_readable_form(b.day), utils.seconds_to_hours(b.amount)))
    for awl in b.absoluteworklogs:
      print("\t",awl)
    total_seconds_submitted += b.amount
  print('Total: {:2.2f}h'.format(utils.seconds_to_hours(total_seconds_submitted)))
  
  resp = input('Are you sure you want to overwrite worklogs for the sprint from {:s} to (including) {:s} with the above?\n'\
               'Enter y/n:'.format(utils.datetime_to_human_readable_form(alldates[0]), utils.datetime_to_human_readable_form(alldates[-1])))
  if actually_submit and resp.strip().lower() == 'y':
    existing_worklogs = jira_api.get_existing_worklogs(jira_info, utils.datetime_to_date_string(alldates[0]), 
                                                   utils.datetime_to_date_string(alldates[-1]))
    _delete_existing_worklogs(jira_info, existing_worklogs)
    for i in range(len(bucket_list)):
      for awl in bucket_list[i].absoluteworklogs:
        jira_api.insert_worklog(jira_info, awl.issue_id, awl.time_amount, awl.date_string, awl.comment)
      print("Updated day {:d} of {:d}".format(i+1, len(bucket_list)))
    print('Done!')
  else:
    print('Did not delete or update anything.')
  
def _delete_existing_worklogs(jira_info, existing_worklogs):
  for wl in existing_worklogs:
    jira_api.delete_worklog(jira_info, wl['id'])
      
def delete(jira_info, negative_sprint_index, board_id, actually_submit=False):
  active_sprint_id = jira_api.get_active_sprint_id(jira_info, board_id)
  earlier_sprint = jira_api.get_sprint_before(jira_info, board_id, negative_sprint_index, active_sprint_id)
  earlier_sprint_id = earlier_sprint['id']
  earlier_sprint_goal = earlier_sprint['goal']
  date_time_start = utils.date_string_to_datetime(earlier_sprint['startDate'].split('T')[0])
  date_time_end = _get_end_date(earlier_sprint)
  existing_worklogs = jira_api.get_existing_worklogs(jira_info, utils.datetime_to_date_string(date_time_start), 
                                                     utils.datetime_to_date_string(date_time_end - datetime.timedelta(days=1)))
  total_hours_alread_logged = sum([wl['time'] for wl in existing_worklogs])

  resp = input('Are you sure you want to delete all worklogs for sprint with id {:d} between {:s} and {:s}?\n'\
               'It was {:d} sprints back with sprint goal "{:s}".' \
                '\nYou logged {:2.2f} hours there.\nEnter y/n:'.
                  format(earlier_sprint_id, utils.datetime_to_human_readable_form(date_time_start),
                         utils.datetime_to_human_readable_form(date_time_end - datetime.timedelta(days=1)),
                         negative_sprint_index * -1, earlier_sprint_goal, total_hours_alread_logged))
  if actually_submit and resp.strip().lower() == 'y':
    _delete_existing_worklogs(jira_info, existing_worklogs)
  else:
    print('Did not delete anything.')

def _get_working_dates(date_time_start, date_time_end):
  dates_list = [date_time_start]
  new_date = date_time_start + datetime.timedelta(days=1)
  while (not new_date == date_time_end):
    if (not new_date.weekday() in [5,6]):
      dates_list.append(new_date)
    new_date = new_date + datetime.timedelta(days=1)
  return dates_list

def _get_day_to_dateviews(existing_worklogs):
  day_to_dateviews = dd(list)
  for wl in existing_worklogs: # already in order
    dv = csv_io.DayViewAfterInput(wl['date'].split('T')[0], wl['issue_id'], wl['summary'], wl['time'], wl['comment'])
    day_to_dateviews[dv.day_as_datetime].append(dv)
  return day_to_dateviews

def _get_issuesviews(issues):
  issueviews = []
  for oi in sorted(issues, key = lambda x: x['issue_id']):
    descr = oi['summary'] 
    if oi['epic'] != None:
      descr +=  " | epic: " + oi['epic']
    if oi['description'] != None:
      descr +=  " | " + oi['description']
    descr = utils.remove_excess_spaces(utils.strip_tags(descr))
    iv = csv_io.IssueViewBeforeInput(oi['issue_id'], descr)
    issueviews.append(iv)
  return issueviews

def _get_end_date(earlier_sprint):
  return utils.date_string_to_datetime(earlier_sprint['completeDate'].split('T')[0]) if 'completeDate' in earlier_sprint \
                    else utils.date_string_to_datetime(earlier_sprint['endDate'].split('T')[0]) 
                    
def get(jira_info, negative_sprint_index, board_id, other_project_ids, outputfile = 'workloglog.csv'):
  active_sprint_id = jira_api.get_active_sprint_id(jira_info, board_id)
  earlier_sprint = jira_api.get_sprint_before(jira_info, board_id, negative_sprint_index, active_sprint_id)
  earlier_sprint_id = earlier_sprint['id']
  earlier_sprint_goal = earlier_sprint['goal'] 
  date_time_start = utils.date_string_to_datetime(earlier_sprint['startDate'].split('T')[0])
  date_time_end = _get_end_date(earlier_sprint)
  
  dates_list = _get_working_dates(date_time_start, date_time_end)

  existing_worklogs = jira_api.get_existing_worklogs(jira_info, 
                                                     utils.datetime_to_date_string(date_time_start), 
                                                     utils.datetime_to_date_string(dates_list[-1]))
  
  total_hours_already_logged = sum([wl['time'] for wl in existing_worklogs])

  day_to_dateviews = _get_day_to_dateviews(existing_worklogs)
  
  all_issues =  jira_api.get_issues_in_sprint(jira_info, board_id, earlier_sprint_id)
  for project_id in other_project_ids:
    all_issues.extend(jira_api.get_issues_in_project(jira_info, project_id))
  issueviews = _get_issuesviews(all_issues)
  
  with open(outputfile, 'w') as fo:
    fo.write(csv_io.TimeRow.get_header() + "\n")
    for issueview in issueviews:
      fo.write(str(issueview) + "\n")
    for this_day in dates_list:
      dayviews = day_to_dateviews[this_day]
      if len(dayviews) == 0: # write empty DateView
        fo.write(str(csv_io.DayViewBeforeInput(utils.datetime_to_date_string(this_day))) + "\n")
      for dayview in dayviews:
        fo.write(str(dayview) + "\n")
        
  print('Sprint goal: "{:s}"'.format(earlier_sprint_goal))
  print('Start date: {:s}, end date:{:s}'.format(utils.datetime_to_human_readable_form(date_time_start), 
                                                 utils.datetime_to_human_readable_form(date_time_end - datetime.timedelta(days=1))))
  print("Total hours already logged: {:1.2f}".format(total_hours_already_logged))
  print("Wrote to file \"{:s}\"".format(outputfile))


  