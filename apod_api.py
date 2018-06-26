#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2017-04-12 11:15
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
apod_api.py
"""


from __future__ import division
from __future__ import unicode_literals
import os
import sys
import time
import requests
from PIL import Image


APOD_API_BASE = 'https://api.nasa.gov/planetary/apod'
APOD_API_DEV_KEY = 'tHpS8gTsnWxn8Uiz34yLnU3SBIyUcBpJQIWO1L1O'

IMAGE_SETTINGS = {
        'min_file_size': 100,
        'min_dimension': (1400, 900),
        'aspect_ratio_range': (1., 2.),
        }


def image_is_usable(filename, **settings):
    settings = dict(IMAGE_SETTINGS, **settings)
    try:
        image = Image.open(filename)
    except AttributeError:
        _print("cannot check if image is usable, skip")
        return False
    min_w, min_h = settings['min_dimension']
    min_asp, max_asp = settings['aspect_ratio_range']

    w, h = image.size
    asp = w / h
    if w < min_w or h < min_h or asp < min_asp or asp > max_asp:
        _print("image does not meet the requirement of a wallpaper, skip")
        return False
    else:
        return True


def grab_from_apod(dest_dir, date):

    apod = _query_apod(date)
    if 'code' in apod and apod['code'] == 500:
        _print("no resource found, skip")
        return None
    if not apod or apod['media_type'] != 'image':
        return None
    try:
        image_url = apod['hdurl']
    except KeyError:
        _print("no hd url found, use regular url")
        image_url = apod['url']
    image_info = _query_image(image_url)
    if image_info is None:
        return None
    image_stream, filename, file_size = image_info
    if file_size < IMAGE_SETTINGS['min_file_size']:
        _print("response size too small ({0:d})")
        return None
    dest_filename = '_'.join([str(date), filename])
    dest_path = os.path.join(dest_dir, dest_filename)
    # check existence
    if os.path.exists(dest_path):
        _print("file exist: date {0!s}\n {1}".format(date, dest_path))
        return dest_path
    else:
        try:
            with open(dest_path, 'wb') as fo:
                block_count, block_size = 0, 512
                for block in image_stream.iter_content(block_size):
                    time.sleep(0.01)
                    fo.write(block)
                    block_count += 1
                    _print_dl(block_count, block_size, file_size)
        except (Exception, KeyboardInterrupt) as e:
            _print("\raborted, clean up".format(e))
            os.remove(dest_path)
            return None
        _print("\rdone: {0:70s}\n".format(_hr_size(file_size)))
        _print("apod image grabbed: date {0!s}\n  {1:s}".format(
            date, dest_path))
        # post process
        overlay_text(dest_path, apod['title'])
    return dest_path


def overlay_text(filename, text):
    pass


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


def _query_apod(date):
    try:
        date_str = date.strftime('%Y-%m-%d')
        r = requests.get(
                APOD_API_BASE, params={
                    'hd': True,
                    'api_key': APOD_API_DEV_KEY,
                    'date': date_str,
                    })
        return r.json()
    except Exception as e:
        _print("failed to query apod with exception {0!s}".format(e))
        return {}


def _query_image(image_url):
    try:
        r = requests.get(image_url, stream=True)
        filename = os.path.basename(image_url)
        file_size = float(r.headers['content-length'])
        return r, filename, file_size
    except Exception as e:
        _print("failed to query image url with exception {0!s}".format(e))
        return None


def _hr_size(size_bytes):
    for x in ['bytes', 'KB', 'MB']:
        if size_bytes < 1024.0:
            return "%3.2f%s" % (size_bytes, x)
        size_bytes /= 1024.0


def _print(string):
    if True:
        if string.startswith('\r'):
            sys.stdout.write(string)
            sys.stdout.flush()
        else:
            print(string)


def _print_dl(block_count, block_size, total_size, prefix='retrieving...'):
    written_size = _hr_size(block_count * block_size)
    total_size = _hr_size(total_size)
    progress = '{0:s} {1:s} of {2:s}'.format(
            prefix, written_size, total_size)
    _print("\r{0:79s}".format(progress))


if __name__ == "__main__":
    import datetime
    dest_dir = '.'
    grab_from_apod(dest_dir, datetime.date.today())
