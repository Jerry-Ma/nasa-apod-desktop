#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2014-01-11 11:21
# Python Version :  2.7.5
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
apod_util.py

An apod image grabber that essentially is reusing of the work
done by David Drake.
"""
#see blow for original copy of license
#
# Copyright (c) 2012 David Drake
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# nasa_apod_desktop.py
# https://github.com/randomdrake/nasa-apod-desktop
#
# Written/Modified by David Drake
# http://randomdrake.com
# http://twitter.com/randomdrake
#
#
# Tested on Ubuntu 12.04
#
# ... (truncated here)

from __future__ import division
import os
import re
import urllib
import urllib2
import random
import subprocess
import sys

from PIL import Image
from lxml import etree


NASA_APOD_SITE = 'http://apod.nasa.gov/apod/'
IMAGE_SIZE_THRES = 1024 * 10   # minimal size of downloaded image file
IMAGE_DIM_THRES = (1366, 768)  # minimal dimension of image that is good for bg
IMAGE_ASPECT_RATIO_THRES = 4/3
IMAGE_DURATION = 1200  # scroll speed of bg slideshow (s)


def message(string):
    # switchable message
    if True:
        if string.startswith('\r'):
            sys.stdout.write(string)
            sys.stdout.flush()
        else:
            print string


def list_image_file(path):

    image = []
    for i in os.listdir(path):
        i = os.path.join(path, i)
        try:
            Image.open(i)
            image.append(i)
        except IOError:
            pass
    return image


def image_can_be_bg(filename):
    try:
        image = Image.open(filename)
    except AttributeError:
        return False
    current_x, current_y = image.size
    aspect_ratio = current_x / current_y
    if current_x < IMAGE_DIM_THRES[0] or current_y < IMAGE_DIM_THRES[1]\
            or aspect_ratio < IMAGE_ASPECT_RATIO_THRES:
        message("apod image today not suitable for wallpaper, skip")
        return False
    else:
        return True


def download_site_html(url):

    opener = urllib2.build_opener()
    req = urllib2.Request(url)
    try:
        response = opener.open(req)
        reply = response.read()
    except urllib2.HTTPError, error:
        message("error at {0:s}\n{0:s}".format(url, error.code))
        reply = None
    return reply


def get_image_info(element, text):
    regex = '<' + element + '="(image.*?)"'
    reg = re.search(regex, text, re.IGNORECASE)
    if reg:
        if 'http' in reg.group(1):
            # Actual URL
            file_url = reg.group(1)
        else:
            # Relative path, handle it
            file_url = NASA_APOD_SITE + reg.group(1)
    else:
        return None, None, None
    remote_file = urllib.urlopen(file_url)
    filename = os.path.basename(file_url)
    file_size = float(remote_file.headers.get("content-length"))
    return file_url, filename, file_size


def human_readable_size(number_bytes):
    for x in ['bytes', 'KB', 'MB']:
        if number_bytes < 1024.0:
            return "%3.2f%s" % (number_bytes, x)
        number_bytes /= 1024.0


def print_download_status(block_count, block_size, total_size):
    written_size = human_readable_size(block_count * block_size)
    total_size = human_readable_size(total_size)
    progress = '{0:s} bytes of {1:s}'.format(written_size, total_size)
    message("\r{0:79s}".format(progress))
    #stdout.flush()


def grab_from_apod(path, date):

    site_url = '{0:s}ap{1:s}.html'.format(NASA_APOD_SITE,
                                          date.strftime('%y%m%d'))
    html_content = download_site_html(site_url)
    if html_content is None:
        return None
    file_url, filename, file_size = get_image_info('a href', html_content)
    if file_url is None:
        message("image cannot be located at the site (may be a video today)")
        return None
    save_to = os.path.join(path, '_'.join([str(date), filename]))
    if os.path.isfile(save_to) and os.path.getsize(save_to) > IMAGE_SIZE_THRES:
        message("apod image exists: date {0!s}\n  {1:s}"
                .format(date, os.path.basename(save_to)))
    else:
        if file_size < IMAGE_SIZE_THRES:
            message("response size too small ({0:d}), try from image source"
                    .format(file_size))
            file_url, filename, file_size = get_image_info('img src',
                                                           html_content)
            if file_url is None or file_size < IMAGE_SIZE_THRES:
                message("image cannot be located at the site "
                        "(may be a video today)")
                return None

        message("{0:79s}".format('retrieving image'))
        urllib.urlretrieve(file_url, save_to, print_download_status)
        message("\rdone: {0:70s}".format(human_readable_size(file_size)))
        message("apod image grabbed: date {0!s}\n  {1:s}"
                .format(date, os.path.basename(save_to)))
    return save_to


def compose_bg_scroll(filename):
    # Create our base, background element
    background = etree.Element("background")
    images = list_image_file(os.path.dirname(filename))
    random.shuffle(images)

    for i, image in enumerate(images):
        # Create a static entry for keeping this image here for IMAGE_DURATION
        static = etree.SubElement(background, "static")
        # Length of time the background stays
        duration = etree.SubElement(static, "duration")
        duration.text = str(IMAGE_DURATION)

        # Assign the name of the file for our static entry
        static_file = etree.SubElement(static, "file")
        static_file.text = image

        # Create a transition for the animation with a from and to
        transition = etree.SubElement(background, "transition")

        # Length of time for the switch animation
        transition_duration = etree.SubElement(transition, "duration")
        transition_duration.text = "5"

        # We are always transitioning from the current file
        transition_from = etree.SubElement(transition, "from")
        transition_from.text = image

        # Create our tranition to element
        transition_to = etree.SubElement(transition, "to")
        try:
            transition_to.text = images[i + 1]
        except IndexError:
            transition_to.text = images[0]

    xml_tree = etree.ElementTree(background)
    xml_tree.write(filename, pretty_print=True)
    message('composed scrolling configuration -> {0:s}'.format(filename))


def set_gnome_wallpaper(filename):
    command = ["gsettings", "set", "org.gnome.desktop.background",
               "picture-uri", "file://{0:s}".format(filename)]
    subprocess.check_call(command)
    message('wallpaper set to: {0:s}'.format(os.path.basename(filename)))
