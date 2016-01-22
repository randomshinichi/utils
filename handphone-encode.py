#!/usr/local/bin/python3

import pdb
import os
import subprocess
import glob
import argparse
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

filelist_encoded = []
with Pool(args.cpus) as pool:
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
