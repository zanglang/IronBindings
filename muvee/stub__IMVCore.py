import os, sys

def _get_build(self):
	"""Retrieves the build number of the muvee runtime"""

	import os, plistlib
	assert isinstance(self, IMVCore)
	info_plist = os.path.join(
		os.path.dirname(os.path.dirname(self.ModuleLocation)),
		"Resources", "Info.plist")
	assert os.path.exists(info_plist), info_plist + " not found!"
	try:
		return int(plistlib.readPlist(info_plist)["CFBundleVersion"])
	except Exception, e:
		print e
		return 0

# only for mac
if sys.platform == "darwin":
	IMVCore.GetRuntimeSpecialBuild = _get_build
