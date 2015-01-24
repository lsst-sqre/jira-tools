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

def printEpic(epic, include_bugs):
    estimated = noNone(getEpicEstimatedSps(epic))
    planned = noNone(getEpicPlannedSps(epic, include_bugs))
    completed = noNone(getEpicCompletedSps(epic, include_bugs))
    print "Epic %s -- Estimated: %d, " % (epic, estimated),
    print "Planned: %d, Completed: %d, " % (planned, completed),
    print "Delta (Estimated-Planned): %d (%.1f%%), " % (estimated - planned, abs(100.0 * estimated - planned)/planned),
    print "Delta (Planned-Completed): %d (%.1f%%)" % (planned - completed, abs(100.0 * planned-completed)/planned)

def summarizeWbsAndCycle(wbs, cycle, include_bugs):
    for epic in getEpicsPerWbsAndCycle(wbs, cycle):
        printEpic(epic, include_bugs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-bugs", action="store_true")

    subparsers = parser.add_subparsers()

    parser_epic = subparsers.add_parser('epic')
    parser_epic.add_argument('epic')
    parser_epic.set_defaults(func=lambda args: printEpic(args.epic, args.include_bugs))

    parser_wbs = subparsers.add_parser('wbs')
    parser_wbs.add_argument('wbs')
    parser_wbs.add_argument('cycle')
    parser_wbs.set_defaults(func=lambda args: summarizeWbsAndCycle(args.wbs, args.cycle, args.include_bugs))

    args = parser.parse_args()
    args.func(args)
