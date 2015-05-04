# -*- coding: utf-8 -*-

# Copyright(C) 2014, 2015      Oleg Plakhotniuk
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
from weboob.browser.pages import HTMLPage, JsonPage, RawPage
from weboob.capabilities.bank import Account, AccountNotFound, Transaction
from weboob.exceptions import BrowserIncorrectPassword
from weboob.tools.capabilities.bank.transactions import \
    AmericanTransaction as AmTr

from .parser import StatementParser, clean_label

import re
import os
from datetime import datetime
from tempfile import mkstemp
from subprocess import check_output, STDOUT
from time import sleep


__all__ = ['Citibank']


class SomePage(HTMLPage):
    @property
    def logged(self):
        return bool(self.doc.xpath(u'//a[text()="Sign Off"]'))


class IndexPage(SomePage):
    def extra(self):
        APPEND = r'jQuery\( "form" \).each\(function\(\) {' \
                    r'if\(isValidUrl\(jQuery\(this\).attr\("action"\)\)\){' \
                        r'jQuery\(this\).append\(([^)]+)\);}}\);'
        script = self.doc.xpath(
            '//script[contains(text(),"XXX_Extra")]/text()')[0]
        script = re.sub(APPEND, lambda m: 'return %s;' % m.group(1), script)
        script = re.sub(r'jQuery\(document\)[^\n]+\n', '', script)
        for x in re.findall('function ([^(]+)\(', script):
            script += '\nvar x = %s(); if (x) print(x);' % x
        scriptFd, scriptName = mkstemp('.js')
        os.write(scriptFd, script)
        os.close(scriptFd)
        html = check_output(["d8", scriptName], stderr=STDOUT)
        os.remove(scriptName)
        return re.findall(r'name=([^ ]+) value=([^>]+)>', html)


class AccountsPage(JsonPage):
    logged = True

    def inner_ids_dict(self):
        return dict((prod['parsedAccountName'][-4:], prod['accountInstanceId'])
            for bean in self.doc['summaryViewBeanList']
            for cat in bean['accountsSummaryViewObj']['categoryList']
            for prod in cat['products'] if cat['categoryType'] == 'CRD')


class AccDetailsPage(JsonPage):
    logged = True

    def account(self):
        detact = self.doc['accountDetailsAndActivity']
        details = detact['accountDetails']
        account = Account()
        account.type = Account.TYPE_CARD
        account.label = re.sub(r'<[^>]+>', '', detact['accountName'])
        account.id = account.label[-4:]
        for bal in details['accountBalances']:
            label, value = bal['label'], (bal['value'] or ['0'])[0]
            if label == u'Current Balance:':
                account.currency = Account.get_currency(value)
                account.balance = -AmTr.decimal_amount(value)
            elif label == u'Total Revolving Credit Line:':
                account.cardlimit = AmTr.decimal_amount(value)
            elif label.startswith(u'Minimum Payment Due'):
                d = re.match(r'.*(..-..-....):$', label).group(1)
                account.paydate = datetime.strptime(d, '%m-%d-%Y')
                account.paymin = AmTr.decimal_amount(value)
        return account

    def transactions(self):
        return sorted(self.unsorted_trans(),
            lambda a, b: cmp(a.date, b.date), reverse=True)

    def unsorted_trans(self):
        for jnl in self.doc['accountDetailsAndActivity']['accountActivity'] \
                           ['postedTransactionJournals']:
            tdate = jnl['columns'][0]['activityColumn'][0]
            label = jnl['columns'][1]['activityColumn'][0]
            amount = jnl['columns'][3]['activityColumn'][0]
            xdescs = dict((x['label'], x['value'][0])
                          for x in jnl['extendedDescriptions'])
            pdate = xdescs[u'Posted Date :']
            ref = xdescs.get(u'Reference Number:') or u''

            if amount.startswith(u'(') and amount.endswith(u')'):
                amount = AmTr.decimal_amount(amount[1:-1])
            else:
                amount = -AmTr.decimal_amount(amount)
            label = clean_label(label)

            trans = Transaction(ref)
            trans.date = datetime.strptime(tdate, '%m-%d-%Y')
            trans.rdate = datetime.strptime(pdate, '%m-%d-%Y')
            trans.type = Transaction.TYPE_UNKNOWN
            trans.raw = label
            trans.label = label
            trans.amount = amount
            yield trans


class StatementsPage(SomePage):
    def dates(self):
        return [x[:10] for x in self.doc.xpath(
            u'//select[@id="currentStatementsDate"]/option/@value')
            if re.match(u'^\d\d\d\d-\d\d-\d\d All$', x)]


class StatementPage(RawPage):
    logged = True

    def __init__(self, *args, **kwArgs):
        RawPage.__init__(self, *args, **kwArgs)
        self._parser = StatementParser(self.doc)

    def is_sane(self):
        return self._parser.read_first_date_range() is not None

    def transactions(self):
        return sorted(self._parser.read_transactions(),
                      cmp=lambda t1, t2: cmp(t2.date, t1.date))


class Citibank(LoginBrowser):
    """
    Citibank website uses some kind of Javascript magic during login
    negotiation, hence a real JS interpreter is being used to log in.

    External dependencies:
    V8 JavaScript Engine (http://code.google.com/p/v8/).
    MuPDF (http://www.mupdf.com).

    Tested on Arch Linux snapshot of 2014-11-11 (official and user packages).

    Only a single credit card account is currently supported.
    Contributions are welcome!
    """

    BASEURL = 'https://online.citibank.com'
    MAX_RETRIES = 10
    TIMEOUT = 30.0
    index = URL(r'/US/JPS/portal/Index.do', IndexPage)
    signon = URL(r'/US/JSO/signon/ProcessUsernameSignon.do', SomePage)
    accounts = URL(r'/US/REST/accountsPanel'
                   r'/getCustomerAccounts.jws\?ttc=(?P<ttc>.*)$',
                   AccountsPage)
    accdetails = URL(r'/US/REST/accountDetailsActivity'
        r'/getAccountDetailsActivity.jws\?accountID=(?P<accountID>.*)$',
        AccDetailsPage)
    statements = URL(r'/US/NCSC/doccenter/flow.action\?TTC=1079&'
        'accountID=(?P<accountID>.*)$', StatementsPage)
    statement = URL(r'/US/REST/doccenterresource/downloadStatementsPdf.jws\?'
                    r'selectedIndex=0&date=(?P<date>....-..-..)&'
                    r'downloadFormat=pdf', StatementPage)
    unknown = URL('/.*$', SomePage)

    def get_account(self, id_):
        innerId = self.to_accounts().inner_ids_dict().get(id_)
        if innerId:
            return self.to_account(innerId).account()
        raise AccountNotFound()

    def iter_accounts(self):
        for innerId in self.to_accounts().inner_ids_dict().values():
            yield self.to_account(innerId).account()

    def iter_history(self, account):
        innerId = self.to_accounts().inner_ids_dict()[account.id]
        for trans in self.to_account(innerId).transactions():
            yield trans
        for date in self.to_statements(innerId).dates():
            for trans in self.to_statement(date).transactions():
                yield trans

    def to_account(self, innerId):
        return self.to_page(self.accdetails, accountID=innerId)

    def to_accounts(self):
        return self.to_page(self.accounts, ttc='742')

    def to_statements(self, innerId):
        return self.to_page(self.statements, accountID=innerId)

    def to_statement(self, date):
        # Sometimes the website returns non-PDF file.
        # It recovers if we repeat whole browsing sequence all the way
        # from home page up to the statement.
        MAX_DELAY=10
        for i in xrange(self.MAX_RETRIES):
            if self.to_page(self.statement, date=date).is_sane():
                return self.page
            sleep(min(MAX_DELAY, 1 << i))
            self.do_login()
            innerId = self.to_accounts().inner_ids_dict().values()[0]
            self.to_account(innerId)
            self.to_statements(innerId)

    @need_login
    def to_page(self, url, **data):
        return self.page if url.is_here(**data) else url.go(data=data, **data)

    def do_login(self):
        self.session.cookies.clear()
        data = dict([('username', self.username), ('password', self.password)]+
                    self.index.go().extra())
        if not self.signon.go(data=data).logged:
            raise BrowserIncorrectPassword()
