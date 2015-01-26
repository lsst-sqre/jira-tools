#!/usr/bin/env python

import argparse
import sys
import requests
from collections import Counter

SP_FIELD = "customfield_10202" # story points, as established by experiment

def noNone(s):
    return 0 if s is None else s

def eligibleIssues(allIssues):
    if allIssues:
        return 'story, bug, improvement'
    else:
        return 'story'

def runJqlQuery(jql, **kwargs):
    SEARCH_URL = "https://jira.lsstcorp.org/rest/api/2/search"
    return requests.get(SEARCH_URL, params={"jql": jql.format(**kwargs)}).json()

def getEpicById(issue):
    return runJqlQuery('id = {id}', id=issue)['issues'][0]

def getEpicEstimatedSps(issue):
    return getEpicById(issue)['fields'][SP_FIELD]

def getIssuesInEpic(issue, allIssues):
    jql = '"Epic Link" = {id} AND issuetype IN ({types})'
    result = runJqlQuery(jql, id=issue, types=eligibleIssues(allIssues))
    return result['issues']

def getEpicPlannedSps(issue, allIssues):
    issues = getIssuesInEpic(issue, allIssues)
    return sum(noNone(issue['fields'][SP_FIELD]) for issue in issues)

def getEpicCompletedSps(issue, allIssues):
    issues = getIssuesInEpic(issue, allIssues)
    return sum(noNone(issue['fields'][SP_FIELD]) for issue in issues
               if issue['fields']['status']['statusCategory']['name'] == 'Complete')

def getEpicsPerWbsAndCycle(wbs, cycle):
    jql = 'issuetype = Epic AND WBS ~ "{wbs}*" AND cycle = "{cycle}" ORDER BY Id'
    result = runJqlQuery(jql, wbs=wbs, cycle=cycle)
    return [issue['key'] for issue in result['issues']]

def printEpicHeader():
    lines = [
        ("       ", "Estimated", "Planned", "Completed", "  Delta  ", "  Delta  "),
        ("       ", "         ", "       ", "         ", "(Est-Pla)", "(Pla-Cmp)")
    ]
    for line in lines:
        print " ".join(line)
    return [len(word) for word in lines[0]]

def printEpic(epic, widths, allIssues):
    estimated = int(noNone(getEpicEstimatedSps(epic)))
    planned = int(noNone(getEpicPlannedSps(epic, allIssues)))
    completed = int(noNone(getEpicCompletedSps(epic, allIssues)))
    template = "{id:>{w1}} {est:>{w2}} {pl:>{w3}} {comp:>{w4}} {del1:>{w5}} {del2:>{w6}}"
    print template.format(id=epic, est=estimated, pl=planned, comp=completed,
                          del1=estimated-planned, del2=planned-completed,
                          w1=widths[0], w2=widths[1], w3=widths[2],
                          w4=widths[3], w5=widths[4], w6=widths[5])

def printEpicStandalone(epic, allIssues):
    field_widths = printEpicHeader()
    printEpic(epic, field_widths, allIssues)
    assigned = Counter()
    done = Counter()
    for issue in getIssuesInEpic(epic, allIssues):
        assignee = issue['fields']['assignee']['displayName']
        assigned[assignee] += int(noNone(issue['fields'][SP_FIELD]))
        if issue['fields']['status']['statusCategory']['name'] == 'Complete':
            done[assignee] += int(noNone(issue['fields'][SP_FIELD]))
    for assignee in assigned.keys():
        print "{s:>{w1}}{assigned:>{w2}} {done:>{w3}} {name}".format(
            s=" ", assigned=assigned[assignee], done=done[assignee], name=assignee,
            w1=field_widths[0]+field_widths[1], w2=field_widths[3], w3=field_widths[4])

def printSummary(wbs, cycle, allIssues):
    field_widths = printEpicHeader()
    for epic in getEpicsPerWbsAndCycle(wbs, cycle):
        printEpic(epic, field_widths, allIssues)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-issues", action="store_true")

    subparsers = parser.add_subparsers()

    parser_epic = subparsers.add_parser('epic')
    parser_epic.add_argument('epic')
    parser_epic.set_defaults(func=lambda args: printEpicStandalone(args.epic, args.all_issues))

    parser_summary = subparsers.add_parser('summary')
    parser_summary.add_argument('wbs')
    parser_summary.add_argument('cycle')
    parser_summary.set_defaults(func=lambda args: printSummary(args.wbs, args.cycle, args.all_issues))

    args = parser.parse_args()
    args.func(args)
