# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
#
# Copyright (C) 2009 Jonathan Matthew  <jonathan@d14n.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import xml.dom.minidom as dom

import rb
from gi.repository import RB

# musicbrainz URLs
MUSICBRAINZ_RELEASE_URL = "http://musicbrainz.org/ws/2/release/%s?inc=artists"
MUSICBRAINZ_RELEASE_PREFIX = "http://musicbrainz.org/release/"
MUSICBRAINZ_RELEASE_SUFFIX = ".html"

# musicbrainz IDs
MUSICBRAINZ_VARIOUS_ARTISTS = "89ad4ac3-39f7-470e-963a-56509c546377"

# Amazon URL bits
AMAZON_IMAGE_URL = "http://images.amazon.com/images/P/%s.01.LZZZZZZZ.jpg"

class MusicBrainzSearch(object):

	def get_release_cb (self, data, args):
		(key, store, callback, cbargs) = args
		if data is None:
			print "musicbrainz release request returned nothing"
			callback(*cbargs)
			return

		try:
			parsed = dom.parseString(data)

			storekey = RB.ExtDBKey.create_storage('album', key.get_field('album'))

			# check that there's an artist that isn't 'various artists'
			artist_tags = parsed.getElementsByTagName('artist')
			if len(artist_tags) > 0:
				artist_id = artist_tags[0].attributes['id'].firstChild.data
				if artist_id != MUSICBRAINZ_VARIOUS_ARTISTS:
					# add the artist name (as album-artist) to the storage key
					nametags = artist_tags[0].getElementsByTagName('name')
					if len(nametags) > 0:
						artistname = nametags[0].firstChild.data
						print "got musicbrainz artist name %s" % artistname
						storekey.add_field('artist', artistname)


			# look for an ASIN tag
			asin_tags = parsed.getElementsByTagName('asin')
			if len(asin_tags) > 0:
				asin = asin_tags[0].firstChild.data

				print "got ASIN %s" % asin
				image_url = AMAZON_IMAGE_URL % asin

				store.store_uri(storekey, RB.ExtDBSourceType.SEARCH, image_url)
			else:
				print "no ASIN for this release"

			callback(*cbargs)
		except Exception, e:
			print "exception parsing musicbrainz response: %s" % e
			callback(*cbargs)

	def search(self, key, last_time, store, callback, *args):
		key = key.copy()	# ugh
		album_id = key.get_info("musicbrainz-albumid")
		if album_id is None:
			print "no musicbrainz release ID for this track"
			callback(*args)
			return

		if album_id.startswith(MUSICBRAINZ_RELEASE_PREFIX):
			album_id = album_id[len(MUSICBRAINZ_RELEASE_PREFIX):]

		if album_id.endswith(MUSICBRAINZ_RELEASE_SUFFIX):
			album_id = album_id[:-len(MUSICBRAINZ_RELEASE_SUFFIX)]

		print "stripped release ID: %s" % album_id

		url = MUSICBRAINZ_RELEASE_URL % (album_id)
		loader = rb.Loader()
		loader.get_url(url, self.get_release_cb, (key, store, callback, args))