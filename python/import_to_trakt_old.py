#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ------------------------------------------------------------------------
# Trakt.tv tools
#
# Copyright 2016-2021 xbgmsharp <xbgmsharp@gmail.com>. All Rights Reserved.
# License:  GNU General Public License version 3 or later; see LICENSE.txt
# Website:  https://trakt.tv, https://github.com/xbgmsharp/trakt
# ------------------------------------------------------------------------
#
# Purpose:
# Import Movies or TVShows IDs into Trakt.tv
#
# Requirement on Ubuntu/Debian Linux system
# apt-get install python3-dateutil python3-simplejson python3-requests python3-openssl jq
#
# Requirement on Windows on Python 3
# C:\Python3\Scripts\easy_install3.exe simplejson requests
#

import sys
import os
# https://urllib3.readthedocs.org/en/latest/security.html#disabling-warnings
# http://quabr.com/27981545/surpress-insecurerequestwarning-unverified-https-request-is-being-made-in-pytho
# http://docs.python-requests.org/en/v2.4.3/user/advanced/#proxies
try:
    import simplejson as json
    import requests
    requests.packages.urllib3.disable_warnings()
    import csv
except:
    sys.exit("Please use your favorite method to install the following module requests and simplejson to use this script")

import argparse
import configparser
import datetime
import collections
import pprint
import time

pp = pprint.PrettyPrinter(indent=4)

desc = """This program import Movies or TVShows IDs into Trakt.tv."""

epilog = """Read a list of ID from 'imdb', 'tmdb', 'tvdb' or 'tvrage' or 'trakt'.
Import them into a list in Trakt.tv, mark as seen if need."""

_trakt = {
    # Auth details for trakt API
    'client_id':       '7f1a0aac77ea2ce3251f5799dc20ef4e44e3e2bfaef78369c3c641756287fac0',
    # Auth details for trakt API
    'client_secret':       '3d8e615e532dfc47286b15d756e9ad0260842a57134f1200bd92af8d6b723b44',
    # Auth details for trakt API
    'access_token':       '79c64caa8228e6ef7f1ac0b07238420d96cac8d5ebc326637414a2c8972f4ee2',
    # Auth details for trakt API
    'refresh_token':       'c5b287a6d06b89cb97d69872c1b57c27a8f0d6705f397de6e2534e02753978c9',
    # Sandbox environment https://api-staging.trakt.tv,
    'baseurl':       'https://api.trakt.tv',
}

_headers = {
    'Accept': 'application/json',   # required per API
    'Content-Type': 'application/json',   # required per API
    'User-Agent': 'Trakt importer',     # User-agent
    # Thanks to urllib3, keep-alive is 100% automatic within a session!
    'Connection': 'Keep-Alive',
    'trakt-api-version': '2',                  # required per API
    # required per API
    'trakt-api-key': '7f1a0aac77ea2ce3251f5799dc20ef4e44e3e2bfaef78369c3c641756287fac0',
    # required per API
    'Authorization': '79c64caa8228e6ef7f1ac0b07238420d96cac8d5ebc326637414a2c8972f4ee2',
}

response_arr = []


def read_csv(options):
    """Read CSV of Movies or TVShows IDs and return a dict"""
    reader = csv.DictReader(options.input, delimiter=',')
    return list(reader)


def api_auth(options, config=None, refresh=False):
    """API call for authentification OAUTH"""
    values = None
    if refresh == False:
        print("Manual authentification. Open the link in a browser and paste the pincode when prompted")
        print(("https://trakt.tv/oauth/authorize?response_type=code&"
              "client_id={0}&redirect_uri=urn:ietf:wg:oauth:2.0:oob".format(
                  _trakt["client_id"])))
        pincode = str(input('Input PIN:'))
        # Exchange code for access_token
        # First run
        values = {
            "code": pincode,
            "client_id": _trakt["client_id"],
            "client_secret": _trakt["client_secret"],
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "grant_type": "authorization_code"
        }
    else:
        # Exchange refresh_token for access_token
        # Refresh token
        values = {
            "refresh_token": _trakt['refresh_token'],
            "client_id": _trakt['client_id'],
            "client_secret": _trakt["client_secret"],
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "grant_type": "refresh_token"
        }

    url = _trakt['baseurl'] + '/oauth/token'
    request = requests.post(url, data=values)
    if request.status_code == 200:
        response = request.json()
        # pp.pprint(response)
        print("Authentication successful")
        _headers['Authorization'] = 'Bearer ' + response["access_token"]
        _headers['trakt-api-key'] = _trakt['client_id']
        # Update configuration file
        if config:
            config.set('TRAKT', 'ACCESS_TOKEN', response["access_token"])
            config.set('TRAKT', 'REFRESH_TOKEN', response["refresh_token"])
            with open(options.config, 'w') as configfile:
                config.write(configfile)
                print('Saved as "access_token" in file {0}: {1}'.format(
                    options.config, response["access_token"]))
                print('Saved as "refresh_token" in file {0}: {1}'.format(
                    options.config, response["refresh_token"]))
    else:
        print("Sorry, the authentication was not successful.")
        pp.pprint(request)
        sys.exit(1)


def api_search_by_id(options, id):
    """API call for Search / ID Lookup / Get ID lookup results"""
    url = _trakt['baseurl'] + \
        '/search?id_type={0}&id={1}'.format(options.format, id)
    if options.verbose:
        print(url)
    r = requests.get(url, headers=_headers, timeout=(5, 60))
    if r.status_code != 200:
        print("Error Get ID lookup results: {0} [{1}]".format(
            r.status_code, r.text))
        return None
    else:
        return json.loads(r.text)


def api_get_list(options, page):
    """API call for Sync / Get list by type"""
    url = _trakt['baseurl'] + '/sync/{list}/{type}?page={page}&limit={limit}'.format(
        list=options.list, type=options.type, page=page, limit=1000)
    if options.verbose:
        print(url)
    r = requests.get(url, headers=_headers, timeout=(5, 60))
    # pp.pprint(r.headers)
    if r.status_code != 200:
        print("Error fetching Get {list}: {status} [{text}]".format(
            list=options.list, status=r.status_code, text=r.text))
        return None
    else:
        global response_arr
        response_arr += json.loads(r.text)
    if 'X-Pagination-Page-Count' in r.headers and r.headers['X-Pagination-Page-Count']:
        print("Fetched page {page} of {PageCount} pages for {list} list".format(
            page=page, PageCount=r.headers['X-Pagination-Page-Count'], list=options.list))
        if page != int(r.headers['X-Pagination-Page-Count']):
            api_get_list(options, page+1)

    return response_arr


def api_add_to_list(options, import_data):
    """API call for Sync / Add items to list"""
    # 429 [AUTHED_API_POST_LIMIT rate limit exceeded. Please wait 1 seconds then retry your request.]
    # Rate limit for API
    time.sleep(1)
    url = _trakt['baseurl'] + '/sync/{list}'.format(list=options.list)
    #values = '{ "movies": [ { "ids": { "imdb": "tt0000111" } }, { "ids": { , "imdb": "tt1502712" } } ] }'
    #values = '{ "movies": [ { "watched_at": "2014-01-01T00:00:00.000Z", "ids": { "imdb": "tt0000111" } }, { "watched_at": "2013-01-01T00:00:00.000Z", "ids": { "imdb": "tt1502712" } } ] }'
    if options.type == 'episodes':
        values = {'episodes': import_data}
    else:
        values = {options.type: import_data}

    json_data = json.dumps(values)
    if options.verbose:
        print("Sending to URL: {0}".format(url))
        pp.pprint(json_data)

    r = requests.post(url, data=json_data,
                          headers=_headers, timeout=(5, 60))

    if r.status_code != 201:
        print("Error Adding items to {list}: {status} [{text}]".format(
            list=options.list, status=r.status_code, text=r.text))
        return None
    else:
        return json.loads(r.text)


def api_remove_from_list(options, remove_data):
    """API call for Sync / Remove from list"""
    url = _trakt['baseurl'] + '/sync/{list}/remove'.format(list=options.list)
    if options.type == 'episodes':
        values = {'shows': remove_data}
    else:
        values = {options.type: remove_data}
    json_data = json.dumps(values)
    if options.verbose:
        print(url)
        pp.pprint(json_data)
    r = requests.post(url, data=json_data,
                          headers=_headers, timeout=(5, 60))
    if r.status_code != 200:
        print("Error removing items from {list}: {status} [{text}]".format(
            list=options.list, status=r.status_code, text=r.text))
        return None
    else:
        return json.loads(r.text)


def cleanup_list(options):
    """Empty list prior to import"""
    export_data = api_get_list(options, 1)
    if export_data:
        print("Found {0} Item-Count".format(len(export_data)))
    else:
        print("Error, Cleanup no item return for {type} from the {list} list".format(
            type=options.type, list=options.list))
        sys.exit(1)
    results = {'sentids': 0, 'deleted': 0, 'not_found': 0}
    to_remove = []
    for data in export_data:
        to_remove.append({'ids': data[options.type[:-1]]['ids']})
        if len(to_remove) >= 10:
            results['sentids'] += len(to_remove)
            result = api_remove_from_list(options, to_remove)
            if result:
                print("Result: {0}".format(result))
                if 'deleted' in result and result['deleted']:
                    results['deleted'] += result['deleted'][options.type]
                if 'not_found' in result and result['not_found']:
                    results['not_found'] += len(result['not_found']
                                                [options.type])
            to_remove = []
    # Remove the rest
    if len(to_remove) > 0:
        # pp.pprint(data)
        results['sentids'] += len(to_remove)
        result = api_remove_from_list(options, to_remove)
        if result:
            print("Result: {0}".format(result))
            if 'deleted' in result and result['deleted']:
                results['deleted'] += result['deleted'][options.type]
            if 'not_found' in result and result['not_found']:
                results['not_found'] += len(result['not_found'][options.type])
    print("Overall cleanup {sent} {type}, results deleted:{deleted}, not_found:{not_found}".format(
        sent=results['sentids'], type=options.type, deleted=results['deleted'], not_found=results['not_found']))


def main():
    """
    Main program loop
    * Read configuration file and validate
    * Read CSV file
    * Authenticate if require
    * Cleanup list from Trakt.tv
    * Inject data into Trakt.tv
    """

    options = {'verbose': True, 'seen': False, 'list': False}

    # Display debug information
    if options.verbose:
        print("Options: %s" % options)

    if options.seen and options.list != "history":
        print("Error, you can only mark seen {0} when adding into the history list".format(
            options.type))
        sys.exit(1)

    if options.seen:
        try:
            datetime.datetime.strptime(options.seen, '%Y-%m-%dT%H:%M:%S.000Z')
        except:
            sys.exit(
                "Error, invalid format, it's must be UTC datetime, eg: '2016-01-01T00:00:00.000Z'")

    # Read configuration and validate
    # config = read_config(options)

    # Display debug information
    # if options.verbose:
        # print("Config: {}".format(config))

    # Trakt auth
    if not _trakt['access_token'] and not _trakt['refresh_token'] and \
            _trakt['client_id'] and _trakt['client_secret']:
        print("Trakt, no token found in config file, requesting authorization_code")
        # api_auth(options, config, False)
    elif _trakt['access_token'] and _trakt['refresh_token'] and \
            _trakt['client_id'] and _trakt['client_secret']:
        # Check token validity
        # Trakt access_token is valid for 3 months before it needs to be refreshed again.
        today = datetime.datetime.today()
        modified_date = datetime.datetime.fromtimestamp(
            os.path.getmtime(options.config))
        duration = today - modified_date
        if duration and duration.seconds < 2592000:
            # 30*24*60*60 = 2592000
            print(
                "Trakt, skipped access token refresh, token is less than 30 days, only %s" % duration)
            _headers['Authorization'] = 'Bearer ' + _trakt["access_token"]
            _headers['trakt-api-key'] = _trakt['client_id']
        else:
            # Exchange refresh_token for access_token
            print(
                "Trakt, access token refresh, token is more than 30 days, token is %s old" % duration)
            # api_auth(options, config, True)
    else:
        print("No valid authentication parameters found in config file")
        sys.exit(1)

    if not _headers['Authorization'] and not _headers['trakt-api-key']:
        print("No valid Authorization header")
        sys.exit(1)

    # Display debug information
    if options.verbose:
        print("Trakt: {}".format(_trakt))
        print("Authorization header: {}".format(_headers['Authorization']))
        print("trakt-api-key header: {}".format(_headers['trakt-api-key']))

    # Empty list prior to import
    if options.clean:
        cleanup_list(options)

    # Read CSV list of IDs
    read_ids = read_csv(options)

    # if IDs make the list into trakt format
    data = []
    results = {'sentids': 0, 'added': 0, 'existing': 0, 'not_found': 0}
    if read_ids:
        print("Found {0} items to import".format(len(read_ids)))

        for myid in read_ids:
            # If id (row) exists and is not blank (has a format)
            if myid and not options.format in myid:
                print(
                    "Invalid file format, id (row) must exists and is not blank (has a format).")
                sys.exit(1)
            if myid and myid[options.format]:
                # pp.pprint(myid)
                # If format is not "imdb" it must be cast to an integer
                if not options.format == "imdb" and not myid[options.format].startswith('tt'):
                    myid[options.format] = int(myid[options.format])
                if (options.type == "movies" or options.type == "shows") and options.seen:
                    data.append(
                        {'ids': {options.format: myid[options.format]}, "watched_at": options.seen})
                elif (options.type == "movies" or options.type == "shows") and options.watched_at:
                    data.append(
                        {'ids': {options.format: myid[options.format]}, "watched_at": myid["watched_at"]})
                elif options.type == "episodes" and options.seen:
                    data.append(
                        {'ids': {options.format: myid[options.format]}, "watched_at": options.seen})
                elif options.type == "episodes" and options.watched_at:
                    data.append(
                        {'ids': {options.format: myid[options.format]}, "watched_at": myid["watched_at"]})
                elif (options.type == "movies" or options.type == "shows") and options.list == 'ratings' and options.rated_at:
                    data.append({'ids': {
                                options.format: myid[options.format]}, "rated_at": myid["rated_at"], "rating": myid["rating"]})
                else:
                    data.append(
                        {'ids': {options.format: myid[options.format]}})
                # Import batch of 10 IDs
                if len(data) >= 10:
                    # pp.pprint(json.dumps(data))
                    results['sentids'] += len(data)
                    result = api_add_to_list(options, data)
                    if result:
                        print("Result: {0}".format(result))
                        if 'added' in result and result['added']:
                            results['added'] += result['added'][options.type]
                        if 'existing' in result and result['existing']:
                            results['existing'] += result['existing'][options.type]
                        if 'not_found' in result and result['not_found']:
                            results['not_found'] += len(
                                result['not_found'][options.type])
                    data = []
        # Import the rest
        if len(data) > 0:
            # pp.pprint(data)
            results['sentids'] += len(data)
            result = api_add_to_list(options, data)
            if result:
                print("Result: {0}".format(result))
                if 'added' in result and result['added']:
                    results['added'] += result['added'][options.type]
                if 'existing' in result and result['existing']:
                    results['existing'] += result['existing'][options.type]
                if 'not_found' in result and result['not_found']:
                    results['not_found'] += len(result['not_found']
                                                [options.type])
    else:
        # TODO Read STDIN to ID
        print("No items found, nothing to do.")
        sys.exit(0)

    print("Overall imported {sent} {type}, results added:{added}, existing:{existing}, not_found:{not_found}".format(
        sent=results['sentids'], type=options.type, added=results['added'],
        existing=results['existing'], not_found=results['not_found']))


if __name__ == '__main__':
    main()
