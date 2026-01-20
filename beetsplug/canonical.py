import string
import sys

import mediafile
from beets.plugins import BeetsPlugin


class CanonicalPlugin(BeetsPlugin):
    artists_fields = (u'artist', u'albumartist')

    def __init__(self, *args, **kwargs):
        super(CanonicalPlugin, self).__init__(*args, **kwargs)
        self.config.add({
            'artist_credit': False,
            'albumartist_credit': False,
            'original_date': False,
            'album_disambig': False
        })
        self.register_listener('albuminfo_received', self.albuminfo_received)
        # self.register_listener('album_imported', self.album_imported)
        self.register_listener('write', self.write)

        for field in self.artists_fields:
            canonical = field + u'_canonical'
            canonical_desc = ' '.join(s.capitalize() for s in canonical.split(u'_'))
            media_field = mediafile.MediaField(
                mediafile.MP3DescStorageStyle(canonical_desc),
                mediafile.MP4StorageStyle(u"----:com.apple.iTunes:{}".format(canonical_desc)),
                mediafile.StorageStyle(canonical.upper()),
                mediafile.ASFStorageStyle('beets/{}'.format(canonical_desc)),
            )
            self.add_media_field(canonical, media_field)
        date_canonical = mediafile.DateField(
            mediafile.MP3DescStorageStyle(u'Date Canonical'),
            mediafile.MP4StorageStyle('----:com.apple.iTunes:Date Canonical'),
            mediafile.StorageStyle('DATE_CANONICAL'),
            mediafile.ASFStorageStyle('WM/Date Canonical'))
        self.add_media_field('date_canonical', date_canonical)
        for df in ('year', 'month', 'day'):
            self.add_media_field(
                '{}_canonical'.format(df), getattr(date_canonical, '{}_field'.format(df))()
            )

        original_date_alt = mediafile.DateField(
            mediafile.MP4StorageStyle('----:com.apple.iTunes:ORIGINALDATE'))
        self.add_media_field('original_date_alt', original_date_alt)
        for df in ('year', 'month', 'day'):
            self.add_media_field(
                'original_{}_alt'.format(df), getattr(original_date_alt, '{}_field'.format(df))()
            )

    def write(self, item, path, tags):
        for field in ("date_canonical", "original_date_alt"):
            if field in tags:
                tags.pop(field)

    def album_imported(self, lib, album):
        item = album.items()[0]
        for f in ('albumartist', 'year', 'month', 'day'):
            album[f] = item[f]
            album['{}_canonical'.format(f)] = item['{}_canonical'.format(f)]
        album.store()

    def albuminfo_received(self, info):
        info['albumartist_canonical'] = info.get('artist')
        if self.config['albumartist_credit']:
            info['artist'] = info['artist_credit']

        for df in ('year', 'month', 'day'):
            canonical_date_field = '{}_canonical'.format(df)
            original_date_field = 'original_{}'.format(df)
            original_date_alt_field = 'original_{}_alt'.format(df)
            if info[df]:
                info[canonical_date_field] = str(info[df])
            if info[original_date_field]:
                info[original_date_alt_field] = str(info[original_date_field])
            if self.config['original_date']:
                info[df] = info[original_date_field]

        for track in info['tracks']:
            track['artist_canonical'] = track['artist']
            if self.config['artist_credit']:
                track['artist'] = track['artist_credit']
        # if self.config['album_disambig']:
        #     info['album'] = item.evaluate_template('$album%aunique{albumartist album, albumtype albumdisambig original_year country year}')
