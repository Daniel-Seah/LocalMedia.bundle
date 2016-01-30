import re
from default import Default

class Smi(Default):
	@classmethod
	def is_parser_for(cls, extension):
		return extension in ['smi', 'sami']

	def process(self):
		self.format = 'smi'
		tracks = {}
		language = Locale.Language.Unknown
		langs = re.findall(r'\.\w+\s*\{.*lang\s*:\s*(\w+)', self.contents)
		if len(langs) > 0:
			language = Locale.Language.Match(langs[0])
		tracks[language] = [{ 'codec': self.format, 'default': self.default, 'forced': self.forced }]
		return tracks
