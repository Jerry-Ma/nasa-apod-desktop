#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2014-01-11 10:31
# Python Version :  2.7.5
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
apod_grabber.py

An apod image grabber that essentially is reusing of the work
done by David Drake.
"""

import os
import datetime
# import nasa_apod_desktop as apod_util
import apod_api
from apod_api import _print


class ApodRepo(object):

    def __init__(self, root_dir, bg_image_dir="image_use_as_bg",
                 orig_image_dir='image_orig'):

        self.root_dir = os.path.abspath(root_dir)

        self.bg_image_dir = os.path.join(self.root_dir, bg_image_dir)
        self.orig_image_dir = os.path.join(self.root_dir, orig_image_dir)

        self.bg_scroll_file = os.path.join(self.bg_image_dir,
                                           'apod_backgrounds.xml')

        if os.path.isdir(self.root_dir):
            _print('notice: root exist: {0:s}'.format(self.root_dir))
        for i in [self.root_dir, self.bg_image_dir, self.orig_image_dir]:
            if not os.path.isdir(i):
                os.makedirs(i)
                _print('+ {0:s}'.format(i))
        _print('Apod grabber initialized\n-> {0:s}'.format(self.root_dir))

    def link_to_bg_dir(self, image):
        dest = os.path.join(self.bg_image_dir,
                            os.path.basename(image))
        os.symlink(image, dest)
        _print('image linked:\n  {0:s}\n->{1:s}'.format(image, dest))

    def clear_bg_dir(self):
        for i in apod_api.list_image_file(self.bg_image_dir):
            os.unlink(i)
        _print('image link purged: {0:s}'.format(self.bg_image_dir))

    def update_bg_repo(self, capacity=10):
        image_to_use = {}
        date_of_image = datetime.date.today()
        oneday = datetime.timedelta(1)
        while len(image_to_use) < capacity:
            image = apod_api.grab_from_apod(self.orig_image_dir,
                                            date_of_image)
            if apod_api.image_is_usable(image):
                image_to_use[date_of_image] = image
            date_of_image -= oneday
        self.clear_bg_dir()
        for i in image_to_use.values():
            self.link_to_bg_dir(i)
        # apod_api.compose_bg_scroll(self.bg_scroll_file)
        _print('image repo updated, capacity={0:d}'.format(capacity))

    # def set_gnome_wallpaper(self):
        # apod_util.set_gnome_wallpaper(self.bg_scroll_file)


if __name__ == '__main__':
    root = '/Users/ma/Misc/apod_backgrounds'
    apod = ApodRepo(root)
    apod.update_bg_repo(20)
    # apod.set_gnome_wallpaper()
