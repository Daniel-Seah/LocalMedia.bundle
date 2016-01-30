import pysrt
from default import Default

class Srt(Default):
	@classmethod
	def is_parser_for(cls, extension):
		return extension == 'srt'

	def read_dialogues(self):
		subs = pysrt.from_string(self.contents)
		buffer = ''
		for quote in subs:
			buffer += quote.text + '\n'
		return unicode(buffer)
