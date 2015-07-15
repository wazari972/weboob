# -*- coding: utf-8 -*-

# Copyright(C) 2015      Baptiste Delpey
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
from decimal import Decimal
from StringIO import StringIO
from PIL import Image

from weboob.browser.pages import LoggedPage, HTMLPage
from weboob.browser.elements import method, ListElement, ItemElement
from weboob.capabilities.bank import Account
from weboob.browser.filters.standard import CleanText, Regexp, Field, Map
from weboob.tools.capabilities.bank.transactions import FrenchTransaction


class BfBKeyboard(object):
    symbols = {'0': '00111111001111111111111111111111000000111000000001111111111111111111110011111100',
               '1': '00000000000011000000011100000001100000001111111111111111111100000000000000000000',
               '2': '00100000111110000111111000011111000011111000011101111111100111111100010111000001',
               '3': '00100001001110000111111000011111001000011101100001111111011111111111110000011110',
               '4': '00000011000000111100000111010001111001001111111111111111111111111111110000000100',
               '5': '00000001001111100111111110011110010000011001000001100110011110011111110000111110',
               '6': '00011111000111111110111111111111001100011000100001110011001111001111110100011110',
               '7': '10000000001000000000100000111110011111111011111100111110000011100000001100000000',
               '8': '00000011001111111111111111111110001000011000100001111111111111111111110010011110',
               '9': '00111000001111110011111111001110000100011000010011111111111111111111110011111100',
               }

    def __init__(self, basepage):
        self.basepage = basepage
        self.fingerprints = []
        for htmlimg in self.basepage.doc.xpath('.//div[@class="m-btn-pin"]//img'):
            url = htmlimg.attrib.get("src")
            imgfile = StringIO(basepage.browser.open(url).content)
            img = Image.open(imgfile)
            matrix = img.load()
            s = ""
            # The digit is only displayed in the center of image
            for x in range(19, 27):
                for y in range(17, 27):
                    (r, g, b, o) = matrix[x, y]
                    # If the pixel is "red" enough
                    if g + b < 450:
                        s += "1"
                    else:
                        s += "0"

            self.fingerprints.append(s)

    def get_symbol_code(self, digit):
        fingerprint = self.symbols[digit]
        for i, string in enumerate(self.fingerprints):
            if string == fingerprint:
                return i

    def get_string_code(self, string):
        code = ''
        for c in string:
            codesymbol = self.get_symbol_code(c)
            code += str(codesymbol)
        return code

class LoginPage(HTMLPage):
    def login(self, birthdate, username, password):
        vk = BfBKeyboard(self)
        code = vk.get_string_code(password)
        form = self.get_form()
        form['j_username'] = username
        form['birthDate'] = birthdate
        form['indexes'] = code
        form.submit()


class ErrorPage(HTMLPage):
    pass

class AccountsPage(LoggedPage, HTMLPage):
    @method
    class iter_accounts(ListElement):
        item_xpath = '//table/tbody/tr'

        class item(ItemElement):
            klass = Account

            TYPE = {'Livret': Account.TYPE_SAVINGS,
                   }

            def obj_balance(self):
                balance = CleanText(self.el.xpath('./td/div/div[1]/div/span'))(self)
                balance = re.sub(r'[^\d\-\,]', '', balance)
                return Decimal(re.sub(r',(?!(\d+$))', '', balance).replace(',', '.'))

            obj_id = CleanText('./td/div/div[3]/span') & Regexp(pattern=r'(\d+)')
            obj_label = CleanText('./td/div/div[2]/span')
            obj_currency = FrenchTransaction.Currency('./td/div/div[1]/div/span')
            obj_type = Map(Regexp(Field('label'), r'^(\w+)'), TYPE, default=Account.TYPE_UNKNOWN)
            obj__link = CleanText('./@data-href')


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^(?P<category>VIREMENT)'), FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^(?P<category>INTERETS)'), FrenchTransaction.TYPE_BANK),
               ]


class HistoryPage(LoggedPage, HTMLPage):
    @method
    class get_operations(ListElement):
        item_xpath = '//table[contains(@class, "table")]/tbody/div/tr[contains(@class, "submit")]'

        class item(ItemElement):
            klass = Transaction

            def obj_amount(self):
                balance = CleanText(self.el.xpath('./td[4]'))(self)
                balance = re.sub(r'[^\d\-\,]', '', balance)
                return Decimal(re.sub(r',(?!(\d+$))', '', balance).replace(',', '.'))

            obj_date = Transaction.Date('./td[2]')
            obj_vdate = Transaction.Date('./td[3]')
            obj_raw = Transaction.Raw('./td[1]')
