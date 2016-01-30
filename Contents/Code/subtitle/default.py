import os
import re
import chardet
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

SUBTITLE_EXTS = []

def lazyprop(fn):
	attr_name = '_lazy_' + fn.__name__

	@property
	def lazyprop_(self):
		if not hasattr(self, attr_name):
			setattr(self, attr_name, fn(self))
		return getattr(self, attr_name)

	return lazyprop_
	
class Default(object):
	"""Extracts info about a subtitle file

	Default reads a subtitle file as text and returns information about it. Assumes there is exactly
	1 track for the current file. Language is guessed based on the contents of the file. 

	Attributes:
	Information about the subtitle file is available from this object as read-only attributes
	filename -- full fillename as passed into the ctor. Contains path, name and extension.
	Eg. E:/movies/big.buck.bunny.en.srt
	file -- path and name only with the extension and trailing dot removed. Tags (eg. forced and
	laguage code) are not removed. Eg. E:/movies/big.buck.bunny.en
	ext -- extension only. Eg. srt
	basename -- name and extension only. Eg. big.buck.bunny.en.srt
	format -- subtitle format. Defaults to the same value as extension
	forced -- '1' if forced flag is enabled, empty str otherwise. Field extracted from filename
	default -- '1' if default flag is enabled, empty str otherwise. Field extracted from filename
	filename_language -- subtitle language. Field extracted from filename. Set to Unknown if
	filename does not end with language code
	contents -- unicode string of the file contents
	dialogues -- (optional) unicode string of the subtitle dialogues. This attr is used by
	guess_language to figure out the subtitle language
	tracks -- a collection of subtitle track information. Track info is a dict which can be passed as 
	kwargs into the Plex subtitle proxy file. Track infos are grouped by language and the collated
	results are returned as a dict.
	eg. { 'en': [ { 'codec':'vobsub', 'index':'0' }, { ...track2 } ], 'ko': [ { ...track3 } ] }

	Methods:
	guess_language -- guesses the language based on the dialgues attribute. Good for formats which do
	not store language information.

	Interfaces:
	Default can be used as a base class to other parsers. The following methods can be overwritten
	when implementing a custom subtitle parser.
	is_parser_for -- (Class functions) returns true if this class can parse and extract info for the
	given extension
	process -- produce a collection of track info for the tracks attribute. Users can also modify
	attributes from here (eg. changing 'format' to a specific value). This function can access all
	attributes except tracks.
	read_dialogues -- produce a unicode string for the dialogues attribute. Text
	formatting and subtitle	timings should be stripped away. Each sentence is separated by a newline.
	If the subtitle format contains information about track language, this function can be omitted.
	"""

	@classmethod
	def is_parser_for(cls, extension):
		"""Returns true for subtitle extensions

		Arguments:
		cls -- the current class (Default)
		extension -- str of the subtitle extension. Leading dot has been removed.
		"""
		# Since Default is the catch all parser for subtitles, return true if it is any subtitle ext
		return extension in SUBTITLE_EXTS

	def process(self):
		"""Produce a collection of track info for the tracks attribute

		The default implementation assumes a single track for each subtitle file. It identifies the
		subtitle language based on filename. If the language code is not present, it is guessed from
		the dialogues.
		"""
		language = self.filename_language
		if language == Locale.Language.Unknown:
			language = self.guess_language()
			Log('Using language ' + str(language) + ' from lang detector')
		else:
			Log('Using language ' + str(language) + ' from filename')
		tracks = {}
		tracks[language] = [{ 'codec': self.format, 'default': self.default, 'forced': self.forced }]
		return tracks

	def read_dialogues(self):
		"""Returns only the dialogues from the text file

		Since we do not know what format this file is in, the default implementation returns all 
		contents as its dialogue.
		"""
		return self.contents
		
	def guess_language(self):
		language = Locale.Language.Unknown
		try:
			language = Locale.Language.Match(detect(self.dialogues))
		except LangDetectException as e:
			Log("Can't detect language of " + filename + ": " + str(e))
		return language

	def __init__(self, filename):
		self.filename = filename
		(file, ext) = os.path.splitext(self.filename)
		self.file = file
		self.ext = ext[1:]
		self.format = self.ext
		self.basename = os.path.basename(self.filename)
		forced = ''
		default = ''
		split_tag = file.rsplit('.', 1)
		if len(split_tag) > 1 and split_tag[1].lower() in ['forced', 'normal', 'default'] :
			file = split_tag[0]
			# don't do anything with 'normal', we don't need it
			if 'forced' == split_tag[1].lower():
				forced = '1'
			if 'default' == split_tag[1].lower():
				default = '1'
		self.forced = forced
		self.default = default

		# Attempt to extract the language from the filename (e.g. Avatar (2009).eng)
		language = ""
		language_match = re.match(".+\.([^\.]+)$", file)
		if language_match and len(language_match.groups()) == 1:
			language = language_match.groups()[0]
		self.filename_language = Locale.Language.Match(language)
		self.tracks = self.process()

	def read_text_file(self):
		raw = Core.storage.load(self.filename)
		info = chardet.detect(raw)
		return unicode(raw, info['encoding'])

	@lazyprop
	def contents(self):
		return self.read_text_file()

	@lazyprop
	def dialogues(self):
		return self.read_dialogues()
