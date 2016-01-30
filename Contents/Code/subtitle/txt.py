import re
from default import Default

class Txt(Default):
	@classmethod
	def is_parser_for(cls, extension):
		return extension == 'txt'

	def process(self):
		lines = [ line.strip() for line in self.contents.splitlines(True) ]
		format = self.format
		if re.match('^\{[0-9]+\}\{[0-9]*\}', lines[1]):
			format = 'microdvd'
		elif re.match('^[0-9]{1,2}:[0-9]{2}:[0-9]{2}[:=,]', lines[1]):
			format = 'txt'
		elif '[SUBTITLE]' in lines[1]:
			format = 'subviewer'
		else:
			Log("The subtitle file does not have a known format, skipping... : " + self.filename)
			return {}
		self.format = format
		return Default.process(self)
