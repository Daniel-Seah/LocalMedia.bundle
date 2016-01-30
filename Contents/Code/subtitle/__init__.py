import default
from default import Default
from txt import Txt
from vobsub import VobSub
from ssa import Ssa
from srt import Srt
from smi import Smi

parsers = [ Smi, Srt, Ssa, VobSub, Txt, Default ]

def parse(filename):
	(file, ext) = os.path.splitext(filename)
	ext = ext.lower()[1:]
	for cls in parsers:
		if cls.is_parser_for(ext):
			return cls(filename)
	return None

def register_exts(subtitle_exts):
	default.SUBTITLE_EXTS = subtitle_exts
