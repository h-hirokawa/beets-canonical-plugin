import string
import sys

import mediafile
from beets.plugins import BeetsPlugin


class RewritePlugin(BeetsPlugin):
    artists_fields = (u'artist', u'albumartist')

    def __init__(self, *args, **kwargs):
        super(RewritePlugin, self).__init__(*args, **kwargs)
        self.config.add({
            'artist_credit': False,
            'albumartist_credit': False,
            'original_date': False,
            'album_disambig': False
        })
        self.register_listener('album_imported', self.album_imported)
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
        for df in ('year', 'month', 'day'):
            self.add_media_field(
                '{}_canonical'.format(df), getattr(date_canonical, '{}_field'.format(df))()
            )

    def write(self, item, path, tags):
        for field in self.artists_fields:
            canonical_field = '{}_canonical'.format(field)
            credit_field = '{}_credit'.format(field)
            tags[canonical_field] = item[canonical_field] = item[field]
            if self.config[credit_field]:
                tags[field] = item[field] = item[credit_field] or item[field]
        for df in ('year', 'month', 'day'):
            canonical_date_field = '{}_canonical'.format(df)
            tags[canonical_date_field] = item[canonical_date_field] = item[df]
            if self.config['original_date']:
                tags[df] = item[df] = item['original_{}'.format(df)]
        if self.config['album_disambig']:
            tags['album'] = item.evaluate_template('$album%aunique{albumartist album, albumtype albumdisambig original_year country year}')

    def album_imported(self, lib, album):
        item = album.items()[0]
        for f in ('albumartist', 'year', 'month', 'day'):
            album[f] = item[f]
            album['{}_canonical'.format(f)] = item['{}_canonical'.format(f)]
        album.store()
