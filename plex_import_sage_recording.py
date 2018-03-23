#!/usr/bin/python2

# Copyright Grant B. Edwards  grant.b.edwards@gmail.com
#
# This code is provided as-is, and I don't guarantee it does anything
# useful. I assume no responsibilty or liability for anything that
# happens when you run it.  You are allowed to do anything you want
# with this code.  You can modify it, copy some or all of it into your
# own app (with or without the above copyright notice).  You can sell
# it or give it to anybody.

import sys,requests,json,os,argparse,errno

# Convert from "ThisIsTheName" to "This Is The Name"
def expand_camelcase(s):
    r = ''
    for c in s:
        if c.isupper() and r:
            r += ' '
        r += c
    return r

# split function that allows delimiter to be escaped with a backslash
def escape_split(s, delim):
    i, res, buf = 0, [], ''
    while True:
        j, e = s.find(delim, i), 0
        if j < 0:  # end reached
            return res + [buf + s[i:]]  # add remainder
        while j - e and s[j - e - 1] == '\\':
            e += 1  # number of escapes
        d = e // 2  # number of double escapes
        if e != d * 2:  # odd number of escapes
            buf += s[i:j - d - 1] + s[j]  # add the escaped char
            i = j + 1  # and skip it
            continue  # add more to buf
        res.append(buf + s[i:j - d])
        i, buf = j + len(delim), ''  # start after delim

# Try to find metadata tags at end of a SageTv recording file.
# Returns a dictionary with tag-name as key and tag-value as value.
# Returns None if no metadata tags are found
def get_metadata(filename):
    suffix = filename.split('.')[-1]
    f = open(filename,"rb")
    stepsize = 8
    offset = 0
    metadata = ''
    while 'META' not in metadata:
        offset -= stepsize
        if offset < -50000:
            # print 'No metadata found in %s' % filename
            return None
        f.seek(offset,2)
        metadata = f.read(stepsize) + metadata
        #print "offset=%d metadata='%s'" % (offset,metadata)
    f.close()
    metadata = metadata.split('META',1)[1]
    tags = {}
    for s in escape_split(metadata,';'):
        if '=' in s:
            key,value = s.split('=',1)
            tags[key] = value
    return tags

# Define a shorthand pretty-printer for debugging
import pprint
pp = pprint.PrettyPrinter(indent=2).pprint

# Enable this code to log TheTVDB requests/responses 
if 0:
    import logging
    import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

# return string with everything except alpha-numeric characters
# removed
def my_strip(s):
    return ''.join(ch.lower() for ch in s if ch.isalnum())

# fuzzy match of two titles (ignores whitespace, punctuation, symbols)
def fuzzy_match(s1,s2):
    if s1 is None or s2 is None:
        return False
    return my_strip(s1) == my_strip(s2)

# class used to query TheTvDb
class TheTvDb(object):
    def __init__(self, apikey, userkey, username):
        self.token = None
        self.series_data = {}
        self.url = 'https://api.thetvdb.com/'
        r = requests.post(self.url+'login', json={"apikey": apikey,
                                                  "userkey": userkey,
                                                  "username": username})
        if r.status_code != 200:
            print "database login failure:"
            print r.text
        else:
            rd = json.loads(r.text)
            # print rd
            self.token = rd['token']
            # print self.token
            self.headers = {"Authorization": "Bearer "+self.token}

    # lookup a series and return all of the season/episode data for it
    def lookup_series(self, series_title):
        r = requests.get(self.url+'search/series', params={'name': series_title}, headers=self.headers)
        if r.status_code == 404:
            print 'series "%s" not found' % series_title
            return None
        
        if r.status_code != 200:
            print "lookup_series error:"
            print r.text
            return None
        rd = json.loads(r.text)
        series_found = rd['data']
        n = len(series_found)
        if n == 1:
            id = series_found[0]['id']
        elif n > 1:
            print "%d series found" % n
            for i in range(n):
                print "%d    %s" % (i, series_found[i]['seriesName'])
            while True:
                s = raw_input('Enter 0-%d or n for none: ' % (n-1))
                if s in 'nN':
                    return None
                id = series_found[int(s)]['id']
                break
        print "'%s' series id: %s" % (series_title,id)

        data = []
        
        for pnum in range(1,100):
            r = requests.get(self.url+'series/%s/episodes' % id,
                             params={'id':id, 'page':pnum},
                             headers=self.headers)
            if r.status_code == 200:
                data += json.loads(r.text)['data']
            elif r.status_code == 404:
                break
            else:
                print r.status_code
                print r.text
                break

        print "data loaded for %d episodes" % len(data)
        return data

    # Lookup an episode based on series title and eposide title return
    # dictionary containing the useful subset of the data similar to
    # that returned by the sagetv metadata lookup function at the top
    # of the file.  It caches series data that's fetched by the
    # function above.
    def lookup(self, series_title, episode_title):
        if series_title not in self.series_data:
            self.series_data[series_title] = self.lookup_series(series_title)
        if not self.series_data[series_title]:
            return None
        sd = self.series_data[series_title]
        episodes = [e for e in sd if fuzzy_match(e['episodeName'],episode_title)]
        if len(episodes) == 1:
            return {'Title': series_title,
                    'EpisodeName': episodes[0]['episodeName'],
                    'SeasonNumber': episodes[0]['airedSeason'],
                    'EpisodeNumber': episodes[0]['airedEpisodeNumber']}
        if len(episodes) > 1:
            print 'Multiple episodes match:'
            for e in episodes:
                print '  ',e['episodeName']
            return None

        return None

# You must fill in legit values here to access TheTvDb.
db = TheTvDb(apikey='YOUR-HEX-APIKEY', userkey='YOUR-HEX-USERKEY', username='your.username')


# conversion of some series titles that cause problems
known_series = {
    "nova": "NOVA",
    "secretsofthedead": "Secrets of the Dead",
    "endeavouronmasterpiece": "Endeavour",
    "laworder": "Law & Order",
    }

# Lookup episode data in TheTvDb by extracting series title and episode title
# from SageTv recording file name.
def lookup_metadata(filename):
    tags = {}
    filename = os.path.basename(filename)
    series,episode = filename.split('-')[0:2]
    if my_strip(series) in known_series:
        series = known_series[my_strip(series)]
    else:
        series = expand_camelcase(series)
    episode = expand_camelcase(episode)
    return db.lookup(series,episode)
    return tags

# Check to see if 'tags' dictionary contains the info we need to
# import into Plex.
def tagsOK(tags):
    if not tags:
        return False
    if 'SeasonNumber' not in tags:
        return False
    if 'EpisodeNumber' not in tags:
        return False
    if 'Title' not in tags:
        return False
    return True

# If called as 'dumpseries', we just lookup a series at TheTvDb and
# dump all the data to stdout
if 'dumpseries' in sys.argv[0]:
    sd = db.lookup_series(sys.argv[1])
    if sd:
        with open(sys.argv[2],"w") as f:
            for e in sd:
                if e['episodeName']:
                    f.write(e['episodeName'].encode("utf8") + '\n')
    sys.exit(0)

# The --libpath option is the path of the root of Plex "Library" under
# which we will create required subdirs and place recording files

# The --pretend option does the lookup and figures out the destination
# path and filename but does not actualy move the file.

parser = argparse.ArgumentParser(description='Plex file importer')
parser.add_argument('--libpath', dest='libpath', type=str, required=True)
parser.add_argument('--pretend', dest='pretend', action='store_true')
parser.add_argument('filenames', metavar='file', type=str, nargs='+')

args = parser.parse_args()

for filename in args.filenames:

    # fetch SageTv metadata from end of file
    tags = get_metadata(filename)
    
    if not tagsOK(tags):
        # try to look it up in TheTvDb
        tags = lookup_metadata(filename)
        
    if not tagsOK(tags):
        print 'Failed to get/lookup metadata for %s' % filename
        continue

    # we know all the info we need to constuct Plex library path and
    # filename.
    snum = int(tags['SeasonNumber'])
    enum = int(tags['EpisodeNumber'])
    suffix = filename.split('.')[-1]
    newfilename = '%s - S%02dE%02d - %s.%s' % (tags['Title'], snum, enum, tags['EpisodeName'], suffix)
    newfilename = newfilename.replace('/',' ')
    path = "%s/%s/Season %02d" % (args.libpath, tags['Title'], snum)
    dest = "%s/%s" % (path,newfilename)
    print dest

    if args.pretend:
        continue

    # create destination directory(s)
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    try:
        os.unlink(dest)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

    # move the file to the new location
    os.rename(filename,dest)

    

    
