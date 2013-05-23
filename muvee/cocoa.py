import objc, time
from AppKit import *
from PyObjCTools import AppHelper, Debugging


class Delegate(NSObject):
	def applicationDidFinishLaunching_(self, notification):
		print time.ctime(), "Cocoa: Application launched."

	def windowWillClose_(self, notification):
		if NSApp() is not None:
			print time.ctime(), "Cocoa: Window closing."
			NSApp().terminate_(self)


class CocoaWindow(object):
	def __init__(self, width=320, height=240, setup=None, teardown=None):
		pool = NSAutoreleasePool.alloc().init()
		self.delegate = Delegate.alloc().init()
		self.app = NSApplication.sharedApplication()
		self.app.setDelegate_(self.delegate)

		window = NSWindow.alloc()
		window.initWithContentRect_styleMask_backing_defer_(((0, 0), (width, height)), 31, 2, 0)
		window.setDelegate_(self.delegate)
		window.setTitle_('muFAT Test')
		window.setLevel_(3)
		window.display()
		self.window = window

		if setup is not None:
			AppHelper.callLater(1, setup, self)
		del pool

	def __enter__(self):
		"""
		Override this function to specify what happens when the form is initialized
		"""
		return self

	def __exit__(self, type, value, traceback):
		"""
		Override this function to specify what happens when the form is closed
		or closing.
		"""
		pass

	def show(self):
		pool = NSAutoreleasePool.alloc().init()
		Debugging.installVerboseExceptionHandler()
		AppHelper.installMachInterrupt()
		self.window.orderFrontRegardless()

		print time.ctime(), "Cocoa: Starting event loop..."
		try:
			NSApp().run()
		except KeyboardInterrupt:
			print time.ctime(), "Interrupted."
		finally:
			print time.ctime(), "Cocoa: Event loop ended."
		del pool

	def close(self):
		pool = NSAutoreleasePool.alloc().init()
		self.window.orderOut_(None)

		# quit app mainloop and hide window
		if NSApp().isRunning() == objc.YES:
			print time.ctime(), "Cocoa: Pausing app..."
			NSApp().stop_(None)

		# needs a pseudo-event before it'll be correctly stopped
		e = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(\
			NSApplicationDefined, NSMakePoint(0, 0), 0, 0.0, 0, None, 0, 0, 0)
		NSApp().postEvent_atStart_(e, True)
		Debugging.removeExceptionHandler()
		del pool

	@property
	def hwnd(self):
		return self.window.windowRef()
