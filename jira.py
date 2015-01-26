import argparse
import sys
import requests

SP_FIELD = "customfield_10202" # story points, as established by experiment

def noNone(s):
    return 0 if s is None else s

def eligibleIssues(includeBugs):
    if includeBugs:
        return 'story, bug, improvement'
    else:
        return 'story'

def runJqlQuery(jql, **kwargs):
    SEARCH_URL = "https://jira.lsstcorp.org/rest/api/2/search"
    return requests.get(SEARCH_URL, params={"jql": jql.format(**kwargs)}).json()

def getEpicEstimatedSps(issue):
    jql = 'id = {id}'
    result = runJqlQuery(jql, id=issue)
    return result['issues'][0]['fields'][SP_FIELD]

def getEpicPlannedSps(issue, includeBugs):
    jql = '"Epic Link" = {id} AND issuetype IN ({types})'
    result = runJqlQuery(jql, id=issue, types=eligibleIssues(includeBugs))
    return sum(noNone(issue['fields'][SP_FIELD]) for issue in result['issues'])

def getEpicCompletedSps(issue, includeBugs):
    jql = '"Epic Link" = {id} AND statusCategory = Complete AND issuetype in ({types})'
    result = runJqlQuery(jql, id=issue, types=eligibleIssues(includeBugs))
    return sum(noNone(issue['fields'][SP_FIELD]) for issue in result['issues'])

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

def printEpic(epic, widths, includeBugs):
    estimated = int(noNone(getEpicEstimatedSps(epic)))
    planned = int(noNone(getEpicPlannedSps(epic, includeBugs)))
    completed = int(noNone(getEpicCompletedSps(epic, includeBugs)))
    template = "{id:>{w1}} {est:>{w2}} {pl:>{w3}} {comp:>{w4}} {del1:>{w5}} {del2:>{w6}}"
    print template.format(id=epic, est=estimated, pl=planned, comp=completed,
                          del1=estimated-planned, del2=planned-completed,
                          w1=widths[0], w2=widths[1], w3=widths[2],
                          w4=widths[3], w5=widths[4], w6=widths[5])

def printEpicStandalone(epic, includeBugs):
    field_widths = printEpicHeader()
    printEpic(epic, field_widths, includeBugs)

def printSummary(wbs, cycle, includeBugs):
    field_widths = printEpicHeader()
    for epic in getEpicsPerWbsAndCycle(wbs, cycle):
        printEpic(epic, field_widths, includeBugs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-bugs", action="store_true")

    subparsers = parser.add_subparsers()

    parser_epic = subparsers.add_parser('epic')
    parser_epic.add_argument('epic')
    parser_epic.set_defaults(func=lambda args: printEpicStandalone(args.epic, args.include_bugs))

    parser_summary = subparsers.add_parser('summary')
    parser_summary.add_argument('wbs')
    parser_summary.add_argument('cycle')
    parser_summary.set_defaults(func=lambda args: printSummary(args.wbs, args.cycle, args.include_bugs))

    args = parser.parse_args()
    args.func(args)
