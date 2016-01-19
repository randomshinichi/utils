#!/usr/local/bin/python3
"""
Usage: python3 scriptname.py (album directory) (cpus to use)
"""

import pdb
import os
import sys
import subprocess
import glob
from multiprocessing import Pool
from shutil import rmtree, copytree, ignore_patterns


def encode(input_filename):
    print("Encoding", input_filename)
    name, ext = os.path.splitext(input_filename)
    output = subprocess.run(['touch', name + '.m4a'])
    # output = subprocess.run(['ffmpeg', '-i', input_filename, '-c:a', 'libfaac', '-q:a', '100', name + '.m4a'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if output.returncode != 0:
        print("Problem encoding", input_filename)
    return name + '.m4a'

source_dir = os.path.abspath(sys.argv[1])
album_dir = os.path.split(source_dir)[1]
try:
    cpus = int(sys.argv[2])
except:
    cpus = 6

output_dir = '/Users/andrewchiw/staging'
output_dir_album = os.path.join(output_dir, album_dir)
os.chdir(source_dir)

print("Building file list")
filelist = glob.glob('*.flac')
if not filelist:
    filelist = glob.glob('**/*.flac', recursive=True)

filelist_encoded = []
with Pool(cpus) as pool:
    filelist_encoded = pool.map(encode, filelist)

print("Copying encoded files to", output_dir_album)
try:
    copytree(source_dir, output_dir_album, ignore=ignore_patterns('*.flac', '._*'))
except FileExistsError:
    print("Album directory already exists at output, removing and retrying")
    rmtree(output_dir_album)
    copytree(source_dir, output_dir_album, ignore=ignore_patterns('*.flac', '._*'))

print("Cleaning up original directory")
for f in filelist_encoded:
    subprocess.run(['rm', f])
