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


from weboob.tools.backend import BaseBackend
from weboob.capabilities.calendar import ICapCalendarEvent
import itertools

from .browser import BiplanBrowser
from.calendar import BiplanCalendarEvent

__all__ = ['BiplanBackend']


class BiplanBackend(BaseBackend, ICapCalendarEvent):
    NAME = 'biplan'
    DESCRIPTION = u'lebiplan.org website'
    MAINTAINER = u'Bezleputh'
    EMAIL = 'carton_ben@yahoo.fr'
    LICENSE = 'AGPLv3+'
    VERSION = '0.h'

    BROWSER = BiplanBrowser

    def list_events(self, date_from, date_to=None):
        with self.browser:
            return itertools.chain(self.browser.list_events_concert(date_from, date_to),
                                   self.browser.list_events_theatre(date_from, date_to))

    def get_event(self, _id, event=None):
        with self.browser:
            return self.browser.get_event(_id, event)

    def fill_obj(self, event, fields):
        self.get_event(event.id, event)

    OBJECTS = {BiplanCalendarEvent: fill_obj}