from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ray


class FilterManager(object):
    """Manages filters and coordination across remote evaluators that expose
        `get_filters` and `sync_filters`.
    """

    @staticmethod
    def synchronize(local_filters, remotes, update_remote=True):
        """Aggregates all filters from remote evaluators.

        Local copy is updated and then broadcasted to all remote evaluators.

        Args:
            local_filters (dict): Filters to be synchronized.
            remotes (list): Remote evaluators with filters.
            update_remote (bool): Whether to push updates to remote filters.
        """
        remote_filters = ray.get(
            [r.get_filters.remote(flush_after=True) for r in remotes])
        for rf in remote_filters:
            for k in local_filters:
                local_filters[k].apply_changes(rf[k], with_buffer=False)
        if update_remote:
            copies = {k: v.as_serializable() for k, v in local_filters.items()}
            remote_copy = ray.put(copies)
            [r.sync_filters.remote(remote_copy) for r in remotes]
