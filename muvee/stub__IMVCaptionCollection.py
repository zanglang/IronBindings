from xml.etree import ElementTree as etree
from . import stub_class, ProxyMixin

@stub_class
class IMVCaptionCollection(ProxyMixin):
	"""Pythonic wrapper for MVRuntimeLib.IMVCaptionCollection"""

	def __init__(self, proxyobj, *args, **kwargs):
		super(IMVCaptionCollection, self).__init__(proxyobj, *args, **kwargs)

	def __len__(self):
		return self.Size()

	def __getitem__(self, key):
		obj = object.__getattribute__(self, '_proxyobj')
		return obj[key]

	def __delitem__(self, key):
		return self.RemoveCaption(key)

	def __iter__(self):
		for i in xrange(len(self)):
			yield self.__getitem__(i)

	def __setitem__(self, *args, **kwargs):
		raise NotImplementedError

	def VerifyUserDscrp(self):
		oldcaptions = list(self)
		xml = self.ToXML()
		assert etree.fromstring(xml) is not None, \
			"ToXML returned invalid XML: " + str(xml)

		self.Clear()
		assert len(self) == 0

		self.FromXML(xml)
		assert len(self) == len(oldcaptions), \
			"Captions count mismatched"

		for older, newer in zip(oldcaptions, self):
			#assert older.Text == newer.Text, \
			#	"Caption text mismatched: %s != %s" % (older.Text, newer.Text)
			assert older.Start == newer.Start and older.Stop == newer.Stop, \
				"Caption highlight time mismatched"

			fmt1 = older.TextDisplayFormat
			fmt2 = newer.TextDisplayFormat
			assert fmt1.LogFontStr == fmt2.LogFontStr and \
				fmt1.Color == fmt2.Color and \
				fmt1.TextRectXCoord == fmt2.TextRectXCoord and \
				fmt1.TextRectYCoord == fmt2.TextRectYCoord and \
				fmt1.TextRectWidth == fmt2.TextRectWidth and \
				fmt1.TextRectHeight == fmt2.TextRectHeight and \
				fmt1.VertAlign == fmt2.VertAlign and \
				fmt1.HorAlign == fmt2.HorAlign, \
				"TextDisplayFormat mismatched"

		return True


if __name__ == "__main__":
	"""Basic tests"""

	from .mvrt import Core
	Core.Init(1)
	src = Core.CreateMVSource(1)
	caption = IMVCaptionCollection(src.Captions)

	assert len(caption) == 0
	caption.AddCaption("test 1")
	print "Caption 1 =", caption[0].Text
	caption.AddCaption("test 2")
	caption.AddCaption("test 3")
	assert len(caption) == 3
	print map(lambda c: c.Text, caption)
	assert etree.fromstring(caption.ToXML()) is not None
	print caption.ToXML()
	caption.RemoveCaption(0)
	assert len(caption) == 2
	caption.Clear()
	assert len(caption) == 0
	print caption.ToXML()
	print "Done."
