# -*- coding: utf-8 -*-

# Copyright(C) 2013      Bezleputh
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

from weboob.browser.elements import ItemElement, DictElement, ListElement, method
from weboob.browser.pages import HTMLPage, JsonPage, XMLPage
from weboob.browser.filters.json import Dict
from weboob.browser.filters.standard import Format, CleanText, Join, Env, Regexp, Duration
from weboob.capabilities.audio import BaseAudio
from weboob.tools.capabilities.audio.audio import BaseAudioIdFilter
from weboob.capabilities.image import BaseImage
from weboob.capabilities.collection import Collection

import time
from datetime import timedelta


class PodcastPage(XMLPage):
    @method
    class iter_podcasts(ListElement):
        item_xpath = '//item'

        class item(ItemElement):
            klass = BaseAudio

            obj_id = BaseAudioIdFilter(Format('podcast.%s',
                                              Regexp(CleanText('./guid'),
                                                     'http://media.radiofrance-podcast.net/podcast09/(.*).mp3')))
            obj_title = CleanText('title')
            obj_format = u'mp3'
            obj_url = CleanText('enclosure/@url')
            obj_description = CleanText('description')

            def obj_author(self):
                author = self.el.xpath('itunes:author',
                                       namespaces={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
                return CleanText('.')(author[0])

            def obj_duration(self):
                duration = self.el.xpath('itunes:duration',
                                         namespaces={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
                return Duration(CleanText('.'))(duration[0])

            def obj_thumbnail(self):
                thumbnail = BaseImage(CleanText('//image[1]/url')(self))
                thumbnail.url = thumbnail.id
                return thumbnail


class RadioPage(HTMLPage):
    def get_url(self):
        return CleanText('//a[@id="player"][1]/@href')(self.doc)

    def get_france_culture_podcasts_url(self):
        return Regexp(CleanText('//a[@class="lien-rss"][1]/@href'),
                      'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self.doc)

    @method
    class get_france_culture_podcast_emissions(ListElement):
        item_xpath = '//li/h3/a'
        ignore_duplicate = True

        class item(ItemElement):
            klass = Collection

            def condition(self):
                return u'/podcast/' in CleanText('./@href')(self)

            def obj_split_path(self):
                _id = Regexp(CleanText('./@href'), '/podcast/(.*)')(self)
                self.env['split_path'].append(_id)
                return self.env['split_path']

            obj_id = Regexp(CleanText('./@href'), '/podcast/(.*)')
            obj_title = CleanText('.')

    @method
    class get_france_info_podcast_emissions(ListElement):
        item_xpath = '//div[@class="emission-gdp"]'
        ignore_duplicate = True

        class item(ItemElement):
            klass = Collection

            def obj_split_path(self):
                _id = Regexp(CleanText('./div/div/div/div/ul/li/a[@class="ico-rss"]/@href'),
                             'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self)
                self.env['split_path'].append(_id)
                return self.env['split_path']

            obj_id = Regexp(CleanText('./div/div/div/div/ul/li/a[@class="ico-rss"]/@href'),
                            'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')
            obj_title = CleanText('./h2/a')

    @method
    class get_mouv_podcast_emissions(ListElement):
        item_xpath = '//div[@class="view-content"]/div'
        ignore_duplicate = True

        class item(ItemElement):
            klass = Collection

            def condition(self):
                return CleanText('./div/a[@class="podcast-rss"]/@href')(self) and \
                    Regexp(CleanText('./div/a[@class="podcast-rss"]/@href'),
                           'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self)

            def obj_split_path(self):
                _id = Regexp(CleanText('./div/a[@class="podcast-rss"]/@href'),
                             'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self)
                self.env['split_path'].append(_id)
                return self.env['split_path']

            obj_id = Regexp(CleanText('./div/a[@class="podcast-rss"]/@href'),
                            'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')
            obj_title = CleanText('./h2')

    @method
    class get_france_musique_podcast_emissions(ListElement):
        item_xpath = '//div[@class="liste-emissions"]/ul/li'
        ignore_duplicate = True

        class item(ItemElement):
            klass = Collection

            def condition(self):
                return CleanText('./div/ul/li/a[@class="ico-rss"]/@href')(self) and\
                    Regexp(CleanText('./div/ul/li/a[@class="ico-rss"]/@href'),
                           'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self)

            def obj_split_path(self):
                _id = Regexp(CleanText('./div/ul/li/a[@class="ico-rss"]/@href'),
                             'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self)
                self.env['split_path'].append(_id)
                return self.env['split_path']

            obj_id = Regexp(CleanText('./div/ul/li/a[@class="ico-rss"]/@href'),
                            'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')
            obj_title = CleanText('./div/h3')

    @method
    class get_france_inter_podcast_emissions(ListElement):
        item_xpath = '//div[has-class("item-list")]/ul/li/div/div'
        ignore_duplicate = True

        class item(ItemElement):
            klass = Collection

            def condition(self):
                return CleanText('./div/a[@class="podrss"]/@href')(self) and\
                    Regexp(CleanText('./div/a[@class="podrss"]/@href'),
                           'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self)

            def obj_split_path(self):
                _id = Regexp(CleanText('./div/a[@class="podrss"]/@href'),
                             'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')(self)
                self.env['split_path'].append(_id)
                return self.env['split_path']

            obj_id = Regexp(CleanText('./div/a[@class="podrss"]/@href'),
                            'http://radiofrance-podcast.net/podcast09/rss_(.*).xml')
            obj_title = CleanText('./h2/a')


class JsonPage(JsonPage):
    @method
    class get_selection(DictElement):
        item_xpath = 'diffusions'
        ignore_duplicate = True

        class item(ItemElement):
            klass = BaseAudio

            def condition(self):
                return Dict('path_mp3')(self)

            obj_id = BaseAudioIdFilter(Format(u'%s.%s', Env('radio_id'), Dict('nid')))
            obj_format = u'mp3'
            obj_title = Format(u'%s : %s',
                               Dict('title_emission'),
                               Dict('title_diff'))
            obj_description = Dict('desc_emission', default=u'')

            obj_author = Join(u', ', Dict('personnes', default=u''))
            obj_url = Dict('path_mp3')

            def obj_thumbnail(self):
                if 'path_img_emission' in self.el:
                    thumbnail = BaseImage(Dict('path_img_emission')(self))
                    thumbnail.url = thumbnail.id
                    return thumbnail

            def obj_duration(self):
                fin = Dict('fin')(self)
                debut = Dict('debut')(self)
                if debut and fin:
                    return timedelta(seconds=int(fin) - int(debut))

    def get_current(self):
        if 'current' in self.doc:
            emission_title = self.doc['current']['emission']['titre']
            song_title = self.doc['current']['song']['titre']
            title = u'%s: %s' % (emission_title, song_title)
            person = self.doc['current']['song']['interpreteMorceau']
            return person, title
        elif 'diffusions' in self.doc:
            now = int(time.time())
            for item in self.doc['diffusions']:
                if item['debut'] < now and item['fin'] > now:
                    title = u'%s: %s' % (item['title_emission'], item['title_diff'])
                    person = u''
                    return person, title
            return u'', u''
        else:
            now = int(time.time())
            for item in self.doc:
                if int(item['debut']) < now and int(item['fin']) > now:
                    emission = u''
                    if 'diffusions' in item and item['diffusions'] and 'title' in item['diffusions'][0]:
                        emission = item['diffusions'][0]['title']

                    title = item['title_emission']
                    if emission:
                        title = u'%s: %s' % (title, emission)

                    person = u''
                    if 'personnes' in item and item['personnes'] and item['personnes'][0]:
                        person = u','.join(item['personnes'])
                    return person, title
            return u'', u''
