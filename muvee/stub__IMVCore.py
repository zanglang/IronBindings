def _get_build(self):
	"""Retrieves the build number of the muvee runtime"""

	import os, plistlib
	from .mvrt import Core

	plist = os.path.join(os.path.dirname(os.path.dirname(Core.ModuleLocation)),
			"Resources", "Info.plist")
	assert os.path.exists(plist), plist + " not found!"
	try:
		return int(plistlib.readPlist(plist)["CFBundleVersion"])
	except Exception, e:
		print e
		return 0

# only for mac
import sys
if sys.platform == "darwin":
	from .mvrt import Core
	from types import MethodType
	Core.GetRuntimeSpecialBuild = MethodType(_get_build, Core)
