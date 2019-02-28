Tic Tac Tempo

==


<img src="clock.gif" alt="drawing" width="80"/>

Allows you to easily insert per-sprint timesheets in JIRA Tempo, using both relative as well as absolute time estimates.

Main advantages:
- Not have to remember the stories and their description from a past sprint, as these will be presented to you
- Not have to remember the exact hours you worked, neither you will have to make sure they sum up to some total amount of hours. This is handled by the code.

### Installation:  


```
virtualenv --python /usr/bin/python3 --no-site-packages env  
source env/bin/activate  
pip install -r requirements.txt  
```

### Usage:
General usage is 

1. You first `get` a .csv file for a sprint. This will contain relevant stories, based on board ID & project IDs. 
2. Using a csv editor, in this csv file you put your time estimates per story (relative) or per day (absolute).
3. You `put` your updated csv file back into JIRA Tempo. This will update your timesheet for that sprint, also according to a parameter denoting your total amount of hours in that sprint.

Additionally you can `delete` all logged time for a sprint.  

Note one can use the `-h` flag to get help information: `python src/cli.py -h` 

#### `get` : getting worklog data

Example command:
```
python src/cli.py  get jira.textkernel.nl vanbelle:<password> -f myworklog.csv -n 1 -b 52 -p IH
```

Here we use the `get` action to get work log data, using parameter `-n` we get it from from *1* sprint back.  
Using parameter `-b` we 
get all the stories on the board with board ID *52*, and using parameter `-p` also those
belonging to project ID *IH*.
<sub>(If you don't know your board ID: it should be in the url of your JIRA board, e.g. `https://jira.textkernel.nl/secure/RapidBoard.jspa?rapidView=52`
has board ID 52).  </sub>   
Using parameter `-f` this is written to *myworklog.csv*.

Example console output:
```
Sprint goal: "Improved Match DE/FR ready to be released, ready to implement fully Match Templating"
Start date: Mon 04-02-2019, end date:Sun 17-02-2019
Total hours already logged: 00.00
Wrote to file "myworklog.csv"
```

This results in a csv as the one in the file [myworklog.csv.get_example](myworklog.csv.get_example).  
It contains the story IDs and their descriptions, and the days of that sprint.  
If you already logged hours in that sprint, they will also be in the csv, as absolute hours.

#### `put` : putting logged hours
Open the csv file from the previous `get` action and add your time in it.  
This can be done in 2 ways, absolute and relative:  
- Absolute: In the bottom rows where the 'day' column is denoting a day, e.g. 'Mon 18-02-2019', you can input a story 'ID'  and the exact 'amount' of hours.
- Relative: On the rows where the 'day' column is denoting '(ignored)', you can input a relative 'amount'.

Floating point numbers are supported.

Hours for the relative amounts will be distributed, over what is left from the absolute hours, and over the unique days that have a row in the sheet. You can have multiple rows with the same 'day' in the sheet.  
You can remove all rows with a specific 'day' to not log anything on that day.  

This results in a csv as the one in the file [myworklog.csv.put_example](myworklog.csv.put_example).

Thereafter, we can put the logged time into JIRA:
```
python src/cli.py  put jira.textkernel.nl vanbelle:<password> -f myworklog.csv -t 80
```
Using the `-t` parameter we express the total hours is 80.

This will show you what will be logged in JIRA exactly. If there were already logged hours there, these
 will be overwritten. It will prompt you to accept or reject this:
```
Going to delete existing worklogs in this sprint and submit this:
day: Mon 04-02-2019, total hours: 8.00
         issue: IH-10 amount: 0.3786h comment: "Working on issue IH-10" date:2019-02-04
         issue: IH-3 amount: 1.0817h comment: "Working on issue IH-3" date:2019-02-04
         issue: IH-5 amount: 1.1356h comment: "Working on issue IH-5" date:2019-02-04
         issue: IH-6 amount: 1.1031h comment: "Working on issue IH-6" date:2019-02-04
         issue: SRCHRD-437 amount: 1.3253h comment: "Working on issue SRCHRD-437" date:2019-02-04
         issue: SRCHRD-478 amount: 0.5408h comment: "Working on issue SRCHRD-478" date:2019-02-04
         issue: SRCHRD-484 amount: 0.0011h comment: "Working on issue SRCHRD-484" date:2019-02-04
         issue: SRCHRD-500 amount: 0.7572h comment: "Working on issue SRCHRD-500" date:2019-02-04
         issue: SRCHRD-510 amount: 1.1358h comment: "Working on issue SRCHRD-510" date:2019-02-04
         issue: SRCHRD-513 amount: 0.5408h comment: "Working on issue SRCHRD-513" date:2019-02-04
day: Tue 05-02-2019, total hours: 8.00
         issue: IH-3 amount: 8.0000h comment: "Working on issue IH-3" date:2019-02-05
(etc... etc...)
day: Fri 15-02-2019, total hours: 8.00
         issue: IH-3 amount: 1.0817h comment: "Working on issue IH-3" date:2019-02-15
         issue: IH-5 amount: 0.7872h comment: "Working on issue IH-5" date:2019-02-15
         issue: IH-6 amount: 0.5678h comment: "Working on issue IH-6" date:2019-02-15
         issue: SRCHRD-437 amount: 1.3253h comment: "Working on issue SRCHRD-437" date:2019-02-15
         issue: SRCHRD-478 amount: 0.5408h comment: "Working on issue SRCHRD-478" date:2019-02-15
         issue: SRCHRD-484 amount: 0.5408h comment: "Working on issue SRCHRD-484" date:2019-02-15
         issue: SRCHRD-500 amount: 0.7572h comment: "Working on issue SRCHRD-500" date:2019-02-15
         issue: SRCHRD-505 amount: 0.6311h comment: "Working on issue SRCHRD-505" date:2019-02-15
         issue: SRCHRD-510 amount: 1.1358h comment: "Working on issue SRCHRD-510" date:2019-02-15
         issue: SRCHRD-513 amount: 0.0011h comment: "Working on issue SRCHRD-513" date:2019-02-15
         issue: SRCHRD-518 amount: 0.6311h comment: "Working on issue SRCHRD-518" date:2019-02-15
Total: 80.00h
Are you sure you want to overwrite worklogs for the sprint from Mon 04-02-2019 to (including) Fri 15-02-2019 with the above?
Enter y/n:
``` 
Upon pressing `y` the hours in Tempo will be updated an you'll a message after each updated day.

#### ` delete`: deleting logged hours
Example:
```
 python src/cli.py delete jira.textkernel.nl vanbelle:<password>  -n 1 -b 52
```
Just as with the `get` action above, `-n` refers to the number of sprints back, and `-b` refers to the board ID.
  

A prompt will be presented, for example:
``` 
Are you sure you want to delete all worklogs for sprint with id 875 between Mon 04-02-2019 and Sun 17-02-2019?
It was 1 sprints back with sprint goal "Improved Match DE/FR ready to be released, ready to implement fully Match Templating".
You logged 79.99 hours there.
```
