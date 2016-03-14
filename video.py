import glob
import os
import argparse

parser = argparse.ArgumentParser(
    description='renames video files from HTC One S in specified folder')
parser.add_argument(
    'path', help='path to the directory containing .mp4 videos')
args = parser.parse_args()

os.chdir(os.path.abspath(args.path))
vidlist = glob.glob('VIDEO*.mp4')
for vid in vidlist:
    print(vid)
    description = input("What's in this video? ")
    vidname = vid[6:9] + ' ' + description + '.mp4'
    os.rename(vid, vidname)
