# -*- coding: utf-8 -*-

# Copyright(C) 2015      P4ncake
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


from weboob.browser import PagesBrowser, URL

from .pages import SearchPage, PostPage
import urllib


class VineBrowser(PagesBrowser):
    BASEURL = 'https://vine.co'

    search_page = URL(r'/api/posts/search/(?P<pattern>.*)',SearchPage)
    post_page = URL('r/api/timelines/posts/s/(?P<_id>.*)', PostPage)

    def search_videos(self, pattern):
        return self.search_page.go(pattern=urllib.quote_plus(pattern.encode('utf-8'))).iter_videos()

    def get_video(self, _id):
        return self.post_page.go(_id=_id).get_video()
