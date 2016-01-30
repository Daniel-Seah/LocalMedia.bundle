from default import Default
import ass

class Ssa(Default):
	@classmethod
	def is_parser_for(cls, extension):
		return extension in ['ssa', 'ass']

	def process(self):
		self.format = 'ssa'
		return Default.process(self)

	def read_dialogues(self):
		subs = ass.parse(self.contents.splitlines())
		buffer = ''
		for quote in subs.events:
			if isinstance(quote, ass.document.Dialogue):
				buffer += quote.text + '\n'
		return unicode(buffer)
