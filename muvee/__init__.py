#-------------------------
# this is a python module
#-------------------------

import logging, os, sys, types

if sys.platform == 'cli':
	import clr
	# check if the CLR already has references to MVRuntimeLib, e.g. inserted by TorsoSharp
	if not filter(lambda r: r.FullName.startswith('Interop.MVRuntimeLib'), clr.References):
		sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
		clr.AddReferenceToFile('Interop.MVRuntimeLib.dll')
		clr.AddReferenceToFile('IronBindings.dll')
else:
	raise "This Python module must be run by IronPython!"

__version__ = (1, 0)
logging.basicConfig(level=logging.DEBUG)

def get_type(obj):
	"""
	Gets the COM interface name of an object instance
	"""

	clr.AddReference('Microsoft.VisualBasic')
	from Microsoft.VisualBasic import Information
	return Information.TypeName(obj)


class ProxyMixin(object):
	"""
	Mixin for creating proxy classes. A ProxyMixin instance can be used to wrap
	native objects with a proxy, and delegates all method and property calls
	to the original proxied object.
	"""

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
		return get_type(self.get())

def stub_func(name):
	"""
	Function decorator to generate a wrapper for a given class, and adds all
	other methods using this decorator to it as class methods. If possible, opt
	to implement the stub functions as .NET extension methods instead.
	
	Example:
		@stub_func('IMVSource')
		def SampleFunction(self):
			return 'foo'
	
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

def stub_class(cls):
	"""
	Class decorator that registers the designated class in the `muvee` globals
	namespace. If a class already exists in that namespace it will be renamed
	and replaced. Use with ProxyMixin to generate wrapper classes that add stub
	methods or properties to classes.
	
	Example:
		@stub_class
		class IMVSource:
			def foo(self):
				return 'bar'
	"""

	globals()['_' + cls.__name__], globals()[cls.__name__] = globals()[cls.__name__], cls
	return cls

def gen_stub(cls):
	"""
	Dynamically creates a wrapper class for type-casting purposes. The wrapper
	is generated in source code form then compiled in the .NET runtime.
	The wrapper class should support all methods and properties of its origin
	class, and will simply delegates all such calls to the wrapped object.
	Once generated, the original class will be replaced in the global namespace
	by the wrapper class.

	Example:
		# type casting src2 from an IDualMVSource_Image instance to IMVSource
		src = gen_stub(IMVSource)(src2)
		assert isinstance(src, IMVSource) == True

	:param cls: Class to wrap with
	"""
	
	# check classname in case cls is already a wrapper
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


#========= Start =========

# load the COM interfaces
from MVRuntimeLib import *

# import IronBindings interface extensions
clr.ImportExtensions(Extensions)

# load IronBindings
import mvrt
sys.modules['muvee.mvrt'] = mvrt

# import stubs
from enums import *
import stub__IMVCaptionCollection
import stub__IMVStyleCollection
from stubs import *

# register for uncaught exceptions
def excepthook(etype, value, tb):
	# check if .NET exception
	if hasattr(value, 'clsException'):
		logging.exception(value.clsException.ToString())
	else:
		logging.fatal("Uncaught exception", exc_info=(etype, value, tb))
sys.excepthook = excepthook
