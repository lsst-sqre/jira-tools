import argparse
import sys
import requests

SP_FIELD = "customfield_10202" # story points, as established by experiment

def noNone(s):
    return 0 if s is None else s

def eligibleIssues(include_bugs):
    if include_bugs:
        return "story, bug, improvement"
    else:
        return "story"

def runJqlQuery(jql):
    SEARCH_URL = "https://jira.lsstcorp.org/rest/api/2/search"
    return requests.get(SEARCH_URL, params={"jql": jql}).json()

def getEpicEstimatedSps(issue):
    jql = "id = %s" % (issue,)
    result = runJqlQuery(jql)
    return result['issues'][0]['fields'][SP_FIELD]

def getEpicPlannedSps(issue, include_bugs):
    jql = "\"Epic Link\" = %s AND issuetype IN (%s)" % (issue, eligibleIssues(include_bugs))
    result = runJqlQuery(jql)
    return sum(noNone(issue['fields'][SP_FIELD]) for issue in result['issues'])

def getEpicCompletedSps(issue, include_bugs):
    jql = "\"Epic Link\" = %s AND statusCategory = Complete AND issuetype in (%s)" % (issue, eligibleIssues(include_bugs))
    result = runJqlQuery(jql)
    return sum(noNone(issue['fields'][SP_FIELD]) for issue in result['issues'])

def getEpicsPerWbsAndCycle(wbs, cycle):
    jql = "issuetype = Epic AND cycle = \"%s\" AND WBS ~ \"%s*\" ORDER BY Id" % (cycle, wbs)
    result = runJqlQuery(jql)
    return [issue['key'] for issue in result['issues']]

def printEpicHeader():
    print "         Estimated Planned Completed   Delta     Delta"
    print "                                     (Est-Pla) (Pla-Cmp)"

def printEpic(epic, include_bugs):
    estimated = int(noNone(getEpicEstimatedSps(epic)))
    planned = int(noNone(getEpicPlannedSps(epic, include_bugs)))
    completed = int(noNone(getEpicCompletedSps(epic, include_bugs)))
    template = "{id:>7}: {est:>{est_width}} {pl:>{pl_width}} {comp:>{comp_width}} {del1:>9} {del2:>9}"
    print template.format(id=epic, est=estimated, pl=planned, comp=completed,
                          del1=estimated-planned, del2=planned-completed,
                          est_width=len("Estimated"), pl_width=len("Planned"), comp_width=len("Completed"))

def printEpicStandalone(epic, include_bugs):
    printEpicHeader()
    printEpic(epic, include_bugs)

def printSummary(wbs, cycle, include_bugs):
    printEpicHeader()
    for epic in getEpicsPerWbsAndCycle(wbs, cycle):
        printEpic(epic, include_bugs)

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
