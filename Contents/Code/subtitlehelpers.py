import config
import helpers
import subtitle

subtitle.register_exts(config.SUBTITLE_EXTS)

class SubtitleHelper(object):
	def __init__(self, filename):
		self.info = subtitle.parse(filename)

	def process_subtitles(self, part):
		Log('Subtitle info: file: ' + self.info.file + ', ext: ' + self.info.ext + ', basename: ' + self.info.basename + 
			', filename: ' + self.info.filename + ', forced: ' + self.info.forced + ', default: ' + self.info.default + 
			', file_lang: ' + str(self.info.filename_language) + ', format: ' + self.info.format + ', tracks: ' + 
			str(self.info.tracks))
		lang_sub_map = {}
		for language, infolist in self.info.tracks.iteritems():
			if not lang_sub_map.has_key(language):
				lang_sub_map[language] = []
			lang_sub_map[language].append(self.info.basename)
			for info in infolist:
				args = { 'format': self.info.format }
				args.update(info)
				part.subtitles[language][self.info.basename] = Proxy.LocalFile(self.info.filename, **args)
		return lang_sub_map

def SubtitleHelpers(filename):
	filename = helpers.unicodize(filename)
	subtitle = SubtitleHelper(filename)
	if subtitle.info != None:
		return SubtitleHelper(filename)
	else:
		return None
