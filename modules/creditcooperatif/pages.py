# -*- coding: utf-8 -*-

# Copyright(C) 2012 Kevin Pouget, based on Romain Bignon work
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


from urlparse import urlsplit, parse_qsl
from decimal import Decimal
import re

from weboob.tools.browser import BasePage
from weboob.capabilities.bank import Account
from weboob.tools.capabilities.bank.transactions import FrenchTransaction


__all__ = ['LoginPage', 'AccountsPage']


class UnavailablePage(BasePage):
    def on_loaded(self):
        a = self.document.xpath('//a[@class="btn"]')[0]
        self.browser.location(a.attrib['href'])

class LoginPage(BasePage):
    def login(self, login, passwd):
        self.browser.select_form(name='loginCoForm')
        self.browser['codeUtil'] = login
        self.browser['motPasse'] = passwd
        self.browser.submit(nologin=True)

class AccountsPage(BasePage):
    ACCOUNT_TYPES = {u'COMPTE NEF':                Account.TYPE_CHECKING
                    }
    CPT_ROW_ID = 0
    CPT_ROW_NAME = 1
    CPT_ROW_NATURE = 2
    CPT_ROW_BALANCE = 3
    CPT_ROW_ENCOURS = 4
    
    def is_error(self):
        for script in self.document.xpath('//script'):
            if script.text is not None and u"Le service est momentanément indisponible" in script.text:
                return True

        return False

    def get_list(self):
        for tbCompte in self.document.xpath('//table[@id="compte"]'):
            for trCompte in tbCompte.xpath('.//tbody/tr'):
                tds = tr.findall('td')

                account = Account()
                
                account.id = tds[CPT_ROW_ID].text()
                account.label = tds[CPT_ROW_NAME].text()

                account_type_str = "".join([td.text() for td in tds[CPT_ROW_ID].xpath('.//td[@id="tx"]')]).strip()

                account.type = ACCOUNT_TYPES.get(account_type_str,  Account.TYPE_UNKNOWN)

                balance_link = tds[CPT_ROW_BALANCE].find("a")
                
                account.balance = Decimal(FrenchTransaction.clean_amount(blance_link.text()))

                yield account

        return

class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^RET DAB (?P<text>.*?) RETRAIT DU (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}).*'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^RET DAB (?P<text>.*?) CARTE ?:.*'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^(?P<text>.*) RETRAIT DU (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) .*'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('(\w+) (?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2}) CB:[^ ]+ (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_CARD),
                (re.compile('^VIR(EMENT)? (?P<text>.*)'),   FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^PRLV (?P<text>.*)'),          FrenchTransaction.TYPE_ORDER),
                (re.compile('^CHEQUE.*'),                   FrenchTransaction.TYPE_CHECK),
                (re.compile('^(AGIOS /|FRAIS) (?P<text>.*)'),       FrenchTransaction.TYPE_BANK),
                (re.compile('^(CONVENTION \d+ )?COTIS(ATION)? (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_BANK),
                (re.compile('^REMISE (?P<text>.*)'),        FrenchTransaction.TYPE_DEPOSIT),
                (re.compile('^(?P<text>.*)( \d+)? QUITTANCE .*'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^.* LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2})$'),
                                                            FrenchTransaction.TYPE_UNKNOWN),
               ]


class TransactionsPage(BasePage):
    def get_next_params(self):
        if len(self.document.xpath('//li[@id="tbl1_nxt"]')) == 0:
            return None

        params = {}
        for field in self.document.xpath('//input'):
            params[field.attrib['name']] = field.attrib.get('value', '')

        params['validationStrategy'] = 'NV'
        params['pagingDirection'] = 'NEXT'
        params['pagerName'] = 'tbl1'

        return params

    def get_history(self):
        for tr in self.document.xpath('//table[@id="tbl1"]/tbody/tr'):
            tds = tr.findall('td')

            t = Transaction(tr.attrib['id'].split('_', 1)[1])

            date = u''.join([txt.strip() for txt in tds[4].itertext()])
            raw = u' '.join([txt.strip() for txt in tds[1].itertext()])
            debit = u''.join([txt.strip() for txt in tds[-2].itertext()])
            credit = u''.join([txt.strip() for txt in tds[-1].itertext()])
            t.parse(date, re.sub(r'[ ]+', ' ', raw))
            t.set_amount(credit, debit)
            yield t
