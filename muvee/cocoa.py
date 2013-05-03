import objc, time
from AppKit import *
from PyObjCTools import AppHelper, Debugging

class CocoaWindow(object):
	instance = None

	def __init__(self, width=320, height=240, setup=None, teardown=None):
		class Delegate(NSObject):
			def applicationDidFinishLaunching_(self, notification):
				print time.ctime(), "Cocoa: Application launched."

			def windowWillClose_(self, notification):
				if NSApp() is not None:
					print time.ctime(), "Cocoa: Window closing."
					if teardown is not None:
						teardown()
					NSApp().terminate_(self)

		pool = NSAutoreleasePool.alloc().init()
		app = NSApplication.sharedApplication()
		delegate = Delegate.alloc().init()
		app.setDelegate_(delegate)

		window = NSWindow.alloc()
		window.initWithContentRect_styleMask_backing_defer_(((0, 0), (width, height)), 31, 2, 0)
		window.setDelegate_(delegate)
		window.setTitle_(kwargs.get('title', 'muFAT Test'))
		window.setLevel_(3)
		window.display()
		window.orderFrontRegardless()
		CocoaWindow.instance = window

		print time.ctime(), "Cocoa: Starting event loop..."
		Debugging.installVerboseExceptionHandler()
		AppHelper.installMachInterrupt()
		if setup is not None:
			AppHelper.callLater(1, setup)
		try:
			NSApp().run()
		except KeyboardInterrupt:
			print time.ctime(), "Interrupted."
		finally:
			print time.ctime(), "Cocoa: Event loop ended."
			del pool

def pause():
	pool = NSAutoreleasePool.alloc().init()

	if CocoaWindow.instance is not None:
		CocoaWindow.instance.orderOut_(None)
		CocoaWindow.instance = None

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
