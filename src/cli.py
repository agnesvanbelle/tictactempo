import argparse
import getpass
import socket

from jira_api import JiraInfo
from main import get, put, delete

parser = argparse.ArgumentParser(description='Tictempoc.')

  
# Required positional arguments:
################################
# action
# jira host
# username:password where :password is optional. If not provided, will be prompted for password with pswd = getpass.getpass('Password:') 
parser.add_argument("action", type=str, help='action (get / put / delete)')
parser.add_argument("jira_host", type=str, help="JIRA host, e.g. jira.textkernel.nl")
parser.add_argument("credentials", type=str, help="username or username:password")

# Required arguments per action:
################################
## get:
# nr_sprints_back
# board_id
# list of other project ids
# optional: outputfile='workloglog.csv'
#
## put:
# total_hours = 80, 
# optional: inputfile = 'workloglog.csv'
#
## delete:
# nr_sprints_back
# board_id
parser.add_argument('-n', metavar="1", type=int, help='nr. sprints back (0 or positive number)')
parser.add_argument('-b', metavar="52", type=str, help="board ID")
parser.add_argument('-p', metavar="IH", nargs = '*',help="project ID (can be multiple, separated by space)", default=[])
parser.add_argument('-f', metavar="myworklog.csv", type=str, help="input (put) or output (get) csv file")
parser.add_argument('-t', metavar="80", type=int, help="total hours", default=None)

args = parser.parse_args()
action = args.action
jira_host = args.jira_host 
credentials = args.credentials

if action == 'get' or action == 'delete':
  if args.n is None:
    raise ValueError("Missing parameter -n: Nr. sprints back")
  elif args.n < 0:
    raise ValueError("Parameter -n has to be 0 or a positive number")
  if args.b is None:
    raise ValueError("Missing parameter -b: Board ID")
  if args.f is None:
    args.f = 'worklog.csv'
if action == 'put':
  if args.f is None:
    raise ValueError("Missing parameter -f: input csv file")

# try to resolve host
try:
  socket.gethostbyname(jira_host)
except:
  raise Exception("Could not resolve host \"{:}\"".format(jira_host))

# parse password or ask for password
username = credentials
password = -1
ask_for_password = True
splitted_credentials = credentials.split(':', 1)
if len(splitted_credentials) == 2:
  username = splitted_credentials[0]
  password = splitted_credentials[1]
else:
  password = getpass.getpass('Enter password:') 

# do the action
jira_info = JiraInfo(jira_host, username, password)
if action == 'get':
  get(jira_info, -args.n, args.b, args.p, outputfile=args.f)
elif action == 'delete':
  delete(jira_info, -args.n, args.b, actually_submit = True)
elif action == 'put':
  put(jira_info, total_hours = args.t, inputfile = args.f, actually_submit = True)
else:
  raise Exception('action argument should be one of: get, delete, put')
