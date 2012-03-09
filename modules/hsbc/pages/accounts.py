# -*- coding: utf-8 -*-

# Copyright(C) 2012  Romain Bignon
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
from datetime import date

from weboob.tools.browser import BasePage
from weboob.capabilities.bank import Account, Transaction
from weboob.capabilities.base import NotAvailable


__all__ = ['AccountsListPage']


class AccountsListPage(BasePage):
    def get_list(self):
        for tr in self.document.getiterator('tr'):
            tds = tr.findall('td')
            if len(tds) != 3 or tds[0].attrib.get('class', '') != 'txt' or tds[0].attrib.get('valign', '') == 'center':
                continue

            account = Account()
            account.id = tds[1].text.strip()

            a = tds[0].findall('a')[-1]
            account.label = a.text.strip()
            account.link_id = a.attrib['href']

            if not 'CPT_IdPrestation' in account.link_id:
                continue

            tag = tds[2].find('font')
            if tag is None:
                tag = tds[2]
            account.balance = float(tag.text.replace('.','').replace(',','.').replace(' ', '').strip(u' \t\u20ac\xa0€\n\r'))
            account.coming = NotAvailable

            yield account

class HistoryPage(BasePage):
    LABEL_PATTERNS = [(re.compile('^VIR(EMENT)? (?P<text>.*)'), Transaction.TYPE_TRANSFER,   '%(text)s'),
                      (re.compile('^PRLV (?P<text>.*)'),        Transaction.TYPE_ORDER,      '%(text)s'),
                      (re.compile('^CB (?P<text>.*)\s+(?P<dd>\d+)/(?P<mm>\d+)\s*(?P<loc>.*)'),
                                                                Transaction.TYPE_CARD,       '%(mm)s/%(dd)s: %(text)s'),
                      (re.compile('^DAB (?P<dd>\d{2})/(?P<mm>\d{2}) (?P<text>.*)'),
                                                                Transaction.TYPE_WITHDRAWAL, '%(mm)s/%(dd)s: %(text)s'),
                      (re.compile('^CHEQUE$'),                  Transaction.TYPE_CHECK,      'CHEQUE'),
                      (re.compile('^COTIS\.? (?P<text>.*)'),    Transaction.TYPE_BANK,       '%(text)s'),
                      (re.compile('^REMISE (?P<text>.*)'),      Transaction.TYPE_DEPOSIT,    '%(text)s'),
                     ]

    def get_operations(self):
        for script in self.document.getiterator('script'):
            if script.text is None or script.text.find('\nCL(0') < 0:
                continue

            for m in re.finditer(r"CL\((\d+),'(.+)','(.+)','(.+)','([\d -\.,]+)','([\d -\.,]+)','\d+','\d+','[\w\s]+'\);", script.text, flags=re.MULTILINE):
                op = Transaction(m.group(1))
                op.raw = m.group(4)
                for pattern, _type, _label in self.LABEL_PATTERNS:
                    mm = pattern.match(op.raw)
                    if mm:
                        op.type = _type
                        op.label = re.sub('[ ]+', ' ', _label % mm.groupdict()).strip()
                        break

                op.amount = float(m.group(5).replace('.','').replace(',','.').replace(' ', '').strip(u' \t\u20ac\xa0€\n\r'))
                op.date = date(*reversed([int(x) for x in m.group(3).split('/')]))
                op.category = NotAvailable
                yield op
