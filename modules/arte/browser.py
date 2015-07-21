# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.

import re

from weboob.capabilities.collection import Collection
from weboob.capabilities.base import UserError
from weboob.capabilities import NotAvailable

from weboob.browser import PagesBrowser, URL
from .pages import VideosListPage, VideoPage, ArteJsonPage
from .video import VERSION_VIDEO, LANG, QUALITY, FORMATS, SITE


__all__ = ['ArteBrowser']


class ArteBrowser(PagesBrowser):
    BASEURL = 'http://arte.tv/'

    webservice = URL('papi/tvguide/(?P<class_name>.*)/(?P<method_name>.*)/(?P<parameters>.*).json',
                     'http://(?P<__site>.*).arte.tv/(?P<_lang>\w{2})/player/(?P<_id>.*)',
                     'https://api.arte.tv/api/player/v1/config/(?P<__lang>\w{2})/(?P<vid>.*)\?vector=(?P<___site>.*)',
                     ArteJsonPage)
    videos_list = URL('http://(?P<site>.*).arte.tv/(?P<lang>\w{2})/?(?P<cat>.*?)', VideosListPage)
    video_page = URL('http://(?P<_site>.*).arte.tv/(?P<id>.+)', VideoPage)

    def __init__(self, lang, quality, order, format, version, *args, **kwargs):
        self.order = order
        self.lang = (value for key, value in LANG.items if key == lang).next()
        self.version = (value for key, value in VERSION_VIDEO.items
                        if self.lang.get('label') in value.keys() and version == key).next()
        self.quality = (value for key, value in QUALITY.items if key == quality).next()
        self.format = format

        if self.lang.get('label') not in self.version.keys():
            raise UserError('%s is not available for %s' % (self.lang.get('label'), version))

        PagesBrowser.__init__(self, *args, **kwargs)

    def search_videos(self, pattern):
        class_name = 'videos/plus7'
        method_name = 'search'
        parameters = '/'.join([self.lang.get('webservice'), 'L1', pattern, 'ALL', 'ALL', '-1',
                               self.order, '10', '0'])
        return self.webservice.go(class_name=class_name, method_name=method_name, parameters=parameters).iter_videos()

    def get_video(self, id, video=None):
        class_name = 'videos'
        method_name = 'stream/player'
        parameters = '/'.join([self.lang.get('webservice'), id, 'ALL', 'ALL'])
        video = self.webservice.go(class_name=class_name,
                                   method_name=method_name,
                                   parameters=parameters).get_video(obj=video)
        video.ext, video.url = self.get_url()
        return video

    def get_url(self):
        url = self.page.get_video_url(self.quality, self.format, self.version.get(self.lang.get('label')),
                                      self.lang.get('version'))
        if format == FORMATS.HLS:
            ext = u'm3u8'
            url = self.get_m3u8_link(url)
        else:
            ext = u'mp4'
            url = url
        return ext, url

    def get_m3u8_link(self, url):
        r = self.openurl(url)
        baseurl = url.rpartition('/')[0]

        links_by_quality = []
        for line in r.readlines():
            if not line.startswith('#'):
                links_by_quality.append(u'%s/%s' % (baseurl, line.replace('\n', '')))

        if len(links_by_quality):
            try:
                return links_by_quality[self.quality[1]]
            except:
                return links_by_quality[0]
        return NotAvailable

    def get_video_from_program_id(self, _id):
        class_name = 'epg'
        method_name = 'program'
        parameters = '/'.join([self.lang.get('webservice'), 'L2', _id])
        video = self.webservice.go(class_name=class_name, method_name=method_name,
                                   parameters=parameters).get_program_video()
        if video:
            return self.get_video(video.id, video)

    def latest_videos(self):
        class_name = 'videos'
        method_name = 'plus7'
        parameters = '/'.join([self.lang.get('webservice'), 'L1', 'ALL', 'ALL', '-1', self.order, '10', '0'])
        return self.webservice.go(class_name=class_name, method_name=method_name, parameters=parameters).iter_videos()

    def get_arte_programs(self):
        class_name = 'epg'
        method_name = 'clusters'
        parameters = '/'.join([self.lang.get('webservice'), '0', 'ALL'])
        return self.webservice.go(class_name=class_name, method_name=method_name,
                                  parameters=parameters).iter_programs(title=self.lang.get('title'))

    def get_arte_program_videos(self, program):
        class_name = 'epg'
        method_name = 'cluster'
        parameters = '/'.join([self.lang.get('webservice'), program[-1]])
        available_videos = self.webservice.go(class_name=class_name, method_name=method_name,
                                              parameters=parameters).iter_program_videos()
        for item in available_videos:
            video = self.get_video_from_program_id(item.id)
            if video:
                yield video

    def get_arte_concert_categories(self):
        return self.videos_list.go(site=SITE.CONCERT.get('id'), lang=self.lang.get('site'),
                                   cat='').iter_arte_concert_categories()

    def get_arte_concert_videos(self, cat):
        return self.videos_list.go(site=SITE.CONCERT.get('id'), lang=self.lang.get('site'),
                                   cat='').iter_arte_concert_videos(cat=cat[-1])

    def get_arte_concert_video(self, id, video=None):
        json_url = self.video_page.go(_site=SITE.CONCERT.get('id'), id=id).get_json_url()
        m = re.search('http://(?P<__site>.*).arte.tv/(?P<_lang>\w{2})/player/(?P<_id>.*)', json_url)
        if m:
            video = self.webservice.go(__site=m.group('__site'), _lang=m.group('_lang'),
                                       _id=m.group('_id')).get_arte_concert_video(obj=video)
            video.id = u'%s.%s' % (video._site, id)
            video.ext, video.url = self.get_url()
            return video

    def get_arte_cinema_categories(self, cat=[]):
        menu = self.videos_list.go(site=SITE.CINEMA.get('id'), lang=self.lang.get('site'),
                                   cat='').get_arte_cinema_menu()

        menuSplit = map(lambda x: x.split("/")[2:], menu)

        result = {}
        for record in menuSplit:
            here = result
            for item in record[:-1]:
                if item not in here:
                    here[item] = {}
                here = here[item]
            if "end" not in here:
                here["end"] = []
            here["end"].append(record[-1])

        cat = cat if not cat else cat[1:]

        for el in cat:
            result = result.get(el)

        if "end" in result.keys():
            return self.page.iter_arte_cinema_categories(cat='/'.join(cat))
        else:
            categories = []
            for item in result.keys():
                categories.append(Collection([SITE.CINEMA.get('id'), unicode(item)], unicode(item)))
            return categories

    def get_arte_cinema_videos(self, cat):
        return self.videos_list.go(site=SITE.CINEMA.get('id'), lang=self.lang.get('site'),
                                   cat='/%s' % '/'.join(cat[1:])).get_arte_cinema_videos()

    def get_arte_cinema_video(self, id, video=None):
        json_url = self.video_page.go(_site=SITE.CINEMA.get('id'), id=id).get_json_url()
        m = re.search('https://api.arte.tv/api/player/v1/config/(\w{2})/(.*)\?vector=(.*)\&.*', json_url)
        if m:
            video = self.webservice.go(__lang=m.group(1),
                                       vid=m.group(2), ___site=m.group(3)).get_arte_cinema_video(obj=video)
            video.ext, video.url = self.get_url()
            video.id = id
            return video
