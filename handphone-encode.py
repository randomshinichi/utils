#!/usr/local/bin/python3

import pdb
import re
import os
import subprocess
import glob
import argparse
from multiprocessing import Pool
from functools import partial
from shutil import rmtree, copytree, ignore_patterns

def is_libfdk_supported():
    ffmpeg = subprocess.run(['ffmpeg', '-encoders'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    libfdk = re.search('.*libfdk_aac.*', ffmpeg.stdout.decode())
    if libfdk:
        print(libfdk.group(0))
        return True
    else:
        return False

def encode(libfdk_aac_present, input_filename):
    if libfdk_aac_present:
        msg = "[libfdk_aac] encoding {}"
    else:
        msg = "[aac] encoding {}"
    print(msg.format(input_filename))

    name, ext = os.path.splitext(input_filename)
    libfdk_aac = ['ffmpeg', '-i', input_filename, '-c:a', 'libfdk_aac', '-vbr', '5', name + '.m4a']
    aac = ['ffmpeg', '-i', input_filename, '-c:a', 'aac', '-b:a', '160k', name + '.m4a']
    # output = subprocess.run(['touch', name + '.m4a'])

    if libfdk_aac_present:
        output = subprocess.run(libfdk_aac, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    else:
        output = subprocess.run(aac, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if output.returncode != 0:
        print("Problem encoding", input_filename)
        print(output.stderr.decode())
    return name + '.m4a'

parser = argparse.ArgumentParser(description='Encodes flac files into m4a for smartphones')
parser.add_argument('source_dir', help='The source music directory with flac files')
parser.add_argument('output_dir', help='The destination to copy the encoded files to')
parser.add_argument('--cpus', help='Number of workers/CPUs to use', default=6)
args = parser.parse_args()


source_dir = os.path.abspath(args.source_dir)
album_dir = os.path.split(source_dir)[1]

output_dir = args.output_dir
output_dir_album = os.path.join(output_dir, album_dir)
os.chdir(source_dir)


print("Building file list")
filelist = glob.glob('*.flac')
if not filelist:
    filelist = glob.glob('**/*.flac', recursive=True)

libfdk = is_libfdk_supported()
partial_encode = partial(encode, libfdk)

filelist_encoded = []
with Pool(args.cpus) as pool:
    filelist_encoded = pool.map(partial_encode, filelist)

print("Copying encoded files to", output_dir_album)
try:
    copytree(source_dir, output_dir_album, ignore=ignore_patterns('*.flac', '._*'))
except FileExistsError:
    print("Album directory already exists at output, rm -rf-ing and retrying")
    rmtree(output_dir_album)
    copytree(source_dir, output_dir_album, ignore=ignore_patterns('*.flac', '._*'))

print("Removing encoded files from original directory")
for f in filelist_encoded:
    subprocess.run(['rm', f])
