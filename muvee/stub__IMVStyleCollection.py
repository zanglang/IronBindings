from . import stub_class, ProxyMixin

@stub_class
class IMVStyleCollection(ProxyMixin):
	"""Pythonic wrapper for MVRuntimeLib.IMVStyleCollection"""

	def __init__(self, *args, **kwargs):
		super(IMVStyleCollection, self).__init__(*args, **kwargs)

	def __len__(self):
		return self.Count

	def __getitem__(self, key):
		obj = object.__getattribute__(self, '_proxyobj')
		return obj[key]

	def __delitem__(self, key):
		raise NotImplementedError

	def __iter__(self):
		for i in xrange(len(self)):
			yield self.__getitem__(i)

	def __setitem__(self, *args, **kwargs):
		raise NotImplementedError


if __name__ == "__main__":
	"""Basic tests"""

	from .mvrt import Core
	Core.Init(1)
	styles = IMVStyleCollection(Core.Styles)
	assert len(styles) > 1

	for style in styles:
		assert style.InternalName.startswith('S00')

	styles.SetActiveMVStyle(styles[0].InternalName)
	assert styles.GetActiveMVStyle() == styles[0].InternalName
	print "Done."
