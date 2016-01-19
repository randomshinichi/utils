#!/usr/local/bin/python3
"""
Asks what would I like to rename the folder to (because sometimes artist - album is not good, for classical, anime OSTs, singles...)
verifies them
copies the folder to /data/music with new folder name if specified
does the file renaming inside destination folder
"""

import os
import sys
import subprocess
import xml.etree.ElementTree as ET
import shutil
import re
import argparse
import pdb


def cap(s, l):
    return s if len(s) <= l else s[:l]


def buildfilelist(exts, directory):
    filelist = []
    for dirpath, subdirs, files in os.walk(directory):
        for f in files:
            if os.path.splitext(f)[1].lower() in exts:
                filelist.append(os.path.join(dirpath, f))
    return filelist


def extract_metadata(f):
    result = subprocess.run(
        ['mediainfo', '--Output=XML', f], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    stdout = result.stdout.decode('utf8')
    root = ET.fromstring(stdout)
    try:
        artist = root.findall(
            './File/track[@type=\'General\']/Performer')[0].text
        tracknumber = root.findall(
            './File/track[@type=\'General\']/Track_name_Position')[0].text
        # Try and sanitize the tracknumber
        # Can't do auto track number because this script may operate on an
        # ALBUM/CD1-CD2-CD3 tree
        tracknumber = re.sub('[^0-9]', '', tracknumber)
        tracknumber = str(tracknumber).zfill(2)
        title = root.findall(
            './File/track[@type=\'General\']/Track_name')[0].text
        # Sanitize the title, goddamn this is dangerous
        title = re.sub(r'"|=|-|&|#|@|\*|/|\\|\^', ' ', title)
    except IndexError:
        print("couldn't read metadata from", f)
        return None
    return (artist, tracknumber, title)


def buildactionlist(f):
    directory, original_filename = os.path.split(f)
    ext = os.path.splitext(f)[1]

    try:
        artist, tracknumber, title = extract_metadata(f)
    except TypeError:
        return None

    # Build new filename from metadata
    if renaming_scheme == 'TT':
        new_filename = tracknumber + ' ' + title + ext
    elif renaming_scheme == 't':
        new_filename = tracknumber + ext
    else:
        return None

    # Check if new filename is the same as the old
    # if so don't return anything
    if original_filename == new_filename:
        print(original_filename, '->', 'unchanged')
    else:
        print(original_filename, '->', new_filename)
        full_original_filename = os.path.join(directory, original_filename)
        full_new_filename = os.path.join(directory, new_filename)
        return full_original_filename, full_new_filename


def verify(filename):

    def is_error_serious(error):
        if re.search('non monotonically increasing dts to muxer', error):
            # this happens in videos, you won't notice it
            return None
        else:
            return error

    def sanitize_error(error):
        # strip trailing \n, convert \n in middle of string to space
        error = re.sub('\n', ' ', report.stderr.decode('utf8')[:-1])
        return error

    report = subprocess.run(["ffmpeg", "-v", "error", "-i", filename,
                             "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if report.stderr:
        error = sanitize_error(report.stderr)
        serious = is_error_serious(error)
        if serious:
            print('audio:', filename, error)
            return (filename, error)
    return None

# creates absolute path from command line argument
parser = argparse.ArgumentParser(description='copies music to destination and renames according to metadata')
parser.add_argument('input', help='the album to copy')
parser.add_argument('target_dir', help='where you want the music to end up')
args = parser.parse_args()
source = os.path.abspath(args.input)
target_dir = os.path.abspath(args.target_dir)

# Directory Rename Question
userinput = input(
    'what would you like to rename it to? [{}] '.format(os.path.split(source)[1]))
if userinput:
    # if /test/source, this strips original_dir away and makes it
    # /test/userinput
    destination = os.path.join(target_dir, userinput)
else:
    # will use source's name if nothing else specified
    destination = os.path.join(target_dir, os.path.split(source)[1])

# Track Rename Question
print('Tracknumber Title/tracknumber only/none')
renaming_scheme = input('Renaming scheme? [TT/t/n] ')
if not renaming_scheme:
    renaming_scheme = 'TT'

# Copy working copy to target directory
print("Copying to {}".format(destination))
try:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('._*'))
except FileExistsError as e:
    raise(e)

# Find audio files
filelist = buildfilelist(('.flac', '.mp3', '.m4a', '.ogg'), destination)

# Verify
"""
print("Verifying")
for f in filelist:
    verify(f)
"""

# Build a list of files that need renaming
actionlist = []
for f in filelist:
    actionlist.append(buildactionlist(f))
actionlist = [a for a in actionlist if a]  # remove Nones in actionlist


# Confirm from user
if renaming_scheme == 'TT' or renaming_scheme == 't':
    userinput = input('Rename files? [y/N] ')
    if userinput == 'y':
        for a in actionlist:
            os.rename(a[0], a[1])
        userinput = input('Remove original directory? [y/N] ')
        if userinput == 'y':
            shutil.rmtree(source)
print("Done")
