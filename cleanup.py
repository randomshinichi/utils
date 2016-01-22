#!/usr/local/bin/python3

from multiprocessing import Pool
import os
import re
import subprocess
import logging
import pdb
import argparse


def cap(s, l):
    return s if len(s) <= l else s[:l]


def build_filelist(path, extensions):
    filelist = []

    for dirpath, subdirs, files in os.walk(path):
        for f in files:
            if os.path.splitext(f)[1].lower() in extensions:
                filelist.append(os.path.join(dirpath, f))
    return filelist


def ffmpeg(filename):

    def is_error_serious(error):
        if re.search('non monotonically increasing dts to muxer', error):
            return None
        else:
            return error

    def process(error):
        # strip trailing \n, convert \n in middle of string to space
        error = re.sub('\n', ' ', report.stderr.decode('utf8')[:-1])
        return error

    report = subprocess.run(["ffmpeg", "-v", "error", "-i", filename,
                             "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if report.stderr:
        error = process(report.stderr)
        serious = is_error_serious(error)
        if serious:
            print('videos: corrupt file', filename)
            return (filename, error)
    return None


def identify(filename):
    report = subprocess.run(
        ["identify", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if report.returncode == 1:
        print('images: corrupt file', filename)
        return (filename, report.stderr[:-1].decode('utf8'))


def finders_deleters():
    finders = [
        (["find", os.getcwd(), "-name", "._*", "-print", "-delete"],
         'Mac resource forks'),
        (["find", os.getcwd(), "-name", ".mediaartlocal", "-print", "-delete"],
         '.mediaartlocal'),
        (["find", os.getcwd(), "-name", "*.url", "-print", "-delete"],
         'useless .url files')
    ]

    for f in finders:
        cmd = f[0]
        message = f[1]
        if args.pretend:
            message = 'Pretend ' + message
            cmd.pop()
        print(message)
        report = subprocess.run(cmd, stdout=subprocess.PIPE)
        logging.info(message)


def lowercase_file_extensions():
    message = 'lowercase file extensions'
    if args.pretend:
        message = 'Pretend ' + message
    print(message)

    for dirpath, subdirs, files in os.walk(datadir):
        for f in files:
            dot_position = f.rfind('.')
            if dot_position > 0 and f[dot_position:].isupper():
                file_with_UPPEREXT = os.path.join(dirpath, f)
                new_filename_lowerext = os.path.join(
                    dirpath, f[:dot_position] + f[dot_position:].lower())
                if args.pretend:
                    logging.warning(
                        'Pretend renamed {} to {}'.format(file_with_UPPEREXT, new_filename_lowerext))
                else:
                    os.rename(file_with_UPPEREXT, new_filename_lowerext)
                    logging.warning(
                        'renamed {} to {}'.format(file_with_UPPEREXT, new_filename_lowerext))


def validate_images():
    print('validating images')

    extensions = ('.jpg', '.png', '.bmp', '.tif', '.tiff')
    filelist = build_filelist(datadir, extensions)

    with Pool(8) as pool:
        result = pool.map(identify, filelist)
        result = [x for x in result if x is not None]
        result.sort()
        for r in result:
            # some errors may not include the filename, which is why the
            # filename is still included here
            logging.error('{}\t{}'.format(r[0], r[1]))


def validate_videos():
    pictures_path = datadir
    print('validating videos in', pictures_path)

    extensions = ('.avi', '.mp4', '.mkv')
    filelist = build_filelist(pictures_path, extensions)

    problematic_files = []
    for f in filelist:
        result = ffmpeg(f)
        if result:
            problematic_files.append(result)

    for p in problematic_files:
        logging.error('{}\t{}'.format(p[0], cap(p[1], 150) + '...'))


parser = argparse.ArgumentParser(
    description='Cleans up the given directory and validates images and videos')
parser.add_argument('-p', '--pretend', action="store_true",
                    help='Do not actually delete or rename anything. Only affects finders_deleters() and lowercase_file_extensions()')
parser.add_argument('-v', '--validate', action="store_true",
                    help='Perform image and video validation as well')
parser.add_argument(
    'datadir', help='The directory to clean up. A log will be placed here as well.')
args = parser.parse_args()

datadir = args.datadir
logname = os.path.join(datadir, 'cleanup.log')

os.chdir(datadir)

logging.basicConfig(filename=logname, format='%(asctime)s\t%(levelname)s\t%(message)s',
                    datefmt='%d-%m-%Y %H:%M', level=logging.INFO)
logging.info('STARTED on ' + datadir)

print("working in", datadir)

finders_deleters()
lowercase_file_extensions()
if args.validate:
    validate_images()
    validate_videos()
logging.info('ENDED')
