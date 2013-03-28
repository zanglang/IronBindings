#-------------------------
# this is a python module
#-------------------------

import clr, logging, os, sys, types

# check if the CLR already has references to MVRuntimeLib, e.g. inserted by TorsoSharp
if not filter(lambda r: r.FullName.startswith('Interop.MVRuntimeLib'), clr.References):
	sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
	clr.AddReferenceToFile('Interop.MVRuntimeLib.dll')
	clr.AddReferenceToFile('IronBindings.dll')

__version__ = (1, 0)
logging.basicConfig(level=logging.DEBUG)

######### Start #########

from MVRuntimeLib import *

# import IronBindings interface extensions
clr.ImportExtensions(Extensions)


class ProxyMixin(object):
	"""Mixin for generating proxy classes to MVRuntimeLib COM classes"""

	__slots__ = ['_proxyobj',]

	def __init__(self, proxyobj, *args, **kwargs):
		object.__setattr__(self, '_proxyobj', proxyobj)

	def __del__(self):
		# release com reference to proxied object
		from System.Runtime.InteropServices import Marshal
		obj = object.__getattribute__(self, '_proxyobj')
		Marshal.FinalReleaseComObject(obj)

	def __getattribute__(self, name):
		# check if call can be handled by proxy or proxied object
		try:
			return object.__getattribute__(self, name)
		except AttributeError:
			return getattr(self.get(), name)

	def get(self):
		# returns the original proxied object
		return object.__getattribute__(self, '_proxyobj')

	@property
	def TypeName(self):
		# Gets the type name of the proxied class
		clr.AddReference('Microsoft.VisualBasic')
		from Microsoft.VisualBasic import Information
		return Information.TypeName(self.get())


def stub(name):
	"""
	Function decorator to generate a wrapper for a given class, and adds all
	other methods using this decorator to it as class methods
	
	:param name: Class name to wrap with
	"""

	def _f(f):
		def wrapped(*args, **kwargs):
			return f(*args, **kwargs)

		# check if class wrapper had been generated
		cls = globals().get(name)
		if not cls or not hasattr(cls, '_proxyobj'):
			# generate class wrapper using ProxyMixin and rename existing class
			globals()['_' + name], cls = cls, type(name, (ProxyMixin,), { f.__name__: f })
			globals()[name] = cls
		else:
			# add method to existing wrapper
			setattr(cls, f.__name__, f)
		return wrapped
	return _f

def class_stub(cls):
	"""Class decorator that adds itself to the globals namespace in `muvee`"""

	globals()['_' + cls.__name__], globals()[cls.__name__] = globals()[cls.__name__], cls
	return cls

def enum(cls):
	"""
	Decorator that generates a dummy Python class with static members imported
	from MVRuntimeLib's enumerator flags. Example usage:
	
	@enum
	class SourceType:
		# imports all MV_SRC_TYPE_ENUM flags which names are prefixed with "SRC_TYPE_"
		_src = MV_SRC_TYPE_ENUM
		_prefix = 'SRC_TYPE_'
	"""

	for name in filter(lambda n: n.startswith(cls._prefix), dir(cls._src)):
		setattr(cls, name.replace(cls._prefix, ''), getattr(cls._src, name))
	return cls

def gen_stub(cls):
	"""Use Microsoft Roslyn to generate a wrapper class in .NET"""
	
	if type(cls) != types.TypeType and 'Wrapper' in str(cls):
		return cls

	print 'Generating stubs for', cls.__name__
	generator = StubGenerator(cls)
	module = generator.Compile()
	
	# compile successful, replace original class in global namespace
	t = module.Assembly.GetTypes()[0]
	globals()[t.Name] = t
	globals()['_' + cls.__name__], globals()[cls.__name__] = globals()[cls.__name__], t
	return t


### Miscellaneous enumerators ###

@enum
class SourceType:
	# imports all MV_SRC_TYPE_ENUM flags which names are prefixed with "SRC_TYPE_"
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

@enum
class ArType:
	_src = MV_AR_TYPE_ENUM
	_prefix = 'AR_TYPE'

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
	# check if .NET exception
	if hasattr(value, 'clsException'):
		logging.exception(value.clsException.ToString())
	else:
		logging.fatal("Uncaught exception", exc_info=(etype, value, tb))
sys.excepthook = excepthook
