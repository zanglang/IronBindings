import os, threading, time
from functools import wraps
from . import gen_stub, InitFlags, LoadFlags, MakeFlags, SourceType, TimelineType, \
	IMVCaptionHighlight, IMVExclude, IMVHighlight, IMVSource, \
	IMVStyleCollection, IMVTargetRect


def is_a_stub(f):
	"""Wraps a function as a `unittest.FunctionTestCase`"""
	@wraps(f)
	def _wrap(*args, **kwargs):
		return f(*args, **kwargs)
	setattr(_wrap, "is_a_stub", True)
	return _wrap


@is_a_stub
def Init(flags=InitFlags.DEFAULT):
	from .mvrt import Core
	Core.Init(flags)

@is_a_stub
def Release():
	from . import mvrt
	mvrt.Release()

@is_a_stub
def AddSource(src, srctype=SourceType.UNKNOWN, loadtype=LoadFlags.VERIFYSUPPORT):
	from .mvrt import Core
	if srctype == SourceType.UNKNOWN:
		typename = IMVSource(src).TypeName
		if 'MVSource_Image' in typename:
			srctype = SourceType.IMAGE
		elif 'MVSource_Music' in typename:
			srctype = SourceType.MUSIC
		elif 'MVSource_Video' in typename:
			srctype = SourceType.VIDEO
	assert Core.AddSource(srctype, src, loadtype), \
			'AddSource failed: ' + GetLastErrorDescription()

@is_a_stub
def CreateSource(path, srctype):
	from .mvrt import Core
	src = IMVSource(Core.CreateMVSource(srctype))
	if srctype in [ SourceType.IMAGE, SourceType.MUSIC, SourceType.VIDEO ]:
		assert os.path.exists(path), "File %s does not exist" % path
		assert src.LoadFile(path, LoadFlags.VERIFYSUPPORT), \
			'LoadFile failed: ' + GetLastErrorDescription()
		assert src.AnalyseTillDone(), \
			'AnalyseTillDone failed: ' + GetLastErrorDescription()
	else:
		src.Load(path, LoadFlags.CONTEXT)
	return src.get()

@is_a_stub
def AddSourceImage(path):
	src = CreateSource(path, SourceType.IMAGE)
	AddSource(src, SourceType.IMAGE, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceImageWithCaption(path, caption):
	src = IMVSource(CreateSource(path, SourceType.IMAGE))
	src.AddCaption(caption)
	AddSource(src.get(), SourceType.IMAGE, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceImageWithMagicSpot(path, *args):
	src = CreateSource(path, SourceType.IMAGE)
	rect = gen_stub(IMVTargetRect)(src)
	for i in xrange(0, len(args), 4):
		coords = args[i:i+4]
		assert len(coords) == 4
		rect.AddTargetRect(*coords)
	AddSource(src, SourceType.IMAGE, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceMusic(path):
	src = CreateSource(path, SourceType.MUSIC)
	AddSource(src, SourceType.MUSIC, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceTextWithMinDuration(text, duration):
	src = CreateSource(text, SourceType.TEXT)
	src.MinImgSegDuration = duration
	AddSource(src, SourceType.TEXT, LoadFlags.CONTEXT)

@is_a_stub
def AddSourceVideo(path):
	src = CreateSource(path, SourceType.VIDEO)
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceVideoWithCapHL(path, caption, start, end):
	src = CreateSource(path, SourceType.VIDEO)
	hilite = gen_stub(IMVCaptionHighlight)(src)
	hilite.SetCaptionHighlight(caption, start, end, None)
	hilite.VerifyUserDescriptors()
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceVideoWithMagicMoments(path, *args):
	src = CreateSource(path, SourceType.VIDEO)
	hilite = gen_stub(IMVHighlight)(src)
	for i in xrange(0, len(args), 2):
		pair = args[i:i+2]
		assert len(pair) == 2
		hilite.SetHighlight(*pair)
	hilite.VerifyUserDescriptors()
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceVideoWithExclusion(path, *args):
	src = CreateSource(path, SourceType.VIDEO)
	exclude = gen_stub(IMVExclude)(src)
	for i in xrange(0, len(args), 2):
		pair = args[i:i+2]
		assert len(pair) == 2
		exclude.SetExclusion(*pair)
	exclude.VerifyUserDescriptors()
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def GetLastErrorDescription():
	from .mvrt import Core
	return Core.GetLastErrorDescription()

@is_a_stub
def SelectStandardStyle():
	SetActiveMVStyle('S00516_Plain')

@is_a_stub
def SetActiveMVStyle(style):
	from .mvrt import Core
	assert style in map(lambda s: s.InternalName, IMVStyleCollection(Core.Styles))
	Core.SetActiveMVStyle(style)

@is_a_stub
def PutCreditsString(string):
	from .mvrt import Core
	col = Core.GetStyleCollection()
	col.CreditsString = string

@is_a_stub
def PutTitleString(string):
	from .mvrt import Core
	col = Core.GetStyleCollection()
	col.TitleString = string

@is_a_stub
def AnalyseTillDone(resolution=500, timeout=200):
	from .mvrt import Core
	prog = -1
	count = timeout
	sleep = resolution/1000.0

	assert Core.StartAnalysisProc(0), \
		("StartAnalysisProc failed: ", GetLastErrorDescription())
	try:
		while prog < 1:
			prog = Core.GetAnalysisProgress()
			print "Progress:", prog

			count -= 1
			assert count >= 0, "Timed out after %d repetitions." % timeout
			time.sleep(sleep)
	except:
		Core.StopAnalysisProc()
		raise
	return True

@is_a_stub
def MakeTillDone(mode, duration):
	from .mvrt import Core
	assert Core.MakeMuveeTimeline(mode, duration), \
		"MakeMuveeTimeline failed: " + GetLastErrorDescription()

@is_a_stub
def ThreadedMakeTillDone(mode, duration):
	from .mvrt import Core
	mode |= MakeFlags.THREADED
	assert Core.MakeMuveeTimeline(mode, duration), \
		"MakeMuveeTimeline failed: " + GetLastErrorDescription()
	try:
		count = 6000 # 15 minutes
		sleep = 0.05
		prog = -1
		while prog < 1:
			prog = Core.GetMakeProgress()
			print "Progress:", prog

			count -= 1
			assert count >= 0, 'Timed out'
			time.sleep(sleep)
	except:
		Core.CancelMake()
		raise

@is_a_stub
def PreviewUntil(timeline, width, height, until):
	import clr
	from .mvrt import Core
	clr.AddReference('System.Windows.Forms')
	from System.Windows.Forms import Form

	assert width > 0
	assert height > 0
	assert until > 0

	with Form(Text='MuFAT Test', Width=width, Height=height) as f:
		def checkProgress():
			prog = -1
			timeout = 3600
			while prog < until:
				prog = Core.GetRenderTL2WndProgress(timeline)
				assert prog >= 0, 'GetRenderTL2WndProgress failed: ' + GetLastErrorDescription()

				print "\rProgress:", prog,
				timeout -= 1
				assert timeout >= 0, 'Timed out!'
				time.sleep(1)
			print "done."
			f.Close()

		def teardown(*args):
			print 'Stopping.'
			Core.StopRenderTL2WndProc(timeline)
		f.Closing += teardown

		assert Core.SetupRenderTL2Wnd(timeline, f.Handle, 0, 0, width, height, None), \
			'SetupRenderTL2Wnd failed: ' + GetLastErrorDescription()
		Core.StartRenderTL2WndProc(timeline)
		threading.Thread(target=checkProgress).start()
		f.ShowDialog()

@is_a_stub
def PreviewTillDone(timeline=TimelineType.MUVEE, width=320, height=240):
	return PreviewUntil(timeline, width, height, until=1)
