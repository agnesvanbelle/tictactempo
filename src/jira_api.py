import requests
from requests.auth import HTTPBasicAuth
import json
import utils
from time import sleep
import random

# TODOs:
# check if response makes sense: use r.raise_for_status() or check r.status_code
# http://developer.tempo.io/doc/timesheets/api/rest/latest/#-1503281163

jira_delete_put_call_seconds_sleep_bounds = (0.1,0.5)


class JiraInfo():
  def __init__(self, jira_host, username, password):
    self.username = username
    self.password = password
    if jira_host[-1] !="/":
      jira_host += "/"
    if jira_host.startswith("http://"):
      jira_host = "https://" + jira_host[7:]
    elif not jira_host.startswith("https://"):
      jira_host = "https://" + jira_host
    self.jira_issue_endpoint = jira_host + "rest/api/2/issue/"
    self.jira_search_endpoint = jira_host + "rest/api/2/search/"
    self.jira_greenhopper_endpoint = jira_host + "rest/greenhopper/latest/"
    self.jira_boards_endpoint = jira_host + "rest/agile/1.0/board/"
    self.tempo_timesheets_endpoint = jira_host +  "rest/tempo-timesheets/3/"

def _sleep():
  sleep(random.uniform(jira_delete_put_call_seconds_sleep_bounds[0],jira_delete_put_call_seconds_sleep_bounds[1]))


def get_existing_worklogs(jira_info, date_from, date_to):
  '''
  date_from / date_to should be strings and e.g. 2018-09-20 / 2018-09-25
  date_to is inclusive
  '''
  url = jira_info.tempo_timesheets_endpoint + "worklogs?" + "dateFrom="+ date_from + "&dateTo=" + date_to + "&username=" + jira_info.username
  r = requests.get(url,  auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  _sleep()
  return _transform_worklogs(r.json())

def _transform_worklogs(worklog_list_from_jira):
  l = []
  for v in worklog_list_from_jira:
    new_v  = {}
    new_v['comment'] = v['comment']
    new_v['time'] = utils.seconds_to_hours(int(v['timeSpentSeconds'])) 
    new_v['issue_id'] = v['issue']['key']
    new_v['summary'] = v['issue']['summary']
    new_v['id'] = str(v['jiraWorklogId'])
    new_v['date'] = v['dateStarted']
    new_v['issue_type'] = v['issue']['issueType']['name'].lower()
    l.append(new_v)
  return l

def get_projects_for_board(jira_info, board_id):
  '''
  board_id is e.g. 52
  '''
  url = jira_info.jira_boards_endpoint + str(board_id) + "/project"
  r = requests.get(url,  auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  _sleep()
  return [{ k: v[k] for k in ['id', 'key', 'name'] } for v in r.json()['values']]

def delete_worklog(jira_info, worklog_id):
  '''
  worklog_id is e.g. 34015
  '''
  try:
    url = jira_info.tempo_timesheets_endpoint + "worklogs/" + str(worklog_id)
    _ = requests.delete(url,  auth = HTTPBasicAuth(jira_info.username, jira_info.password))
    print('Deleted worklog {:s}'.format(url))
    _sleep()
  except Exception as e:
    print(e)
    pass

def insert_worklog(jira_info, issue_id, time_seconds, date_string, comment):
  '''
  issue_id is e.g. SRCHRD-392
  date_string is e.g. 2018-09-25, in other words, the format is yyyy-mm-dd
  '''
  this_data = json.dumps({
    "timeSpentSeconds": int(time_seconds),
    "dateStarted": date_string + "T00:00:00.000",
    "author": {
    "name": jira_info.username
    },
    "issue": {
      "key": issue_id
    },
    "comment": comment
  })
  r = requests.post(jira_info.tempo_timesheets_endpoint + 'worklogs', data = this_data, auth = HTTPBasicAuth(jira_info.username, jira_info.password), 
                    headers = {'Content-type': 'application/json'})
  #print(jira_info.tempo_timesheets_endpoint + 'worklogs')
  #print(this_data)
  _sleep()
  return r.json()
  
  
def get_issue_info(jira_info, issue_id):
  '''
  issue_id is e.g. SRCHRD-392
  '''
  r = requests.get(jira_info.jira_issue_endpoint + issue_id,  auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  _sleep()
  return r.json()

def get_active_sprint_id(jira_info, board_id):
  '''
  board_id is e.g. 52
  '''
  url = jira_info.jira_boards_endpoint + str(board_id) + "/sprint?state=active"
  r = requests.get(url,  auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  try:
    _sleep()
    return r.json()['values'][0]['id']
  except:
    print(r.content) #TODO do this checking everywhere
    
def get_board_ids(jira_info, project_id):
  '''
  project_id is e.g. "SRCHRD"
  '''
  url = jira_info.jira_greenhopper_endpoint + "rapidviews/list?projectKey=" + project_id 
  r = requests.get(url,  auth=HTTPBasicAuth(jira_info.username, jira_info.password))
  _sleep()
  return r.json()

def get_board_id(jira_info, board_name):
  '''
  board_name is e.g. "Search R&D"
  '''
  r = requests.get(jira_info.jira_boards_endpoint, auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  d = json.loads(r.text)
  for v in d['values']:
    if v['name'].lower() == board_name.lower():
      _sleep()
      return v['id']

def get_sprint_before(jira_info, board_id, negative_index, active_sprint_id):
  '''
  board_id is e.g. 52
  negative_index can be e.g. -1
  active_sprint_id is e.g. 675
  '''
  max_results_page = 1000
  if negative_index <= max_results_page * -1:
    raise Exception("Cannot go {:d} or more sprints back".format(max_results_page))
  base_url = jira_info.jira_boards_endpoint + str(board_id) + "/sprint?" + "maxResults=" + str(max_results_page)
  #print(base_url)
  page_index = 0
  r = requests.get(base_url + "&startAt=" + str(page_index), auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  d = r.json()
  if 'errors' in d :
    raise ValueError('Error from Jira:', d['errors'])
  while (not d['isLast']): # loop until we are on the last page
    page_index += 1
    r = requests.get(base_url + "&startAt=" + str(page_index), auth = HTTPBasicAuth(jira_info.username, jira_info.password))
    d = r.json()
 
  sprint_list_last_page = list(filter(lambda x: 'startDate' in x, d['values']))
  # sort, because the order returned is the order in the backlog
  sprint_list_last_page.sort(key = lambda s: utils.date_string_to_datetime(s['startDate'].split('T')[0]))
  for i in range(len(sprint_list_last_page)-1, -1, -1):
    if  sprint_list_last_page[i]['id'] == active_sprint_id:
      if negative_index < i * -1:
        raise Exception("Cannot go more than {:d} sprints back".format(i))
      _sleep()
      return sprint_list_last_page[i + negative_index]
  #TODO fix this extreme edge case
  raise Exception('There are more than {:d} sprints between your current active sprint \
                    and the actual order in the backlog. Cannot proceed.'.format(max_results_page))

def _transform_issues(issue_list_from_jira):
  l = []
  for v in issue_list_from_jira:
    new_v  = {}
    new_v['issue_id'] = v['key']
    new_v['summary'] = v['fields']['summary']
    new_v['description'] = v['fields']['description']
    new_v['sub_task'] = v['fields']['issuetype']['subtask']
    new_v['epic'] = v['fields']['epic']['name'] if 'epic' in v['fields'] else None
    l.append(new_v)
  return l

def get_issues_in_sprint(jira_info, board_id, sprint_id):
  '''
  board_id is e.g. 52
  sprint_id is e.g 675  
  '''
  url = jira_info.jira_boards_endpoint + str(board_id) + "/sprint/" + str(sprint_id) + "/issue?fields=summary,description,issuetype,epic"
  r = requests.get(url, auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  d = r.json()
  _sleep()
  return _transform_issues(d['issues'])

def get_issues_in_project(jira_info, project_id):
  '''
  project_id is e.g. "IH"
  '''
  url = jira_info.jira_search_endpoint + "?jql=project=" + project_id + "&fields=summary,description,issuetype,epic"
  r = requests.get(url, auth = HTTPBasicAuth(jira_info.username, jira_info.password))
  d = r.json()
  _sleep()
  return _transform_issues(d['issues'])

  
