#-------------------------
# this is a python module
#-------------------------

import clr, logging, os, sys, types
if not filter(lambda r: r.FullName.startswith('Interop.MVRuntimeLib'), clr.References):
	sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
	clr.AddReferenceToFile('Interop.MVRuntimeLib.dll')
	clr.AddReferenceToFile('IronBindings.dll')

	__version__ = (1, 0)
logging.basicConfig(level=logging.DEBUG)

### Start ###

from MVRuntimeLib import *

# import IronBindings interface extensions
clr.ImportExtensions(Extensions)


class ProxyMixin(object):
	__slots__ = ['_proxyobj',]
	def __init__(self, proxyobj, *args, **kwargs):
		object.__setattr__(self, '_proxyobj', proxyobj)

	def __del__(self):
		from System.Runtime.InteropServices import Marshal
		obj = object.__getattribute__(self, '_proxyobj')
		Marshal.FinalReleaseComObject(obj)

	def __getattribute__(self, name):
		try:
			return object.__getattribute__(self, name)
		except AttributeError:
			return getattr(self.get(), name)

	def get(self):
		return object.__getattribute__(self, '_proxyobj')

	@property
	def TypeName(self):
		# general hackery
		clr.AddReference('Microsoft.VisualBasic')
		from Microsoft.VisualBasic import Information
		return Information.TypeName(self.get())


def stub(name):
	def _f(f):
		def wrapped(*args, **kwargs):
			return f(*args, **kwargs)

		cls = globals().get(name)
		if not cls or not hasattr(cls, '_proxyobj'):
			globals()['_' + name], cls = cls, type(name, (ProxyMixin,), { f.__name__: f })
			globals()[name] = cls
		else:
			setattr(cls, f.__name__, f)
		return wrapped
	return _f

def class_stub(cls):
	"""Class decorator that adds itself to the globals namespace in muvee"""

	globals()['_' + cls.__name__], globals()[cls.__name__] = globals()[cls.__name__], cls
	return cls

def enum(cls):
	for name in filter(lambda n: n.startswith(cls._prefix), dir(cls._src)):
		setattr(cls, name.replace(cls._prefix, ''), getattr(cls._src, name))
	return cls

def gen_stub(cls):
	if type(cls) != types.TypeType and 'Wrapper' in str(cls):
		return cls

	print 'Generating stubs for', cls.__name__
	generator = StubGenerator(cls)
	module = generator.Compile()
	t = module.Assembly.GetTypes()[0]
	globals()[t.Name] = t
	globals()['_' + cls.__name__], globals()[cls.__name__] = globals()[cls.__name__], t
	return t


### Miscellaneous enumerators ###

@enum
class SourceType:
	_src = MV_SRC_TYPE_ENUM
	_prefix = 'SRC_TYPE_'

@enum
class InitFlags:
	_src = MV_INIT_ENUM
	_prefix = 'INIT_'

@enum
class LoadFlags:
	_src = MV_LOAD_FLAGS
	_prefix = 'LOAD_'

@enum
class MakeFlags:
	_src = MV_MAKE_ENUM
	_prefix = 'MAKE_'

@enum
class TimelineType:
	_src = MV_TL_TYPE_ENUM
	_prefix = 'TL_TYPE_'

import sys
import mvrt
sys.modules['muvee.mvrt'] = mvrt

# import stubs
import stub__IMVSource
import stub__IMVCaptionCollection
import stub__IMVStyleCollection
from stubs import *

# uncaught exceptions
def excepthook(etype, value, tb):
	if hasattr(value, 'clsException'):
		logging.exception(value.clsException.ToString())
	else:
		logging.fatal("Uncaught exception", exc_info=(etype, value, tb))
sys.excepthook = excepthook
