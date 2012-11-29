import os
import helpers

from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

class AudioHelper(object):
  def __init__(self, filename):
    self.filename = filename

def AudioHelpers(filename):
  filename = helpers.unicodize(filename)
  file = os.path.basename(filename)
  (file, ext) = os.path.splitext(file)

  for cls in [ MP3AudioHelper, MP4AudioHelper, FLACAudioHelper, OGGAudioHelper ]:
    if cls.is_helper_for(ext):
      return cls(filename)
  return None

#####################################################################################################################

class MP3AudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, file_extension):
    return file_extension.lower() in ['.mp3']

  def process_metadata(self, metadata):
    
    Log("Reading MP3 tags")
    try: tags = ID3(self.filename)
    except: 
      Log('An error occurred while attempting to parse the MP4 file: ' + filename)
      return

    # Release Date
    try:
      tdrc_tag = tags.getall("TDRC")[0]
      metadata.originally_available_at = Datetime.ParseDate('01-01-' + tdrc_tag.text[0].get_text()).date()
    except:
      pass

    # Genres
    try:
      genres = f.getall('TCON')
      metadata.genres.clear()
      for genre in genres:
        metadata.genres.add(genre)
    except: 
      pass

    # Posters
    valid_posters = []
    for frame in f.getall("APIC"):
      if (frame.mime == 'image/jpeg') or (frame.mime == 'image/jpg'): ext = 'jpg'
      elif frame.mime == 'image/png': ext = 'png'
      elif frame.mime == 'image/gif': ext = 'gif'
      else: ext = ''

      poster_name = hashlib.md5(frame.data).hexdigest()
      valid_posters.append(poster_name)
      if poster_name not in metadata.posters:
        Log('Adding embedded APIC art from mp3 file: ' + filename)
        metadata.posters[posterName] = Proxy.Media(frame.data, ext = ext)
      else:
        Log('Skipping APIC art since its already added')

    return valid_posters

#####################################################################################################################

class MP4AudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, file_extension):
    return file_extension.lower() in ['.mp4','.m4a','.m4p']

  def process_metadata(self, metadata):

    Log('Reading MP4 tags')
    try: tags = MP4(self.filename)
    except: 
      Log('An error occurred while attempting to parse the MP4 file: ' + filename)
      return

    # Genres
    try:
      genres = tags["\xa9gen"][0]
      if len(genres) > 0:
        genre_list = genres.split('/')
        metadata.genres.clear()
        for genre in genre_list:
          metadata.genres.add(genre.strip())
    except: pass

    # Release Date
    try:
      release_date = tags["\xa9day"][0]
      release_date = release_date.split('T')[0]
      parsed_date = Datetime.ParseDate(release_date)
      metadata.originally_available_at = parsed_date.date()
    except: pass

    # Posters
    valid_posters = []
    try:
      data = str(tags["covr"][0])
      poster_name = hashlib.md5(data).hexdigest()
      valid_posters.append(poster_name)
      if poster_name not in metadata.posters:
        Log('Adding embedded coverart from m4a/mp4 file: ' + filename)
        metadata.posters[posterName] = Proxy.Media(data)
      else:
        Log('Skipping coverart since its already added')
    except: pass

    return valid_posters

#####################################################################################################################

class FLACAudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, file_extension):
    return file_extension.lower() in ['.flac']

  def process_metadata(self, metadata):

    Log('Reading FLAC tags')
    try: tags = FLAC(self.filename)
    except:
      Log('An error occurred while attempting to parse the FLAC file: ' + filename)
      return

    # Posters
    valid_posters = []
    for poster in tags.pictures:
      poster_name = hashlib.md5(poster.data).hexdigest()
      valid_posters.append(poster_name)
      if poster_name not in metadata.posters:
        Log('Adding embedded art from FLAC file: ' + filename)
        metadata.posters[posterName] = Proxy.Media(poster.data)
      else:
        Log('Skipping embedded art since its already added')

    return valid_posters

#####################################################################################################################

class OGGAudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, file_extension):
    return file_extension.lower() in ['.ogg']

  def process_metadata(self, metadata):

    Log('Reading OGG tags')
    try: tags = OggVorbis(self.filename)
    except:
      Log('An error occured while attempting to parse the OGG file: ' + filename)

    # Posters
    valid_posters = []
    if tags.has_key('metadata_block_picture'):
      for picture_data in tags['metadata_block_picture']:
        picture = Picture(base64.standard_b64decode(picture_data))

        if (picture.mime == 'image/jpeg') or (picture.mime == 'image/jpg'): ext = 'jpg'
        elif picture.mime == 'image/png': ext = 'png'
        elif picture.mime == 'image/gif': ext = 'gif'
        else: ext = ''

        poster_name = hashlib.md5(picture.data).hexdigest()
        valid_posters.append(valid_posters)
        if poster_name not in metadata.posters:
          Log('Adding embedded art from OGG file: ' + filename)
          metadata.posters[posterName] = Proxy.Media(picture.data, ext = ext)
        else:
          Log('Skipping embedded art since its already added')

    return valid_posters