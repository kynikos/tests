# Copyright (C) 2015 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import json
import string
import random
import getpass
import smtplib
from email.mime.text import MIMEText

with open(sys.argv[1], 'r') as cf:
    config = json.load(cf)

# Example config (json)
#{
#    'passwords': (
#        'addr1@somedomain.com',
#        'addr2@somedomain.com',
#        'OtherProvider',
#    ),
#    'parameters': {
#        'somedomain.com': (
#            ('smtp.somedomain.com', 465, 2, '{address}', '{address}'),
#            (
#                'addr1@somedomain.com',
#            ),
#            (
#                'addr2@somedomain.com',
#            ),
#        ),
#        'OtherProvider': (
#            ('mail.{domain}', 587, 0, '{domain}', 'OtherProvider'),
#            (
#                'addrA@foodomain.com',
#                'addrB@foodomain.com',
#            ),
#            (
#                'addrC@bardomain.net',
#            ),
#        ),
#    },
#}

passwords = {
    provider: getpass.getpass("{} password: ".format(provider))
    for provider in config["passwords"]
}
parameters = config["parameters"]

servers = []

for provider in parameters:
    for group in parameters[provider][1:]:
        servers.append((parameters[provider][0], group))

random.shuffle(servers)
sessionid = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for _ in range(3))
print("Session ID:", sessionid)
sentN = 0
refusedN = 0

for i, rserver in enumerate(servers):
    # Make sure to test all servers
    # Make sure not to test a recipient using its own server
    attempts = servers[i + 1:] + servers[:i]
    recipients = list(rserver[1])

    for sserver in attempts:
        params = sserver[0]
        address0 = sserver[1][0]
        strf = {"address": address0, "domain": address0.rpartition('@')[2]}
        smtp = params[0].format(**strf)
        port = params[1]
        secure = params[2]
        login = params[3].format(**strf)
        password = passwords[params[4].format(**strf)]

        if secure > 1:
            Conn = smtplib.SMTP_SSL
        else:
            Conn = smtplib.SMTP

        print("Connecting as {} ...".format(address0))
        smtp = Conn(smtp, port=port)
        #smtp.set_debuglevel(1)

        if secure == 1:
            smtp.starttls()

        smtp.login(login, password)

        try:
            # Send one email per recipient, so it's easier to test
            while recipients:
                recipient = recipients[-1]
                text = 'Test {} - {}'.format(sessionid, sentN + 1)

                msg = MIMEText(text)
                msg['Subject'] = text
                msg['From'] = address0
                msg['To'] = recipient

                print("Sending email {} to {} ...".format(sentN + 1,
                                                          recipient))

                refused = smtp.send_message(msg)

                # Remove the recipient since no exception has been raised
                recipients.remove(recipient)

                if len(refused):
                    print("Recipient refused:", refused)
                    refusedN += 1
                else:
                    sentN += 1

        except smtplib.SMTPSenderRefused as err:
            # The server (usually Alice.it) may be blacklisting the client's
            # IP, so use an alternative server
            smtp.quit()
            print(err)
            continue
        except smtplib.SMTPDataError as err:
            # The server (usually Hotmail.it) may require reconnecting after
            # sending a few emails, so use an alternative server
            try:
                smtp.quit()
            except smtplib.SMTPServerDisconnected:
                # The client may have been already disconnected by the server
                pass
            print(err)
            continue
        else:
            smtp.quit()
            break

print("{} emails sent, {} refused".format(sentN, refusedN))
