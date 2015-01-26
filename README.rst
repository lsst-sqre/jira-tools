=================
LSST JIRA Queries
=================

Requires Python 2.7.x, Requests_.

.. _Requests: http://docs.python-requests.org/en/latest/

Get details for a single epic::

   $ ./jira.py epic DM-1101
           Estimated Planned Completed   Delta     Delta
                                       (Est-Pla) (Pla-Cmp)
   DM-1101        51      55        45        -4        10

Get a summary of all epics for a given WBS and cycle::

   $ ./jira.py summary 02C.04 "Winter 2015"
           Estimated Planned Completed   Delta     Delta
                                       (Est-Pla) (Pla-Cmp)
     DM-85        31      31         0         0        31
   DM-1074        20      11         1         9        10
   [etc]

Note that the WBS matches anything beginning with the string given; thus,
``02C.04`` retrieves epics with a WBS of ``02C.04.01``, ``02C.04.02``, etc.

By default, only issues of type "story" are counted when calculating planned
and completed story points. To include other issue types (bug, improvement),
use the ``--all-issuess`` command line option.
