# coding=utf-8
# Author: miigotu <miigotu@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import datetime
from urllib import quote_plus

import sickbeard
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import db
from sickbeard import classes
from sickbeard.common import Quality
from sickbeard.providers import generic

class BitCannonProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "BitCannon")

        self.supportsBacklog = True
        self.public = True

        self.enabled = False
        self.minseed = None
        self.minleech = None
        self.ratio = 0

        self.cache = BitCannonCache(self)

        self.url = 'http://127.0.0.1:1337/'
        self.urls = {
            'base_url': self.url,
            'search': self.url + 'search/',
            'trackers': self.url + 'stats',
        }

    def isEnabled(self):
        return self.enabled

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        trackers = (self.getURL(self.urls['trackers'], json=True) or {}).get(u'Trackers', [])
        if not trackers:
            logger.log(u'Could not get tracker list from BitCannon, aborting search')
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                searchURL = self.urls['search'] + search_string
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                data = self.getURL(searchURL, json=True)
                for item in data or []:
                    if 'tv' not in (item.get('Category') or u'').lower():
                        continue

                    title = item.get(u'Title', u'')
                    info_hash = item.get(u'Btih', u'')
                    if not all([title, info_hash]):
                        continue

                    swarm = item.get(u'Swarm', {})
                    seeders = swarm.get(u'Seeders', 0)
                    leechers = swarm.get(u'Leechers', 0)
                    size = item.get(u'Size', -1)

                    #Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    # Only build the url if we selected it
                    download_url = u'magnet:?xt=urn:btih:%s&dn=%s&tr=%s' % (info_hash, quote_plus(title.encode('utf-8')).decode('utf-8'), u'&tr='.join([quote_plus(x.encode('utf-8')).decode('utf-8') for x in trackers]))

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                    items[mode].append(item)

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def findPropers(self, search_date=datetime.datetime.today()-datetime.timedelta(days=1)):
        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate, s.indexer FROM tv_episodes AS e' +
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
            ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        for sqlshow in sqlResults or []:
            show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if show:
                curEp = show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

                searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(searchStrings[0]):
                    title, url = self._get_title_and_url(item)
                    pubdate = item[6]

                    results.append(classes.Proper(title, url, pubdate, show))

        return results

    def seedRatio(self):
        return self.ratio


class BitCannonCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        return {'entries': []}
        #search_params = {'RSS': ['']}
        #return {'entries': self.provider._doSearch(search_params)}

provider = BitCannonProvider()
