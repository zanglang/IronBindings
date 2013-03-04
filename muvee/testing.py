import os, re, shutil, sys, unittest
from datetime import datetime
from functools import wraps
from inspect import getmodule
from pkgutil import iter_modules
from tempfile import mkstemp
from types import FunctionType


class MufatLogger(object):
	"""
	File-like object class that writes all text input to the muveedebug log folder.
	If c:\muveedebug\Log.txt exists, will also intercept all writes to standard
	output as well.
	"""

	def __init__(self):
		# check if logfiles exist
		exists = lambda a, b: os.path.isfile(a) and a or b
		self.file = reduce(exists, [r'c:\muveedebug\Log.txt', 'c:\muveedebug\LoggingError.txt'])
		if not os.path.exists(os.path.dirname(self.file)):
			os.makedirs(os.path.dirname(self.file))
		self.stdout = sys.stdout
		if os.path.isfile(self.file):
			sys.stdout = self

	def __del__(self):
		# revert standard out back to normal
		sys.stdout = self.stdout

	def write(self, *args):
		# append to logfile and print to stdout
		try:
			with open(self.file, 'a') as f:
				f.write(*args)
		except:
			self.stdout.write("MufatLogger: Skipped write.")
		self.stdout.write(*args)

	def writeln(self, *args):
		self.write(*args)
		self.write('\n')

	# do nothing
	def _noop(self):
		pass
	close = flush = _noop


def testcase(f):
	"""Marks a function as a testcase so it can be discovered by unittest"""
	@wraps(f)
	def _wrap(*args, **kwargs):
		return f(*args, **kwargs)
	setattr(_wrap, "is_a_testcase", True)
	return _wrap


def make_tests(module):
	"""Helper function to generate a list of `unittest.FunctionTestCase` from a module"""
	from . import Init, Release
	for func in module.__dict__.itervalues():
		if type(func) == FunctionType and getattr(func, "is_a_testcase", False):
			yield unittest.FunctionTestCase(func, setUp=Init, tearDown=Release)


def make_discoverable(name, file):
	"""
	Generates a `load_tests` function that assists `unittest`'s discovery
	feature to generate a list of test cases, customized for the test package.
	
	A standard way to use this function is to place this snippet inside a
	test suite package's __init__.py:
	
	  load_tests = make_discoverable(__name__, __file__)
	
	:param name: The package's name
	:param file: The package's path
	:returns: A customized function that should be assigned to `load_tests`
	"""

	def load_tests(loader, standard_tests, pattern):
		suite = unittest.TestSuite()
		for _, modname, ispkg in iter_modules([ os.path.dirname(os.path.realpath(file)), ], name + "."):
			module = __import__(modname, fromlist="dummy")
			for test in make_tests(module):
				suite.addTest(test)
		return suite
	return load_tests


class MufatTestResult(unittest.TextTestResult):
	"""
	Custom `unittest.TextTestResults` subclass that records the start and end
	time of a muFAT run, collection of passed tests
	"""

	def __init__(self, *args, **kwargs):
		super(MufatTestResult, self).__init__(*args, **kwargs)
		self.passed = []
		# logfile for storing run output text
		self.logfile_fd, self.logfile = mkstemp()

	def addSuccess(self, test):
		self.passed.append(test)
		super(MufatTestResult, self).addSuccess(test)

	def startTest(self, test):
		# record start timestamp
		setattr(test, "startTime", datetime.now())
		super(MufatTestResult, self).startTest(test)

	def stopTest(self, test):
		# record time taken for this run
		setattr(test, "stopTime", datetime.now())
		setattr(test, "timeTaken", (test.stopTime - test.startTime).total_seconds()*1000)
		super(MufatTestResult, self).stopTest(test)


class MufatTestRunner(unittest.TextTestRunner):
	"""
	Custom `unittest.TextTestRunner` that generate a `unittest.TestSuite`
	"""

	def __init__(self, *args, **kwargs):
		# immediately stop upon failure, extra verbose logging
		super(MufatTestRunner, self).__init__(*args, failfast=True, verbosity=2,
			resultclass=MufatTestResult, **kwargs)

	def run(self, suite=None, runname="Mufat"):
		startTime = datetime.now()
		if not suite:
			suite = unittest.TestSuite()
			module = __import__(runname, fromlist="dummy")
			for test in make_tests(module):
				suite.addTest(test)

		if not "Init" in (t.id() for t in suite._tests[:1]):
			from . import Init
			suite._tests.insert(0, unittest.FunctionTestCase(Init))
		if not "Release" in (t.id() for t in suite._tests[-1:]):
			from . import Release
			suite._tests.append(unittest.FunctionTestCase(Release))

		# execute tests
		self.stream.writeln("**** Starting: %s ****" % runname)
		result = super(MufatTestRunner, self).run(suite)
		passed = map(lambda t: t.id(), result.passed)
		result.skipped = list(set(suite._tests).difference(result.passed))

		# generate summary log file
		with open(result.logfile, "w+") as f:
			print >> f, "time:", startTime.strftime("%m-%d-%Y, %H:%M:%S")
			print >> f, "passes:", len(result.passed)
			print >> f, "failures:", len(result.failures) + len(result.errors)
			print >> f, "untested:", len(result.skipped), "\n"

			# log stubs that were not run/failed
			for test in suite:
				print >> f, test.id()
				print >> f, getmodule(test._testFunc).__file__
				print >> f, (test.id() in passed) and "1" or "0"
				print >> f, getattr(test, "timeTaken", 0), "\n"

		os.close(result.logfile_fd)
		return result


def detect_media(*media):
	LOCAL = os.path.expanduser(r"C:\mufat_repo")
	REMOTE = r"T:\\testsets\\muFAT_SDKRuntime"
	local_re = re.compile(re.escape(LOCAL), re.IGNORECASE)
	remote_re = re.compile(re.escape(REMOTE), re.IGNORECASE)
	media = filter(lambda s: isinstance(s, basestring), media)
	for dest in media:
		if not local_re.findall(dest) and not remote_re.findall(dest):
			continue
		src = local_re.sub(REMOTE, dest)
		if not os.path.exists(dest) or os.stat(src).st_size != os.stat(dest).st_size:
			if not os.path.exists(os.path.dirname(dest)):
				os.makedirs(os.path.dirname(dest))
			print "Copying %s -> %s" % (src, dest)
			shutil.copy(src, dest)


def generate_wrapper(func, testsuite):
	"""
	Wraps a function call with `unittest.FunctionTestCase` and adds it to a
	`unittest.TestSuite`.
	"""

	@wraps(func)
	def wrapper(*args, **kwargs):
		@wraps(func)
		def _wrap():
			# print ">>>>> Delegating function call to", func.__name__
			func(*args, **kwargs)
		case = unittest.FunctionTestCase(_wrap)
		# detect missing media or binfiles that needs copying
		if args:
			detect_media(*args)
		if kwargs:
			detect_media(kwargs.values())
		testsuite.addTest(case)
	return wrapper


def run(func, localdict):
	"""
	Generates a `unittest.TestSuite` out of a given function `func` by creating
	`unittest.FunctionTestCase` tests out of all imported test stubs and passing
	them to a test runner.

	Using meta-programming, this function irreversibly replaces any test stub
	functions with dummy wrappers that generate `unittest.FunctionTestCase`
	cases to the actual stubs. Hence, it should only be used in __main__.

	:param func: The test function to be called
	:param localdict: `locals()`
	"""

	suite = unittest.TestSuite()
	for k, f in localdict.items():
		# stubs are identified by having applied @stubs.is_a_stub decorators
		if type(f) != FunctionType or not getattr(f, "is_a_stub", False):
			continue
		wrapped = generate_wrapper(f, suite)
		print ">>>>> Generated wrapper for", f.__module__ + "." + k, "..."
		# replace locals with the wrapped version
		localdict[k] = wrapped

	# this function now only generates test cases
	func.__call__()

	# test cases collected, clear to run!
	return MufatTestRunner(stream=MufatLogger()).run(suite, func.__name__)
