#!/usr/bin/env python3

#
# jtupload.py
# JSON Trace Upload Client 
#
# Copyright (c) 2023 Data Culpa, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to 
# deal in the Software without restriction, including without limitation the 
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
# DEALINGS IN THE SOFTWARE.
#

import argparse
import base64
import json
import logging 
import os
import requests
import socket
import sys
import time
import traceback
import uuid

# Not yet. :-)
#API_KEY    = os.environ.get('JSONTRACE_API_KEY')
#API_SECRET = os.environ.get('JSONTRACE_SECRET')

API_BASE_URL = os.environ.get('JSONTRACE_BASE_URL', "https://demo.jsontrace.com")
API_BASE_UPLOAD_URL = API_BASE_URL + "/v1/upload"

class DataCulpaConnectionError(Exception):
    def __init__(self, url, message):
        #logger.error("Connection error for url %s: __%s__" % (url, message))
        super().__init__("Connection error for URL %s: __%s__" % (url, message))

class DataCulpaServerResponseParseError(Exception):
    def __init__(self, url, payload):
        #logger.error("Error parsing result from url %s: __%s__" % (url, payload))
        super().__init__("Bad response from URL %s: __%s__" % (url, payload))

class DataCulpaBadServerCodeError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = "Unexpected status code %s: %s" % (status_code, message)
        super().__init__(self.message)

class DataCulpaWatchpointNotDefined(Exception):
    def __init__(self):
        self.message = "No id found on the server for the supplied watchpoint spec"
        super().__init__(self.message)

class DataCulpaServerError(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

class Upload:
    def __init__(self):
        self.api_access_token = None
        self._cached_hostname = None

    def _json_headers(self):
        if self._cached_hostname is None:
            try:
                self._cached_hostname = socket.gethostname()
            except:
                pass
            if self._cached_hostname is None:
                self._cached_hostname = "gethostname_failed"

        headers = {'Content-type': 'application/json',
                   'Accept': 'text/plain',
                   'X-request-id': str(uuid.uuid1()),
                   'X-hostname': self._cached_hostname
                   }

        if self.api_access_token is not None:
            headers['Authorization'] = 'Bearer %s' % self.api_access_token

        return headers

    def _retry_on_error_code(self, rc):
        return rc >= 400 and rc < 500

    def GET(self, url, headers=None, stream=False):
        try:
            retry_count = 0
            while True:
                # The headers have to be in this loop so that we re-gen on
                # failure if the token has expired, etc.
                if headers is None:
                    _headers = self._json_headers()
                else:
                    _headers = headers

                try:
                    #tag_suffix = self._tag_from_headers(_headers)
                    r = requests.get(url=url, # + tag_suffix, 
                                     headers=_headers, 
                                     timeout=1 + retry_count, 
                                     stream=stream)
                    if self._retry_on_error_code(r.status_code) and retry_count < 2:
                        self.api_access_token = None
                        try:
                            #self.login()
                            retry_count += 1
                            continue # go to while True
                        except:
                            # tried to login again but guess it didn't stick.
                            pass
                    
                    break
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count > 10:
                        raise
                    print("%s: retry_count = %s" % (url, retry_count))


            if r.status_code != 200:
                raise DataCulpaBadServerCodeError(r.status_code, "url was %s" % url)
            return r
        except requests.exceptions.Timeout:
            raise DataCulpaConnectionError(url, "timed out")
        except requests.exceptions.HTTPError as err:
            raise DataCulpaConnectionError(url, "http error: %s" % err)
        except requests.RequestException as e:
            raise DataCulpaConnectionError(url, "request error: %s" % e)
        except BaseException as e:
            if isinstance(e, DataCulpaBadServerCodeError):
                raise e # Don't wrap the exception we just made above.
            raise DataCulpaConnectionError(url, "unexpected error: %s" % e)
        return None

    def POST(self, url, data, timeout=10.0, headers=None, is_login=False):
        
        try:
            retry_count = 0
            while True:
                # The headers have to be in this loop so that we re-gen on
                # failure if the token has expired, etc.
                if headers is None:
                    _headers = self._json_headers()
                else:
                    _headers = headers

                try:
                    #print("%s: Trying" % url)
                    #tag_suffix = self._tag_from_headers(_headers)

                    r = requests.post(url=url, # + tag_suffix,
                                  data=data, timeout=1 + retry_count,
                                  headers=_headers)
                    
                    if r.status_code != 200 and not is_login:
                        #print("%s: not 200" % url)
                        if self._retry_on_error_code(r.status_code) and retry_count < 2:
                            #print("%s: going to retry" % url)
                            self.api_access_token = None
                            try:
                                #print("%s: doing the login" % url)
                                #self.login()
                                #print(self.api_access_token)
                                retry_count += 1
                                #print("%s: continue..." % url);
                                continue # go to while True
                            except:
                                # tried to login again but guess it didn't stick.
                                pass
                        # endif
                    
                    #print("%s: breaking loop" % url);
                    break
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count > 10:
                        raise

            if r.status_code != 200:
                new_text = r.text
                # Chop off the annoying HTML nonsense if it's there..
                if new_text.startswith("<!DOCTYPE"):
                    p_pos = new_text.find("<p>")
                    if p_pos >= 0:
                        new_text = new_text[p_pos + 3:]
                        p_pos = new_text.find("</p>")
                        if p_pos > 0:
                            new_text = new_text[:p_pos]
                raise DataCulpaBadServerCodeError(r.status_code, "url was %s; text = %s" % (r.url, new_text))

            return r
        except requests.exceptions.Timeout:
            raise DataCulpaConnectionError(url, "timed out")
        except requests.exceptions.HTTPError as err:
            raise DataCulpaConnectionError(url, "http error: %s" % err)
        except requests.RequestException as e:
            raise DataCulpaConnectionError(url, "request error: %s" % e)
        except BaseException as e:
            if isinstance(e, DataCulpaBadServerCodeError):
                raise e # Don't wrap the exception we just made above.
            raise DataCulpaConnectionError(url, "unexpected error: %s" % e)
        return None

    def _batch_headers(self, file_name, label, append_hash):
        basename = ""
        if file_name is not None:
            basename = os.path.basename(file_name)

        headers = {'Content-type': 'application/json', 
                   'Accept': 'text/plain',
                   'X-agent': 'jsontrace-upload',
                   'X-batch-name': base64.urlsafe_b64encode(basename.encode('utf-8')),
                   }

        if label is not None:
            headers['X-label'] = base64.urlsafe_b64encode(label.encode('utf-8'))
        
        if append_hash is not None:
            headers['X-append-hash'] = append_hash

        if self.api_access_token is not None:
            headers['Authorization'] = 'Bearer %s' % self.api_access_token
        
        return headers

    def _parseJson(self, url, js_str):
        try:
            jr = json.loads(js_str)
        except:
            raise DataCulpaServerResponseParseError(url, js_str)
        return jr

    def load_file(self, method, file_name, label, append_hash=None):
        post_url = f"{API_BASE_UPLOAD_URL}/{method}"
        headers = self._batch_headers(file_name, label, append_hash)

        try:
            if file_name is None:
                r = requests.post(url=post_url, 
                                  files={"stdin": sys.stdin}, 
                                  headers=headers,
                                  timeout=120) # FIXME: not sure this is what we want.
            else:
                file_sz = os.stat(file_name).st_size
                file_sz_mb = int(file_sz / (1024 * 1024 * 1024))
                timeout = 10 + (2 * (1 + file_sz_mb))
                with open(file_name, "rb") as the_file:
                    r = requests.post(url=post_url, 
                                      files={file_name: the_file}, 
                                      headers=headers,
                                      timeout=timeout) # variable
                    #r.raise_for_status() # turn HTTP errors into exceptions -- 

            jr = self._parseJson(post_url, r.content)
            had_error = jr.get('had_error', False)
            if had_error:
                FatalError(4, "Error from server: %s" % jr)
                return 

            return jr
        except requests.exceptions.Timeout:
            FatalError(4, "timed out trying to load csv file...")
#        except requests.exceptions.RetryError:
        except requests.exceptions.HTTPError as err:
            FatalError(4, "got an http error: %s" % err)
        except requests.RequestException as e:
            FatalError(4, "got an request error... server down?: %s" % e)
        except BaseException as e:
            FatalError(4, "got some other error: %s" % e)
        return { "had_error": True }

    def do_ls(self, hash_name):
        get_url = f"{API_BASE_UPLOAD_URL}/list/{hash_name}"
        r = self.GET(get_url)
        jr = self._parseJson(get_url, r.content)
        return jr


# FIXME: shared with Snowflake; need library
def FatalError(rc, message):
    sys.stdout.flush()
    sys.stderr.flush()
    sys.stderr.write(message)
    sys.stderr.write("\n")
    sys.stderr.flush()
    sys.exit(rc)
    os._exit(rc)
    return

def WarningMessage(message):
    sys.stdout.flush()
    sys.stderr.flush()
    sys.stderr.write(message)
    sys.stderr.write("\n")
    sys.stderr.flush()
    return

def do_first_load(name, file_name):
    if name is None:
        WarningMessage("No --name; will auto-assign a name")
    if file_name is None:
        WarningMessage("No file specified; will read from stdin")
        FatalError(3, "reading from stdin is not yet supported -- put it in a file for now!")
    else:
        if not os.path.exists(file_name):
            FatalError(2, "No file found at local path %s" % file_name)

    up = Upload()
    jr = up.load_file("first", file_name, name)
    if jr.get('had_error', False):
        FatalError(5, "Error: %s" % jr)
    bytes_sz = jr.get('bytes', 'unknown')
    hash_id = jr.get('hash_id', 'unknown')
    print("Server received %s bytes" % bytes_sz)
    print(f"YOUR NEW diff set id is: {hash_id}")
    print(f"VIEW: {API_BASE_URL}/view/{hash_id}")
    return

def do_append(append_hash, name, file_name):
    #print("__%s__, __%s__, __%s__" % (append_hash, name, file_name))
    if name is None:
        WarningMessage("No --name; will auto-assign a name")
    if file_name is None:
        WarningMessage("No --file specified; will read from stdin")
    
    # Make sure file exists if it is not None
    if file_name is not None:
        if not os.path.exists(file_name):
            FatalError(2, "No file found at local path %s" % file_name)
    up = Upload()
    up.load_file("append", file_name, name, append_hash)
    print("View your bucket diff at %s/#view/%s" % (API_BASE_URL, append_hash))
    
    return

def do_ls(ls_name):
    print("TODO: get list for %s" % ls_name)
    up = Upload()
    jr = up.do_ls(ls_name)
    print(jr)
    return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--append",     help="Append to the specified hash.")
    ap.add_argument("--label",       help="Specify a label for this JSON document")
    ap.add_argument("--file",       help="File to append or upload.")
    #ap.add_argument("--ls",         help="List the documents for a given hash.")

    args = ap.parse_args()
    if args.append:
        #if args.ls:
        #    FatalError(1, "Cannot use --ls with --append")
        do_append(args.append, args.label, args.file)
    else:
        ap.print_help()
    #elif args.ls:
    #    if args.name:
    #        FatalError(1, "Cannot use --name with --ls")
    #    do_ls(args.ls)
    #else:
    #    do_first_load(args.name, args.file)


if __name__ == "__main__":
    main()


