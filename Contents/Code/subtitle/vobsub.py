from default import Default
import re

class VobSub(Default):
	@classmethod
	def is_parser_for(cls, extension):
		# We only support idx (and maybe sub)
		return extension in ['idx', 'sub']

	def process(self):
		self.format = 'vobsub'
		
		# We don't directly process the sub file, only the idx. Therefore if we are passed on of these files, we simply
		# ignore it.
		if self.ext == 'sub':
			return {}

		# If we have an idx file, we need to confirm there is an identically names sub file before we can proceed.
		sub_filename = self.file + ".sub"
		if os.path.exists(sub_filename) == False:
			return {}

		if self.contents.count('VobSub index file') == 0:
			Log('The idx file does not appear to be a VobSub, skipping...')
			return {}

		tracks = {}
		language_index = 0
		for language in re.findall('\nid: ([A-Za-z]{2})', self.contents):
			if not tracks.has_key(language):
				tracks[language] = []
			Log('Found .idx subtitle file: ' + self.filename + ' language: ' + language + ' stream index: ' + str(language_index))
			tracks[language].append({ 'index': str(language_index) })
			language_index += 1
		return tracks
