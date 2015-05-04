# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Christophe Benz
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

from weboob.capabilities.base import enum
from weboob.capabilities.video import BaseVideo

FORMATS = enum(HTTP_MP4=u'HBBTV', HLS=u'M3U8', RTMP=u'RTMP', HLS_MOBILE=u'MOBILE')

LANG = enum(FRENCH={u'label': u'French', u'webservice': u'F', u'site': u'fr', u'version': u'1', u'title': u'titleFR'},
            GERMAN={u'label': u'German', u'webservice': u'D', u'site': u'de', u'version': u'1', u'title': u'titleDE'})

SITE = enum(PROGRAM={u'id': u'program', u'label': u'Arte Programs', 1: 'get_arte_programs',
                     2: 'get_arte_program_videos', u'video': 'get_video_from_program_id'},
            CONCERT={u'id': u'concert', u'label': u'Arte Concert videos', 1: 'get_arte_concert_categories',
                     2: 'get_arte_concert_videos', 'video': 'get_arte_concert_video'},
            CINEMA={u'id': u'cinema', u'label': u'Arte Cinema', 1: 'get_arte_cinema_categories',
                    2: 'get_arte_cinema_categories', 3: 'get_arte_cinema_videos', 'video': 'get_arte_cinema_video'})

QUALITY = enum(HD=u'SQ', MD=u'EQ', SD=u'MQ', LD=u'LQ')

VERSION_VIDEO = enum(VOSTA={u'label': u'Original version subtitled (German)', LANG.GERMAN.get('label'): u'3'},
                     VOSTF={u'label': u'Original version subtitled (French)', LANG.FRENCH.get('label'): u'3'},
                     VASTA={u'label': u'Translated version (German)',
                            LANG.GERMAN.get('label'): u'1', LANG.FRENCH.get('label'): u'2'},
                     VFSTF={u'label': u'Translated version (French)',
                            LANG.FRENCH.get('label'): u'1', LANG.GERMAN.get('label'): u'2'},
                     VASTMA={u'label': u'Deaf version (German)', LANG.GERMAN.get('label'): u'8'},
                     VFSTMF={u'label': u'Deaf version (French)', LANG.FRENCH.get('label'): u'8'})


class ArteVideo(BaseVideo):
    pass


class ArteSiteVideo(BaseVideo):
    pass
