import sys

class ClrForm(object):
	def __init__(self, width=320, height=240, setup=None, teardown=None):
		"""
		Creates a .NET Windows Form instance.
		
		:param width: Width of the window
		:param height: Height of the window
		:param setup: Function callback to call when the form has been created
		:param tearmdown: Function delegate to assign to the Form's Closing event
		"""

		from System.Windows.Forms import Application, Form
		self.form = Form(Text="muFAT Test", Width=width, Height=height, TopMost=True)
		self.hwnd = self.form.Handle
		if setup is not None:
			setup.__call__()
		if teardown is not None:
			self.form.Closing += teardown
		else:
			self.form.Closing += self.__exit__

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
		self.form.ShowDialog()

	def close(self):
		self.form.Close()


#=== specify different Window implementations depending on platform

if sys.platform == "cli": # .NET
	import clr
	clr.AddReference('System.Windows.Forms')
	Window = ClrForm
elif sys.platform == "darwin": # MacOS
	from cocoa import CocoaWindow
	Window = CocoaWindow
else:
	raise Exception("Only 'clr' and 'darwin' is supported for now.")
