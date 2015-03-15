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
import urllib.request

with open(sys.argv[1], 'r') as cf:
    config = json.load(cf)

# Example config (json)
#{
#    "target": "target.domain.com/page",
#    "domains": [
#        "domain.net",
#        "domain.org",
#    ],
#    "tests": [
#        "http://www.{}/",
#        "http://{}/aaa",
#        "http://www.{}/aaa#bbb",
#        "http://test.{}/aaa#bbb?ccc=ddd&eee=fff"
#    ]
#}

dest = config["target"]

for orig in config["domains"]:
    for test in config["tests"]:
        if isinstance(test, str):
            ourl = test.format(orig)
            durl = test.format(dest)
        else:
            ourl = test[0].format(orig)
            durl = test[1].format(dest)
        print('Request:', ourl)
        try:
            response = urllib.request.urlopen(ourl)
        except urllib.error.URLError as err:
            print(err.reason)
        else:
            if response.geturl() == durl:
                print('OK')
            else:
                print('ERROR:', response.geturl(), durl)
            print('Code:', response.getcode())
            for header in response.getheaders():
                print('\t{}: {}'.format(header[0], header[1]))
        print()
