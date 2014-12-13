import os
import helpers

from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen import File as MFile

class AudioHelper(object):
  def __init__(self, filename):
    self.filename = filename

def AudioHelpers(filename):
  filename = helpers.unicodize(filename)
  tag = MFile(filename, None, True)

  if tag is not None:
    for cls in [ ID3AudioHelper, MP4AudioHelper, FLACAudioHelper, OGGAudioHelper ]:
      if cls.is_helper_for(type(tag).__name__):
        return cls(filename)
  return None

#####################################################################################################################

class ID3AudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ('EasyID3', 'EasyMP3', 'EasyTrueAudio', 'ID3', 'MP3', 'TrueAudio', 'AIFF') # All of these file types use ID3 tags like MP3

  def process_metadata(self, metadata):
    
    Log("Reading ID3 tags")
    try: tags = MFile(self.filename, easy=True)
    except: 
      Log('An error occurred while attempting to read ID3 tags from ' + self.filename)
      return

    # Release Date
    try:
      tdrc_tag = tags.getall("TDRC")[0]
      metadata.originally_available_at = Datetime.ParseDate('01-01-' + tdrc_tag.text[0].get_text()).date()
    except:
      pass

    # Genres
    try:
      genres = tags.getall('TCON')
      metadata.genres.clear()
      for genre in genres:
        metadata.genres.add(genre)
    except: 
      pass

    # Posters
    valid_posters = []
    for frame in tags.getall("APIC"):
      if (frame.mime == 'image/jpeg') or (frame.mime == 'image/jpg'): ext = 'jpg'
      elif frame.mime == 'image/png': ext = 'png'
      elif frame.mime == 'image/gif': ext = 'gif'
      else: ext = ''

      poster_name = hashlib.md5(frame.data).hexdigest()
      valid_posters.append(poster_name)
      if poster_name not in metadata.posters:
        Log('Adding embedded APIC art from mp3 file: ' + self.filename)
        metadata.posters[poster_name] = Proxy.Media(frame.data, ext = ext)
      else:
        Log('Skipping APIC art since its already added')

    return valid_posters

#####################################################################################################################

class MP4AudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ['MP4','EasyMP4']

  def process_metadata(self, metadata):

    Log('Reading MP4 tags')
    try: tags = MFile(self.filename, easy=True)
    except: 
      Log('An error occurred while attempting to parse the MP4 file: ' + self.filename)
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
        Log('Adding embedded coverart from m4a/mp4 file: ' + self.filename)
        metadata.posters[poster_name] = Proxy.Media(data)
      else:
        Log('Skipping coverart since its already added')
    except: pass

    return valid_posters

#####################################################################################################################

class FLACAudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ['FLAC']

  def process_metadata(self, metadata):

    Log('Reading FLAC tags')
    try: tags = FLAC(self.filename)
    except:
      Log('An error occurred while attempting to parse the FLAC file: ' + self.filename)
      return

    # Posters
    valid_posters = []
    for poster in tags.pictures:
      poster_name = hashlib.md5(poster.data).hexdigest()
      valid_posters.append(poster_name)
      if poster_name not in metadata.posters:
        Log('Adding embedded art from FLAC file: ' + self.filename)
        metadata.posters[poster_name] = Proxy.Media(poster.data)
      else:
        Log('Skipping embedded art since its already added')

    return valid_posters

#####################################################################################################################

class OGGAudioHelper(AudioHelper):
  @classmethod
  def is_helper_for(cls, tagType):
    return tagType in ['OggVorbis']

  def process_metadata(self, metadata):

    Log('Reading OGG tags')
    try: tags = OggVorbis(self.filename)
    except:
      Log('An error occured while attempting to parse the OGG file: ' + self.filename)
      return

    # Posters
    valid_posters = []
    if tags.has_key('coverart'):
      for poster in tags['coverart']:
        poster_data = base64.standard_b64decode(poster)
        poster_name = hashlib.md5(poster_data).hexdigest()
        valid_posters.append(poster_name)
        if poster_name not in metadata.posters:
          Log('Adding embedded art from OGG file: ' + self.filename)
          metadata.posters[poster_name] = Proxy.Media(poster_data)
        else:
          Log('Skipping embedded art since its already added')

    return valid_posters