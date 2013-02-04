import time
from . import stub

@stub('IMVSource')
def AddCaption(self, text):
	from . import GetLastErrorDescription, IMVCaptionCollection
	captions = IMVCaptionCollection(self.Captions)
	assert captions.AddCaption(text) is not None, \
		'AddCaption failed: ' + GetLastErrorDescription()
	assert len(captions) == 1
	assert captions.VerifyUserDscrp(), \
		'VerifyUserDscrp failed: ' + GetLastErrorDescription()

@stub('IMVSource')
def AnalyseTillDone(self, resolution=500, timeout=200):
	from . import GetLastErrorDescription
	prog = -1
	count = timeout
	sleep = resolution/1000.0

	assert self.StartAnalysisProc(""), \
		("StartAnalysisProc failed: ", GetLastErrorDescription())
	try:
		while prog < 1:
			prog = self.GetAnalysisProgress()
			print "Progress:", prog

			count -= 1
			assert count >= 0, "Timed out after %d repetitions." % timeout
			time.sleep(sleep)
	except:
		self.StopAnalysisProc()
		raise
	return True

@stub('IMVSource')
def __del__(self):
	obj = object.__getattribute__(self, '_proxyobj')
	Marshal.FinalReleaseComObject(obj)
