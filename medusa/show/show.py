# coding=utf-8

from datetime import date

from medusa.exceptions import (
    CantRefreshShowException,
    CantRemoveShowException,
    MultipleShowObjectsException,
)
from medusa.helper.exceptions import ex
from .. import app
from ..common import Quality, SKIPPED, WANTED
from ..db import DBConnection


class Show(object):
    def __init__(self):
        pass

    @staticmethod
    def delete(indexer_id, remove_files=False):
        """
        Try to delete a show
        :param indexer_id: The unique id of the show to delete
        :param remove_files: ``True`` to remove the files associated with the show, ``False`` otherwise
        :return: A tuple containing:
         - an error message if the show could not be deleted, ``None`` otherwise
         - the show object that was deleted, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        if show:
            try:
                app.show_queue_scheduler.action.removeShow(show, bool(remove_files))
            except CantRemoveShowException as exception:
                return ex(exception), show

        return None, show

    @staticmethod
    def find(shows, indexer_id, indexer=None):
        """
        Find a show by its indexer id in the provided list of shows
        :param shows: The list of shows to search in
        :param indexer_id: The indexer id of the desired show
        :param indexer: The indexer to be used
        :return: The desired show if found, ``None`` if not found
        :throw: ``MultipleShowObjectsException`` if multiple shows match the provided ``indexer_id``
        """

        if indexer_id is None or shows is None or len(shows) == 0:
            return None

        indexer_ids = [indexer_id] if not isinstance(indexer_id, list) else indexer_id
        results = [show for show in shows if (indexer is None or show.indexer == indexer) and show.indexerid in indexer_ids]

        if not results:
            return None

        if len(results) == 1:
            return results[0]

        raise MultipleShowObjectsException()

    @staticmethod
    def find_by_id(shows, indexer, show_id):
        """
        Find a show by its indexer id in the provided list of shows
        :param shows: The list of shows to search in
        :param indexer: shows indexer
        :param show_id: The indexers show id of the desired show
        :return: The desired show if found, ``None`` if not found
        :throw: ``MultipleShowObjectsException`` if multiple shows match the provided ``indexer_id``
        """

        if show_id is None or shows is None or len(shows) == 0:
            return None

        # indexer_ids = [show_id] if not isinstance(show_id, list) else show_id
        results = [show for show in shows if show.indexer == int(indexer) and show.indexerid == int(show_id)]

        if not results:
            return None

        if len(results) == 1:
            return results[0]

    @staticmethod
    def overall_stats():
        db = DBConnection()
        shows = app.showList
        today = str(date.today().toordinal())

        downloaded_status = Quality.DOWNLOADED + Quality.ARCHIVED
        snatched_status = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST
        total_status = [SKIPPED, WANTED]

        results = db.select(
            'SELECT airdate, status '
            'FROM tv_episodes '
            'WHERE season > 0 '
            'AND episode > 0 '
            'AND airdate > 1'
        )

        stats = {
            'episodes': {
                'downloaded': 0,
                'snatched': 0,
                'total': 0,
            },
            'shows': {
                'active': len([show for show in shows if show.paused == 0 and show.status == 'Continuing']),
                'total': len(shows),
            },
        }

        for result in results:
            if result['status'] in downloaded_status:
                stats['episodes']['downloaded'] += 1
                stats['episodes']['total'] += 1
            elif result['status'] in snatched_status:
                stats['episodes']['snatched'] += 1
                stats['episodes']['total'] += 1
            elif result['airdate'] <= today and result['status'] in total_status:
                stats['episodes']['total'] += 1

        return stats

    @staticmethod
    def pause(indexer_id, pause=None):
        """
        Change the pause state of a show
        :param indexer_id: The unique id of the show to update
        :param pause: ``True`` to pause the show, ``False`` to resume the show, ``None`` to toggle the pause state
        :return: A tuple containing:
         - an error message if the pause state could not be changed, ``None`` otherwise
         - the show object that was updated, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        if pause is None:
            show.paused = not show.paused
        else:
            show.paused = pause

        show.save_to_db()

        return None, show

    @staticmethod
    def refresh(indexer_id):
        """
        Try to refresh a show
        :param indexer_id: The unique id of the show to refresh
        :return: A tuple containing:
         - an error message if the show could not be refreshed, ``None`` otherwise
         - the show object that was refreshed, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        try:
            app.show_queue_scheduler.action.refreshShow(show)
        except CantRefreshShowException as exception:
            return ex(exception), show

        return None, show

    @staticmethod
    def _validate_indexer_id(indexer_id):
        """
        Check that the provided indexer_id is valid and corresponds with a known show
        :param indexer_id: The indexer id to check
        :return: A tuple containing:
         - an error message if the indexer id is not correct, ``None`` otherwise
         - the show object corresponding to ``indexer_id`` if it exists, ``None`` otherwise
        """

        try:
            indexer_id = int(indexer_id)
        except (TypeError, ValueError):
            return 'Invalid show ID', None

        try:
            show = Show.find(app.showList, indexer_id)
        except MultipleShowObjectsException:
            return 'Unable to find the specified show', None

        return None, show
