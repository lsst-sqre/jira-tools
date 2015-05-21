#!/usr/bin/env python

import argparse
import re
import sys
import requests
from collections import Counter

# Custom field names, as established by experiment
SP_FIELD      = "customfield_10202" # story points
CYCLE_FIELD   = "customfield_10900" # cycle
SUMMARY_FIELD = "customfield_10207" # epic summary

def noNone(s):
    return 0 if s is None else s

def eligibleIssues(allIssues):
    if allIssues:
        return 'story, bug, improvement'
    else:
        return 'story'

def isComplete(issue):
    if issue['fields']['status']['statusCategory']['name'] == 'Complete':
        return True
    return False

def excludeWontFix(issues):
    return [issue for issue in issues if issue['fields']['status']['name'] != 'Won\'t Fix']

def runJqlQuery(jql, **kwargs):
    SEARCH_URL = "https://jira.lsstcorp.org/rest/api/2/search"
    MAX_RESULTS = 10000 # May be limited server-side
    return requests.get(SEARCH_URL, params={"maxResults": MAX_RESULTS, "jql": jql.format(**kwargs)}).json()

def getIssueById(issueId):
    return runJqlQuery('id = {id}', id=issueId)['issues'][0]

def getEpicEstimatedSps(epic):
    return epic['fields'][SP_FIELD]

def getEpicSummary(epic):
    return epic['fields'][SUMMARY_FIELD]

def getIssuesInEpic(issue, args):
    jql = '"Epic Link" = {id} AND issuetype IN ({types})'
    result = runJqlQuery(jql, id=issue, types=eligibleIssues(args.all_issues))
    if not args.wontfix_is_done:
        return excludeWontFix(result['issues'])
    else:
        return result['issues']

def sumStoryPoints(issues):
    return sum(noNone(issue['fields'][SP_FIELD]) for issue in issues)

def getWorkBreakdown(epicId):
    description = getIssueById(epicId)['fields']['description'] or ""
    # Does the epic contain a breakdown line? If not, return None.
    bdown = re.search(r"^Breakdown:.*$", description, re.MULTILINE)
    if bdown:
        return {item.split()[0] : float(item.split()[1]) / 100.0
                for item in re.compile(r"(\w+ ?\d+)%;?").findall(description, bdown.start(), bdown.end())}
    else:
        return {}

def getEpicsPerWbsAndCycle(wbs, cycle):
    jql = 'issuetype = Epic AND WBS ~ "{wbs}*" ORDER BY Id'
    result = runJqlQuery(jql, wbs=wbs)
    # Filtering client-side means tranferring more data, but is unlikely to be
    # a significant performance hit unless the number of epics is huge.
    return [issue['key'] for issue in result['issues'] if cycle is None
            or (issue['fields'][CYCLE_FIELD] and issue['fields'][CYCLE_FIELD]['value'] == cycle)]

def printEpicHeader():
    lines = [
        ("        ", "Estimated", "Planned", "Completed", "  Delta  ", "  Delta  "),
        ("        ", "         ", "       ", "         ", "(Est-Pla)", "(Pla-Cmp)")
    ]
    for line in lines:
        print " ".join(line)
    return [len(word) for word in lines[0]]

def printEpic(epicId, widths, args):
    epic = getIssueById(epicId)
    estimated = int(noNone(getEpicEstimatedSps(epic)))
    summary = getEpicSummary(epic)
    issues = getIssuesInEpic(epicId, args)
    planned = int(sumStoryPoints(issues))
    completed = int(sumStoryPoints(issue for issue in issues if isComplete(issue)))
    template = "{id:>{w1}} {est:>{w2}} {pl:>{w3}} {comp:>{w4}} {del1:>{w5}} {del2:>{w6}} {desc}"
    print template.format(id=epicId, est=estimated, pl=planned, comp=completed,
                          del1=estimated-planned, del2=planned-completed, desc=summary,
                          w1=widths[0], w2=widths[1], w3=widths[2],
                          w4=widths[3], w5=widths[4], w6=widths[5])
    return (estimated, planned, completed)

def printEpicStandalone(args):
    field_widths = printEpicHeader()
    estSp, planSp, compSp = printEpic(args.epic, field_widths, args)
    estimated = Counter()
    assigned = Counter()
    done = Counter()
    for assignee, percentage in getWorkBreakdown(args.epic).iteritems():
        estimated[assignee] = int(round(estSp * percentage))
    for issue in getIssuesInEpic(args.epic, args):
        try:
            assignee = issue['fields']['assignee']['name']
        except TypeError:
            assignee = "Not assigned"
        assigned[assignee] += int(noNone(issue['fields'][SP_FIELD]))
        if isComplete(issue):
            done[assignee] += int(noNone(issue['fields'][SP_FIELD]))
    for assignee in set(assigned.keys() + estimated.keys()):
        print "{s:>{w1}} {estimated:>{w2}} {assigned:>{w3}} {done:>{w4}} {name}".format(
            s=" ", estimated=estimated[assignee], assigned=assigned[assignee], done=done[assignee], name=assignee,
            w1=field_widths[0], w2=field_widths[1], w3=field_widths[2], w4=field_widths[3])

def printSummary(args):
    field_widths = printEpicHeader()
    estimated = Counter()
    for epic in getEpicsPerWbsAndCycle(args.wbs, args.cycle):
        estSp, planSp, compSp = printEpic(epic, field_widths, args)
        for assignee, percentage in getWorkBreakdown(epic).iteritems():
            estimated[assignee] += int(round(estSp * percentage))
    print
    for assignee, sps in estimated.iteritems():
        print "{assignee:>{w1}} {sps:>{w2}}".format(assignee=assignee, sps=sps, w1=field_widths[0], w2=field_widths[1])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-issues", action="store_true")
    parser.add_argument("--wontfix-is-done", action="store_true")

    subparsers = parser.add_subparsers()

    parser_epic = subparsers.add_parser('epic')
    parser_epic.add_argument('epic')
    parser_epic.set_defaults(func=printEpicStandalone)

    parser_summary = subparsers.add_parser('summary')
    parser_summary.add_argument("--cycle", default=None)
    parser_summary.add_argument('wbs')
    parser_summary.set_defaults(func=printSummary)

    args = parser.parse_args()
    args.func(args)
