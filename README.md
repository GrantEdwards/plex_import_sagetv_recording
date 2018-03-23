## plex_import_sage_recording

plex_import_sage_recording.py is a simple Python-2 command-line
application I wrote to import SageTv DVR recordings into PlexDVR.
It was written to run on Linux. I don't remember doing anything that's
Linux-specific, so there's a good chance it will work on Windows
(maybe with some minor tweaking).

It gets metadata from one of two places:

 1. It looks for metadata tags that newer versions of the SageTv
    backend appends to the ATSC transport stream recording files. If
    present, those tags contain series name, eipsode name, season and
    episode numbers.

 2. If SageTv metadata tags aren't found, then it assumes that the
    existing filename is in a specific format used by SageTv
    comprising the series name and episode title. Then it connects to
    TheTvDb to try to try to look up season and episode numbers (which
    are required by Plex).

Once it has the series name, season number, and episode number, it
creates directories expected by Plex and moves the recording into the
correct place with the filename as expected by Plex.

In the end, it worked for most of the old recordings, and the rest I
just moved manually.

If you what TheTvDB stuff to work, you'll need to sign up for a
developer/application key at https://www.thetvdb.com/ and then modify
the source code to fill in your apikey, userkey, and username:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# You must fill in legit values here to access TheTvDb.
db = TheTvDb(apikey='YOUR-HEX-APIKEY', userkey='YOUR-HEX-USERKEY', username='your.username')

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### Usage

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

$ plex_import_sagetv_recording.py --libpath=/Plex/Old [--pretend] <sage-recording-file> [...]

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
