# -*- coding: utf-8 -*-

# Copyright(C) 2012-2014 Kevin Pouget, Florent Fourcot
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

from weboob.tools.json import json
from weboob.capabilities.bank import Account
from weboob.tools.capabilities.bank.transactions import FrenchTransaction
from weboob.browser.pages import HTMLPage, JsonPage, LoggedPage
from weboob.browser.filters.standard import Filter, Format, CleanText, CleanDecimal
from weboob.browser.elements import ListElement, ItemElement, method


class LoginPage(HTMLPage):
    def login(self, login, password):
        form = self.get_form(xpath='//form[@id="AuthForm"]')
        form['j_username'] = login.encode('iso-8859-15')
        form['j_password'] = password.encode('iso-8859-15')
        form.submit()


class CreditLoggedPage(HTMLPage):
    def get_error(self):
        div = self.doc.xpath('//div[@class="errorForm-msg"]')
        if len(div) == 0:
            return None

        msg = u', '.join([li.text.strip() for li in div[0].xpath('.//li')])
        return re.sub('[\r\n\t\xa0]+', ' ', msg)


class AddType(Filter):
    types = {u'COMPTE NEF': Account.TYPE_CHECKING,
             u'CPTE A VUE': Account.TYPE_CHECKING,
             u'LIVRET AGIR': Account.TYPE_SAVINGS}

    def filter(self, str_type):
        for key, acc_type in self.types.items():
            if key == str_type:
                return acc_type
        return Account.TYPE_UNKNOWN


class AccountsPage(LoggedPage, HTMLPage):
    @method
    class get_list(ListElement):
        item_xpath = '//table[has-class("table-synthese")]'

        class item(ItemElement):
            klass = Account

            obj_label = Format('%s %s', CleanText('.//h2[@class="tt_compte"][1]'), CleanText('.//ul[@class="nClient"]/li[1]'))
            obj_id = CleanText('.//ul[@class="nClient"]/li[last()]', symbols=u'N°')
            obj_type = AddType(CleanText('.//h2[@class="tt_compte"][1]'))
            obj_balance = CleanDecimal('.//td[@class="sum_solde"]//span[last()]', replace_dots=True)
            obj_coming = None # will be set in Browser.CreditCooperatif.get_accounts_list
            obj_currency = u'EUR'

            obj__credit_card_account = False
            obj__has_cb = CleanText('.//tbody/tr[@class="nn_border"]//a', default='')
            obj__has_encours = CleanDecimal('.//tbody/tr[@class="operations"]/td/a', replace_dots=True, default=0)
            
class EncoursCBPage(LoggedPage, HTMLPage):
    @method
    class get_list(ListElement):
        item_xpath = '//table[has-class("table-encourscb")][caption]'

        class item(ItemElement):
            klass = Account
            obj_label = CleanText('./caption') # or .//form[@id="creditCardDTO"]/input[@id="porteur"]/@value
            obj_id = CleanText('.//form[@id="creditCardDTO"]/input[@id="numero"]/@value', symbols=u'N°')
            obj_type = Account.TYPE_LOAN
            def sign(x):
                return 1 if x == "0,00" else -1
            
            obj_coming = CleanDecimal('.//form[@id="creditCardDTO"]/input[@id="montantTotal"]/@value', replace_dots=True, sign=sign)
            obj_currency = u'EUR'

            obj__credit_card_account = True
            
class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^(?P<text>RETRAIT DAB) (?P<dd>\d{2})-(?P<mm>\d{2})-([\d\-]+)'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^RETRAIT DAB (?P<dd>\d{2})-(?P<mm>\d{2})-([\d\-]+) (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^CARTE (?P<dd>\d{2})(?P<mm>\d{2}) \d+ (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_CARD),
                (re.compile('^VIR COOPA (?P<dd>\d{2})/(?P<mm>\d{2}) (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^SDD RECU (TRANSFRONTALIER|NATIONAL)? (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^VIR(EMENT|EMT| SEPA EMET :)? (?P<text>.*?)(- .*)?$'),
                                                            FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^(PRLV|PRELEVEMENT) SEPA (?P<text>.*?)(- .*)?$'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^(PRLV|PRELEVEMENT) (?P<text>.*?)(- .*)?$'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^CHEQUE.*'),                   FrenchTransaction.TYPE_CHECK),
                (re.compile('^(AGIOS /|FRAIS) (?P<text>.*)'), FrenchTransaction.TYPE_BANK),
                (re.compile('^ABONNEMENT (?P<text>.*)'),    FrenchTransaction.TYPE_BANK),
                (re.compile('^REMISE (?P<text>.*)'),        FrenchTransaction.TYPE_DEPOSIT),
                (re.compile('^(?P<text>.*)( \d+)? QUITTANCE .*'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^.* LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2})$'),
                                                            FrenchTransaction.TYPE_UNKNOWN),
               ]


class TransactionsPage(LoggedPage, HTMLPage):
    pass


class TransactionsJSONPage(LoggedPage, JsonPage):
    ROW_DATE =    0
    ROW_TEXT =    2
    ROW_CREDIT = -1
    ROW_DEBIT =  -2

    def get_transactions(self):
        seen = set()
        for tr in self.doc['exportData'][1:]:
            t = Transaction(0)
            t.parse(tr[self.ROW_DATE], tr[self.ROW_TEXT])
            t.set_amount(tr[self.ROW_CREDIT], tr[self.ROW_DEBIT])
            t.id = t.unique_id(seen)
            yield t


class ComingTransactionsPage(LoggedPage, HTMLPage):
    ROW_REF =     0
    ROW_TEXT =    1
    ROW_DATE =    2
    ROW_CREDIT = -1
    ROW_DEBIT =  -2

    def get_transactions(self):
        data = []
        for script in self.doc.xpath('//script'):
            txt = script.text
            if txt is None:
                continue

            pattern = 'var jsonData ='
            start = txt.find(pattern)
            if start < 0:
                continue

            txt = txt[start+len(pattern):start+txt[start:].find(';')]
            data = json.loads(txt)
            
            # credit card COMING purchases entries contain a link,
            # we don't want them in this list, they have an account
            # on their own in Browser.CreditCooperatif.get_accounts_list
            data = [entry for entry in data if "</a>" not in entry[1]]
            
            break

        for tr in data:
            t = Transaction(0)
            text = tr[self.ROW_TEXT].replace("BANQUE EN LIGNE EN ATTENTE D EXECUTION", "(en attente)")
            t.parse(tr[self.ROW_DATE], text)
            t.set_amount(tr[self.ROW_CREDIT], tr[self.ROW_DEBIT])
            yield t
                
class ComingCBTransactionsPage(LoggedPage, HTMLPage):
    ROW_DATE =  0
    ROW_TEXT =  1
    ROW_DEBIT = 2
    JSON_PREFIX = 'var jsonData1 ='
    
    def get_transactions(self):
        data = []
        for script in self.doc.xpath('//script'):
            txt = script.text
            if txt is None:
                continue

            start = txt.find(self.JSON_PREFIX)
            if start < 0:
                continue
            
            txt = txt[start+len(self.JSON_PREFIX)
                      :start+txt[start:].find(';')]
            data = json.loads(txt)
                        
            break

        for tr in data:
            t = Transaction(0)
            text = tr[self.ROW_TEXT]
            t.parse(tr[self.ROW_DATE], text)
            t.set_amount(debit=tr[self.ROW_DEBIT])
            yield t
            
