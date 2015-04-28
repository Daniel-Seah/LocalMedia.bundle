#local media assets agent
import os, string, hashlib, base64, re, plistlib, unicodedata
import config
import helpers
import localmedia
import audiohelpers
import videohelpers

from mutagen import File
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.flac import Picture
from mutagen.oggvorbis import OggVorbis

PERSONAL_MEDIA_IDENTIFIER = "com.plexapp.agents.none"

#####################################################################################################################

@expose
def ReadTags(f):
  try:
    return dict(File(f, easy=True))
  except Exception, e:
    Log('Error reading tags from file: %s' % f)
    return {}

#####################################################################################################################

class localMediaMovie(Agent.Movies):
  name = 'Local Media Assets (Movies)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  persist_stored_files = False
  contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.none']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))
    
  def update(self, metadata, media, lang):
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title

    part = media.items[0].parts[0]
    path = os.path.dirname(part.file)
    
    # Look for local media.
    try: localmedia.findAssets(metadata, [path], 'movie', media.items[0].parts)
    except Exception, e: 
      Log('Error finding media for movie %s: %s' % (media.title, str(e)))

    # Look for subtitles
    for item in media.items:
      for part in item.parts:
        localmedia.findSubtitles(part)

    # If there is an appropriate VideoHelper, use it.
    video_helper = videohelpers.VideoHelpers(part.file)
    if video_helper:
      video_helper.process_metadata(metadata)

#####################################################################################################################

def FindUniqueSubdirs(dirs):
  final_dirs = {}
  for dir in dirs:
    final_dirs[dir] = True
    try: 
      parent = os.path.split(dir)[0]
      final_dirs[parent] = True
      try: final_dirs[os.path.split(parent)[0]] = True
      except: pass
    except: pass
    
  if final_dirs.has_key(''):
    del final_dirs['']
  return final_dirs

class localMediaTV(Agent.TV_Shows):
  name = 'Local Media Assets (TV)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  persist_stored_files = False
  contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))

  def update(self, metadata, media, lang):
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title

    # Look for media, collect directories.
    dirs = {}
    for s in media.seasons:
      Log('Creating season %s', s)
      metadata.seasons[s].index = int(s)
      for e in media.seasons[s].episodes:
        
        # Make sure metadata exists, and find sidecar media.
        episodeMetadata = metadata.seasons[s].episodes[e]
        episodeMedia = media.seasons[s].episodes[e].items[0]
        dir = os.path.dirname(episodeMedia.parts[0].file)
        dirs[dir] = True
        
        try: localmedia.findAssets(episodeMetadata, [dir], 'episode', episodeMedia.parts)
        except Exception, e: 
          Log('Error finding media for episode: %s' % str(e))
        
    # Figure out the directories we should be looking in.
    try: dirs = FindUniqueSubdirs(dirs)
    except: dirs = []
    
    # Look for show images.
    Log("Looking for show media for %s.", metadata.title)
    try: localmedia.findAssets(metadata, dirs, 'show')
    except: Log("Error finding show media.")
    
    # Look for season images.
    for s in metadata.seasons:
      Log('Looking for season media for %s season %s.', metadata.title, s)
      try: localmedia.findAssets(metadata.seasons[s], dirs, 'season')
      except: Log("Error finding season media for season %s" % s)
        
    # Look for subtitles for each episode.
    for s in media.seasons:
      # If we've got a date based season, ignore it for now, otherwise it'll collide with S/E folders/XML and PMS
      # prefers date-based (why?)
      if int(s) < 1900 or metadata.guid.startswith(PERSONAL_MEDIA_IDENTIFIER):
        for e in media.seasons[s].episodes:
          for i in media.seasons[s].episodes[e].items:

            # Look for subtitles.
            for part in i.parts:
              localmedia.findSubtitles(part)

              # If there is an appropriate VideoHelper, use it.
              video_helper = videohelpers.VideoHelpers(part.file)
              if video_helper:
                video_helper.process_metadata(metadata, episode = metadata.seasons[s].episodes[e])
      else:
        # Whack it in case we wrote it.
        #del metadata.seasons[s]
        pass

#####################################################################################################################

class localMediaArtistCommon(object):
  name = 'Local Media Assets (Artists)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  persist_stored_files = False

  def update(self, metadata, media, lang):
    
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title
   
    if shouldFindExtras():
      extra_type_map = getExtraTypeMap()

      artist_file_dirs = []
      artist_extras = {}

      # First look for track extras.
      for album in media.children:
        for track in album.children:
          part = helpers.unicodize(track.items[0].parts[0].file)
          findTrackExtra(part, extra_type_map, artist_extras)
          artist_file_dirs.append(os.path.dirname(part))

      # Now go through this artist's directories looking for additional extras.
      for artist_file_dir in set(artist_file_dirs):
        findArtistExtras(helpers.unicodize(artist_file_dir), extra_type_map, artist_extras)

      for extra in sorted(artist_extras.values(), key = lambda v: (getExtraSortOrder()[type(v)], v.title)):
        metadata.extras.add(extra)


class localMediaArtistLegacy(localMediaArtistCommon, Agent.Artist):
  contributes_to = ['com.plexapp.agents.discogs', 'com.plexapp.agents.lastfm', 'com.plexapp.agents.plexmusic', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', name=media.artist, score = 100))


class localMediaArtistModern(localMediaArtistCommon, Agent.Artist):
  version = 2
  contributes_to = ['com.plexapp.agents.plexmusic']

  def search(self, results, tree, hints, lang='en', manual=False):
    results.add(SearchResult(id='null', type='artist', parentName=hints.artist, score=100))

  def update(self, metadata, media, lang='en', child_guid=None):
    super(localMediaArtistModern, self).update(metadata, media, lang)


class localMediaAlbum(Agent.Album):
  name = 'Local Media Assets (Albums)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  persist_stored_files = False
  contributes_to = ['com.plexapp.agents.discogs', 'com.plexapp.agents.lastfm', 'com.plexapp.agents.plexmusic', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))

  def update(self, metadata, media, lang):

    find_extras = shouldFindExtras()
    extra_type_map = getExtraTypeMap() if find_extras else None
    updateAlbum(metadata, media, lang, find_extras, artist_extras=[], extra_type_map=extra_type_map)


def updateAlbum(metadata, media, lang, find_extras=False, artist_extras={}, extra_type_map=None):
      
  # Set title if needed.
  if media and metadata.title is None: metadata.title = media.title

  valid_posters = []
  path = None
  for track in media.tracks:
    for item in media.tracks[track].items:
      for part in item.parts:
        filename = helpers.unicodize(part.file)
        path = os.path.dirname(filename)
        (file_root, fext) = os.path.splitext(filename)

        path_files = {}
        for p in os.listdir(path):
          path_files[p.lower()] = p

        # Look for posters
        poster_files = config.POSTER_FILES + [ os.path.basename(file_root), helpers.splitPath(path)[-1] ]
        for ext in config.ART_EXTS:
          for name in poster_files:
            file = (name + '.' + ext).lower()
            if file in path_files.keys():
              data = Core.storage.load(os.path.join(path, path_files[file]))
              poster_name = hashlib.md5(data).hexdigest()
              valid_posters.append(poster_name)

              if poster_name not in metadata.posters:
                metadata.posters[poster_name] = Proxy.Media(data)
                Log('Local asset image added: ' + file + ', for file: ' + filename)
              else:
                Log('Skipping local poster since its already added')

        # If there is an appropriate AudioHelper, use it.
        audio_helper = audiohelpers.AudioHelpers(part.file)
        if audio_helper != None:
          try: 
            valid_posters = valid_posters + audio_helper.process_metadata(metadata)
          except: pass

        # Look for a video extra for this track.
        if find_extras:
          track_video = findTrackExtra(helpers.unicodize(part.file), extra_type_map)
          if track_video is not None:
            track_key = media.tracks[track].guid or track
            metadata.tracks[track_key].extras.add(track_video)

      
def findTrackExtra(file_path, extra_type_map, artist_extras={}):

  # Look for music videos for this track of the format: "track file name - pretty name (optional) - type (optional).ext"
  file_name = os.path.basename(file_path)
  file_root, file_ext = os.path.splitext(file_name)
  track_videos = []
  for video in [f for f in os.listdir(os.path.dirname(file_path)) 
                if os.path.splitext(f)[1][1:].lower() in config.VIDEO_EXTS 
                and helpers.unicodize(f).lower().startswith(file_root.lower())]:

    video_file, ext = os.path.splitext(video)
    name_components = video_file.split('-')
    extra_type = MusicVideoObject
    if len(name_components) > 1:
      type_component = re.sub(r'[ ._]+', '', name_components[-1].lower())
      if type_component in extra_type_map:
        extra_type = extra_type_map[type_component]
        name_components.pop(-1)

    # Use the video file name for the title unless we have a prettier one.
    pretty_title = '-'.join(name_components).strip()
    if len(pretty_title) - len(file_root) > 0:
      pretty_title = pretty_title.replace(file_root, '')
      pretty_title = re.sub(r'^[- ]+', '', pretty_title)

    track_video = extra_type(title=pretty_title, file=os.path.join(os.path.dirname(file_path), video))
    artist_extras[video] = track_video

    if extra_type in [MusicVideoObject, LyricMusicVideoObject]:
      Log('Found video %s for track: %s from file: %s' % (pretty_title, file_name, os.path.join(os.path.dirname(file_path), video)))
      track_videos.append(track_video)
    else:
      Log('Skipping track video %s (only regular music videos allowed on tracks)' % video)

    if len(track_videos) > 0:
      track_videos = sorted(track_videos, key = lambda v: (getExtraSortOrder()[type(v)], v.title))
      return track_videos[0]

  return None


def findArtistExtras(path, extra_type_map, artist_extras):

  # Look for other videos in this directory.
  for video in [f for f in os.listdir(path) 
                if os.path.splitext(f)[1][1:].lower() in config.VIDEO_EXTS
                and f not in artist_extras]:

    video_file, ext = os.path.splitext(video)
    name_components = video_file.split('-')

    if len(name_components) > 1 and name_components[-1].lower().strip() in extra_type_map:
      extra_type = extra_type_map[name_components.pop(-1).lower().strip()]
    else:
      extra_type = MusicVideoObject

    Log('Found artist video: %s' % video)
    if video not in artist_extras:
      artist_extras[video] = extra_type(title='-'.join(name_components), file=os.path.join(path,video))


def shouldFindExtras():
  # Determine whether we should look for video extras.
    try: 
      v = LiveMusicVideoObject()
      if Util.VersionAtLeast(Platform.ServerVersion, 0,9,9,13):
        find_extras = True
      else:
        find_extras = False
        Log('Not adding extras: Server v0.9.11.13+ required')  # TODO: Update with real min version.
    except NameError, e:
      Log('Not adding extras: Framework v2.5.2+ required')  # TODO: Update with real min version.
      find_extras = False
    return find_extras


def getExtraTypeMap():
  return {'video' : MusicVideoObject,
          'live' : LiveMusicVideoObject,
          'lyrics' : LyricMusicVideoObject,
          'behindthescenes' : BehindTheScenesObject,
          'interview' : InterviewObject }

def getExtraSortOrder():
  return {MusicVideoObject : 0, LyricMusicVideoObject : 1, LiveMusicVideoObject : 2, BehindTheScenesObject : 3, InterviewObject : 4}