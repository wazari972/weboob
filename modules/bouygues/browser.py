# -*- coding: utf-8 -*-

# Copyright(C) 2010-2015 Bezleputh
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
from .pages import LoginPage, LoginSuccess, SendSMSPage, SendSMSErrorPage

from weboob.capabilities.messages import CantSendMessage

__all__ = ['BouyguesBrowser']


class BouyguesBrowser(LoginBrowser):
    BASEURL = 'https://www.mon-compte.bouyguestelecom.fr/'
    TIMEOUT = 20

    home = URL('http://www.bouyguestelecom.fr/mon-compte/', LoginSuccess)
    login = URL('cas/login', LoginPage)

    sms_page = URL('http://www.mobile.service.bbox.bouyguestelecom.fr/services/SMSIHD/sendSMS.phtml',
                   'http://www.mobile.service.bbox.bouyguestelecom.fr/services/SMSIHD/confirmSendSMS.phtml',
                   SendSMSPage)

    confirm = URL('http://www.mobile.service.bbox.bouyguestelecom.fr/services/SMSIHD/resultSendSMS.phtml')

    sms_error_page = URL('http://www.mobile.service.bbox.bouyguestelecom.fr/services/SMSIHD/SMS_erreur.phtml',
                         SendSMSErrorPage)

    def do_login(self):
        self.login.go().login(self.username, self.password)

        if not self.home.is_here():
            raise BrowserIncorrectPassword

    @need_login
    def post_message(self, message):
        self.sms_page.go()

        if self.sms_error_page.is_here():
            raise CantSendMessage(self.page.get_error_message())

        receivers = ";".join(list(message.receivers)) if message.receivers else self.username
        self.page.send_sms(message, receivers)

        if self.sms_error_page.is_here():
            raise CantSendMessage(self.page.get_error_message())

        self.confirm.open()
