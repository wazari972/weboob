# -*- coding: utf-8 -*-

# Copyright(C) 2010  Romain Bignon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


from __future__ import with_statement

from weboob.capabilities.content import ICapContent, Content
from weboob.tools.backend import BaseBackend

from .browser import RedmineBrowser


__all__ = ['RedmineBackend']


class RedmineBackend(BaseBackend, ICapContent):
    NAME = 'redmine'
    MAINTAINER = 'Romain Bignon'
    EMAIL = 'romain@peerfuse.org'
    VERSION = '0.3'
    DESCRIPTION = 'The Redmine project management web application'
    LICENSE = 'GPLv3'
    CONFIG = {'url':      BaseBackend.ConfigField(description='URL of the Redmine'),
              'username': BaseBackend.ConfigField(description='Login'),
              'password': BaseBackend.ConfigField(description='Password', is_masked=True),
             }
    BROWSER = RedmineBrowser

    def create_default_browser(self):
        return self.create_browser(self.config['url'], self.config['username'], self.config['password'])

    def id2path(self, id):
        return id.split('/', 2)

    def get_content(self, id):
        if isinstance(id, basestring):
            content = Content(id)
        else:
            content = id
            id = content.id

        try:
            project, _type, page = self.id2path(id)
        except ValueError:
            return None

        with self.browser:
            data = self.browser.get_wiki_source(project, page)

        content.content = data
        return content

    def push_content(self, content, message=None):
        try:
            project, _type, page = self.id2path(content.id)
        except ValueError:
            return

        with self.browser:
            return self.browser.set_wiki_source(project, page, content.content, message)
