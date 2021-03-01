#!/bin/python3
from bs4 import BeautifulSoup
import concurrent.futures
import requests
import argparse
import os
import shutil

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('link', help='link to the album on khinsider')

parser.add_argument('-d', '--delete',
                    dest='delete_dir', action='store_true',
                    help='delete album folder if it already exists')

parser.add_argument('-m', '--mp3',
                    dest='mp3', action='store_true',
                    help='downloads mp3s (default is flac)')

parser.add_argument('-e', '--enumerate',
                    dest='ordered', action='store_true',
                    help='number all the songs (format "## - name")')

parser.add_argument('-o', '--output-dir',
                    dest='output_dir', default='./',
                    help='directory to output to')

args = parser.parse_args()

# get main page
album_page = BeautifulSoup(requests.get(args.link).content, features="lxml")

# get album name and make folder
album_name = album_page.find('p', {'align' : 'left'}).find('b').text
try: os.mkdir(args.output_dir + album_name)
except FileExistsError:
    if args.delete_dir: choice = 'y'
    else: choice = input("Folder {} already exists. Delete it? (y/n): "\
                         .format(album_name))
    if choice == 'y':
        shutil.rmtree(args.output_dir + album_name)
        os.mkdir(args.output_dir + album_name)
    else: exit()

os.chdir(album_name)

# download album cover
cover = album_page.find_all(
    'a', {"target" : "_blank"}, href=True)[-1].get('href')

with open('cover.jpg', 'wb') as out:
    out.write(requests.get(cover).content)

# get links
website = 'https://downloads.khinsider.com'
links = [website + link.find('a', href=True).get('href')\
         for link in album_page\
         .find_all('td', {'class' : 'playlistDownloadSong'})]

names = ["{:02} - ".format(i + 1) if args.ordered else ""\
         for i in range(len(links))]

# check flac availability
header = album_page.find('tr', {'id' : 'songlist_header'}).text
audio_format   = 1
file_extension = '.flac'
if args.mp3 or 'FLAC' not in header:
    audio_format   = 0
    file_extension = '.mp3'


def download(name, link):    
    page = BeautifulSoup(requests.get(link).content, features="lxml")

    link = [link for link in page\
            .find_all('a', {"style" : "color: #21363f;"}, href=True)]\
            [audio_format].get('href')

    name += [p for p in page.find_all('p', {"align" : "left"})]\
        [-1].text.splitlines()[-1].split(": ", 1)[-1] + file_extension


    data = requests.get(link).content
    with open(name, 'wb') as output_file:
        output_file.write(data)

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(download, names, links)
