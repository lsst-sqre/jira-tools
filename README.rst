=================
LSST JIRA Queries
=================

Requires Python 2.7.x, Requests_.

.. _Requests: http://docs.python-requests.org/en/latest/

Get details including a breakdown of assignees for a single epic::

   $ ./jira.py epic DM-1101
           Estimated Planned Completed   Delta     Delta
                                       (Est-Pla) (Pla-Cmp)
   DM-1101        51      55        45        -4        10
                          14         5 Developer X
                          41        26 Developer Y

Get a summary of all epics for a given WBS and cycle::

   $ ./jira.py summary 02C.04 --cycle="Winter 2015"
           Estimated Planned Completed   Delta     Delta
                                       (Est-Pla) (Pla-Cmp)
     DM-85        31      31         0         0        31
   DM-1074        20      11         1         9        10
   [etc]

The summary will also print the number of story points estimated per user if
and only if the epic descriptions contain a line formatted like::

   Breakdown: ${username1} XX%; ${username2} YY%

No attempt is currently made to ensure the percentages sum to 100, or that the
usernames are valid.

Note that the WBS matches anything beginning with the string given; thus,
``02C.04`` retrieves epics with a WBS of ``02C.04.01``, ``02C.04.02``, etc.
Specifying the cycle is optional: if not set, all epics will be shown
regardless of cycle.

By default, only issues of type "story" are counted when calculating planned
and completed story points. To include other issue types (bug, improvement),
use the ``--all-issues`` command line option.

In general, we assume that setting an issue to a status of "Won't Fix" is
equivalent to deleting it: such issues are excluded from counts of planned or
completed story points. The ``--wontfix-is-done`` command line option changes
this so that issues marked as "Won't Fix" are counted in exactly the same way
as issues marked as done.
