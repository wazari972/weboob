# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
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


from urlparse import urlsplit

from weboob.tools.browser import BaseBrowser, BrowserIncorrectPassword

from .pages import LoginPage, IndexPage, ErrorPage, UnavailablePage


__all__ = ['CaisseEpargne']


class CaisseEpargne(BaseBrowser):
    DOMAIN = 'www.caisse-epargne.fr'
    PROTOCOL = 'https'
    CERTHASH = ['165faeb5bd1bad22bf52029e3c09bf540199402a1fa70aa19e9d5f92d562ff69', 'dfff27d6db1fcdf1cea3ab8e3c1ca4f97c971262e95be49f3385b40c97fe640c']
    PAGES = {'https://[^/]+.caisse-epargne.fr/particuliers/ind_pauthpopup.aspx.*':          LoginPage,
             'https://[^/]+.caisse-epargne.fr/Portail.aspx':                                IndexPage,
             'https://[^/]+.caisse-epargne.fr/login.aspx':                                  ErrorPage,
             'https://[^/]+.caisse-epargne.fr/page_hs_dei_.*.aspx':                         UnavailablePage,
            }

    def is_logged(self):
        return self.page is not None and not self.is_on_page(LoginPage)

    def home(self):
        if self.is_logged():
            self.location(self.buildurl('/Portail.aspx'))
        else:
            self.login()

    def login(self):
        """
        Attempt to log in.
        Note: this method does nothing if we are already logged in.
        """
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)

        if self.is_logged():
            return

        if not self.is_on_page(LoginPage):
            self.location('https://www.caisse-epargne.fr/particuliers/ind_pauthpopup.aspx?mar=101&reg=&fctpopup=auth&cv=0', no_login=True)

        self.page.login(self.username)
        self.page.login2()
        self.page.login3(self.password)

        if not self.is_logged():
            raise BrowserIncorrectPassword()

        v = urlsplit(self.page.url)
        self.DOMAIN = v.netloc

    def get_accounts_list(self):
        self.location(self.buildurl('/Portail.aspx'))

        return self.page.get_list()

    def get_account(self, id):
        assert isinstance(id, basestring)

        l = self.get_accounts_list()
        for a in l:
            if a.id == id:
                return a

        return None

    def _get_history(self, link_type, id):
        self.location(self.buildurl('/Portail.aspx'))

        self.page.go_history(link_type, id)

        while 1:
            assert self.is_on_page(IndexPage)

            for tr in self.page.get_history():
                yield tr

            if not self.page.go_next():
                return

    def get_history(self, account):
        return self._get_history(account._link_type, account.id)

    def get_coming(self, account):
        for link_type, id in account._card_links:
            for tr in self._get_history(link_type, id):
                yield tr
