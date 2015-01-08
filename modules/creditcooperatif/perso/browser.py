# -*- coding: utf-8 -*-

# Copyright(C) 2012 Kevin Pouget
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

from weboob.browser import LoginBrowser, URL, need_login
from weboob.exceptions import BrowserIncorrectPassword

from .pages import LoginPage, CreditLoggedPage, AccountsPage, TransactionsPage, TransactionsJSONPage, ComingTransactionsPage, EncoursCBPage, ComingCBTransactionsPage

try:
    from . import config_perso
except:
    config_perso = None

__all__ = ['CreditCooperatif']


class CreditCooperatif(LoginBrowser):
    BASEURL = "https://www.credit-cooperatif.coop"

    loginpage = URL('/portail//particuliers/login.do', LoginPage)
    loggedpage = URL('/portail/particuliers/authentification.do', CreditLoggedPage)
    accountspage = URL('/portail/particuliers/mescomptes/synthese.do', AccountsPage)
    transactionpage = URL('/portail/particuliers/mescomptes/relevedesoperations.do', TransactionsPage)
    transactjsonpage = URL('/portail/particuliers/mescomptes/relevedesoperationsjson.do', TransactionsJSONPage)
    comingpage = URL('/portail/particuliers/mescomptes/synthese/operationsencourslien.do', ComingTransactionsPage)
    encourscbpage = URL('/portail/particuliers/mescomptes/synthese/encourscblien.do', EncoursCBPage)
    comingcbpage = URL('/portail/particuliers/mescomptes/encourscb/detail.do', ComingCBTransactionsPage)

    def do_login(self):
        """
        Attempt to log in.
        Note: this method does nothing if we are already logged in.
        """
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)

        self.loginpage.stay_or_go()
        self.page.login(self.username, self.password)

        if self.loggedpage.is_here():
            error = self.page.get_error()
            if error is None:
                return

        raise BrowserIncorrectPassword(error)

    @need_login
    def get_accounts_list(self):
        accounts = []
        self.accountspage.stay_or_go()

        for account in self.page.get_list():
            accounts.append(account)

            data = {'accountExternalNumber': account.id}
            
            if int(account._has_encours) != 0:
                self.comingpage.go(data=data)
                account.coming = sum([coming_tr.amount for coming_tr 
                                      in self.page.get_transactions()])
            
            if len(account._has_cb) != 0:
                self.encourscbpage.go(data=data)
                accounts += self.page.get_list()

        if config_perso is not None:
            for account in accounts:
                if config_perso.RENAME.has_key(account.id):
                   account.label = config_perso.RENAME[account.id]
                
        return accounts
        
        

    @need_login
    def get_history(self, account):
        if account._credit_card_account:
            return []
        
        data = {'accountExternalNumber': account.id}

        self.transactionpage.go(data=data)
        
        data = {'iDisplayLength':  400,
                'iDisplayStart':   0,
                'iSortCol_0':      0,
                'iSortingCols':    1,
                'sColumns':        '',
                'sEcho':           1,
                'sSortDir_0':      'asc',
                }
        self.transactjsonpage.go(data=data)
        
        return self.page.get_transactions()

    @need_login
    def get_coming(self, account):
        if not account._credit_card_account:
            data = {'accountExternalNumber': account.id}
            self.comingpage.go(data=data)
            assert self.comingpage.is_here()
        else:
            data = {'accountExternalNumber': "41011070318"}
            self.encourscbpage.go(data=data)
            data = {'numero': account.id}
            self.comingcbpage.go(data=data)
            
        return self.page.get_transactions()
