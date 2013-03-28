import os, threading, time
from functools import wraps
from . import gen_stub, ArType, InitFlags, LoadFlags, MakeFlags, SourceType, TimelineType, \
	IMVCaptionHighlight, IMVExclude, IMVHighlight, IMVOperatorInfo, IMVSource, \
	IMVStyleCollection, IMVTargetRect, IMVTitleCredits
from .testing import generate_test


def is_a_stub(f):
	"""
	Marks the function as a test stub, so that `muvee.testing.MufatTestRunner`
	can discover and wrap the function as a `unittest.FunctionTestCase`
	 """
	@wraps(f)
	def _wrap(*args, **kwargs):
		return generate_test(f, *args, **kwargs)

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

def AddSource(src, srctype=SourceType.UNKNOWN, loadtype=LoadFlags.VERIFYSUPPORT):
	from .mvrt import Core
	if srctype == SourceType.UNKNOWN:
		# guess source type from the returned class name
		typename = IMVSource(src).TypeName
		if 'MVSource_Image' in typename:
			srctype = SourceType.IMAGE
		elif 'MVSource_Music' in typename:
			srctype = SourceType.MUSIC
		elif 'MVSource_Video' in typename:
			srctype = SourceType.VIDEO
	assert Core.AddSource(srctype, src, loadtype), \
			'AddSource failed: ' + GetLastErrorDescription()

def CreateSource(path, srctype):
	from .mvrt import Core
	# wrap IMVSource with stub
	src = IMVSource(Core.CreateMVSource(srctype))
	if srctype in [ SourceType.IMAGE, SourceType.MUSIC, SourceType.VIDEO ]:
		assert os.path.exists(path), "File %s does not exist" % path
		assert src.LoadFile(path, LoadFlags.VERIFYSUPPORT), \
			'LoadFile failed: ' + GetLastErrorDescription()
	elif srctype == SourceType.OPERATOR:
		assert os.path.exists(path), "File %s does not exist" % path
		assert src.LoadFile(path, LoadFlags.NULL), \
			'LoadFile failed: ' + GetLastErrorDescription()
	else:
		# not a file source type
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
	# cast IMVSource to IMVTargetRect
	rect = gen_stub(IMVTargetRect)(src)
	# add magic spots from variable arguments in 4-pairs
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
	# cast IMVSource to IMVCaptionHighlight
	hilite = gen_stub(IMVCaptionHighlight)(src)
	hilite.SetCaptionHighlight(caption, start, end, None)
	hilite.VerifyUserDescriptors()
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceVideoWithMagicMoments(path, *args):
	src = CreateSource(path, SourceType.VIDEO)
	# cast IMVSource to IMVHighlight
	hilite = gen_stub(IMVHighlight)(src)
	# add highlights from variable arguments in tuple pairs
	for i in xrange(0, len(args), 2):
		pair = args[i:i+2]
		assert len(pair) == 2
		hilite.SetHighlight(*pair)

	# test if highlights were set correctly
	hilite.VerifyUserDescriptors()
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceVideoWithExclusion(path, *args):
	src = CreateSource(path, SourceType.VIDEO)
	# cast IMVSource to IMVExclude
	exclude = gen_stub(IMVExclude)(src)
	# add exclusions from variable arguments in tuple pairs
	for i in xrange(0, len(args), 2):
		pair = args[i:i+2]
		assert len(pair) == 2
		exclude.SetExclusion(*pair)

	# test if exclusions were set correctly
	exclude.VerifyUserDescriptors()
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceAnchorOperator(scmfile, anchor_value):
	from .mvrt import Core
	assert Core.MusicSources.Count > 0, "No music sources loaded!"
	music = Core.MusicSources[0]

	src = CreateSource(scmfile, SourceType.OPERATOR)
	# setup anchor parameters
	op = gen_stub(IMVOperatorInfo)(src)
	op.SetParam("ANCHOR_MEDIA", music.UniqueID)
	op.SetParam("ANCHOR_TIME", anchor_value)

	AddSource(src, SourceType.OPERATOR, LoadFlags.NULL)

@is_a_stub
def ConfigRenderTL2File(path):
	from .mvrt import Core
	# check if file exists
	assert os.path.isfile(path) and os.path.splitext(path)[1] == '.bin'
	Core.ConfigRenderTL2File(path)

def GetLastErrorDescription():
	from .mvrt import Core
	return Core.GetLastErrorDescription()

@is_a_stub
def SetActiveMVStyle(style, check=False):
	"""
	Sets the current Muvee Style to `style`
	
	:param style: A string containing the name of the style, or a number representing
	    the n-th index in the styles list
	:param check: Whether to validate if the given parameter is in the list of
	    available styles first.
	"""

	from .mvrt import Core
	if check:
		assert Core.Styles.Count > 0, "No styles found!"
		# check if style name is valid
		assert style in map(lambda s: s.InternalName, IMVStyleCollection(Core.Styles))
	Core.SetActiveMVStyle(style)

@is_a_stub
def PutCreditsString(credits):
	from .mvrt import Core
	# cast IMVStyleCollection to IMVTitleCredits
	tc = gen_stub(IMVTitleCredits)(Core.Styles)
	tc.CreditsString = credits

@is_a_stub
def PutTitleString(title):
	from .mvrt import Core
	# cast IMVStyleCollection to IMVTitleCredits
	titles = gen_stub(IMVTitleCredits)(Core.Styles)
	titles.TitleString = title

@is_a_stub
def PutAspectRatio(ratio):
	from .mvrt import Core
	assert ratio in ArType.__dict__
	Core.AspectRatio = ratio

@is_a_stub
def PutDescriptorFolder(path):
	from .mvrt import Core
	if not os.path.exists(path):
		os.makedirs(path)
	Core.DescriptorFolder = path

@is_a_stub
def PutSyncSoundLevel(level):
	from .mvrt import Core
	assert 0 <= level <= 1
	Core.SyncSoundLevel = level

@is_a_stub
def PutMusicLevel(level):
	from .mvrt import Core
	assert 0 <= level <= 1
	Core.MusicLevel = level

@is_a_stub
def AnalyseTillDone(resolution=1000, timeout=600):
	from .mvrt import Core

	assert Core.StartAnalysisProc(0), \
		("StartAnalysisProc failed: ", GetLastErrorDescription())
	try:
		prog = -1
		count = timeout
		sleep = resolution/1000.0
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
	"""
	Calls `IMVCore.MakeMuveeTimeline` and blocks until making is done.
	
	:param mode: `muvee.MakeFlags` enum
	:param duration: Duration of muvee in seconds
	"""

	from .mvrt import Core
	assert Core.MakeMuveeTimeline(mode, duration), \
		"MakeMuveeTimeline failed: " + GetLastErrorDescription()

@is_a_stub
def ThreadedMakeTillDone(mode, duration):
	"""
	Calls `IMVCore.MakeMuveeTimeline` in a separate thread and polls its
	progress until making is done.
	
	:param mode: `muvee.MakeFlags` enum
	:param duration: Duration of muvee in seconds
	"""

	from .mvrt import Core
	mode |= MakeFlags.THREADED

	assert Core.MakeMuveeTimeline(mode, duration), \
		"MakeMuveeTimeline failed: " + GetLastErrorDescription()
	try:
		prog = -1
		count = timeout = 6000
		sleep = 1 # 1 second
		while prog < 1:
			prog = Core.GetMakeProgress()
			assert prog >= 0, "GetMakeProgress failed: " + GetLastErrorDescription()
			print "Progress:", prog

			count -= 1
			assert count >= 0, "Timed out after %d repetitions." % timeout
			time.sleep(sleep)
	except:
		Core.CancelMake()
		raise

@is_a_stub
def ThreadedMakeForSaveTillDone(mode, duration):
	"""
	Calls `IMVCore.MakeMuveeTimeline` in a separate thread with the
	`muvee.MakeFlags.FORSAVING` flag enabled, and polls its progress
	until making is done.
	
	:param mode: `muvee.MakeFlags` enum
	:param duration: Duration of muvee in seconds
	"""

	mode |= MakeFlags.FORSAVING
	ThreadedMakeTillDone(mode, duration)

@is_a_stub
def PreviewTillDone(timeline=TimelineType.MUVEE, width=320, height=240):
	"""
	Creates a WinForms Window and renders the muvee preview to it
	
	:param timeline: `muvee.TimelineFlag` enum
	:param width: Width of created window in pixels
	:param height: Height of created window in pixels
	"""

	import clr
	from .mvrt import Core
	clr.AddReference('System.Windows.Forms')
	from System.Windows.Forms import Form

	assert width > 0
	assert height > 0

	# create winforms window
	with Form(Text='MuFAT Test', Width=width, Height=height, TopMost=True) as f:
		# check progress in separate thread
		def checkProgress():
			prog = -1
			count = timeout = 3600
			sleep = 1
			try:
				while prog < 1.0:
					prog = Core.GetRenderTL2WndProgress(timeline)
					assert prog >= 0, "GetRenderTL2WndProgress failed: " + GetLastErrorDescription()
					print "Progress:", prog,

					count -= 1
					assert count >= 0, "Timed out after %d repetitions." % timeout
					time.sleep(sleep)
				print "done."
			finally:
				f.Close()

		# stop the rendering if window is closed
		def teardown(*args):
			print 'Stopping.'
			Core.StopRenderTL2WndProc(timeline)
			Core.ShutdownRenderTL2Wnd(timeline)
		f.Closing += teardown

		# setup and start the rendering
		assert Core.SetupRenderTL2Wnd(timeline, f.Handle, 0, 0, width, height, None), \
			'SetupRenderTL2Wnd failed: ' + GetLastErrorDescription()
		Core.StartRenderTL2WndProc(timeline)
		threading.Thread(target=checkProgress).start()
		f.ShowDialog()

@is_a_stub
def SaveTillDone(filename, resolution=1000, timeout=600):
	"""
	Saves the video to a filename
	
	:param filename: Path of video file to save to
	:param resolution: Time in milliseconds to check rendering progress
	:param timeout: How many checks before considered timed out
	"""

	from .mvrt import Core
	path = filename.replace("[CurrentStyle]", Core.GetActiveMVStyle())

	assert Core.StartRenderTL2FileProc(path, None, 0, 0, 0, 0, None) >= 0, \
			("StartRenderTL2FileProc failed: " + GetLastErrorDescription())
	try:
		prog = -1
		count = timeout
		sleep = resolution/1000.0
		while prog < 1:
			prog = Core.GetRenderTL2FileProgress()
			assert prog >= 0, "GetRenderTL2FileProgress failed: " + GetLastErrorDescription()
			print "Progress:", prog

			count -= 1
			assert count >= 0, "Timed out after %d repetitions." % timeout
			time.sleep(sleep)
	except:
		Core.StopRenderTL2FileProc()
		raise

@is_a_stub
def SaveTillDoneWithPreview(filename, resolution=1000, timeout=600, width=320, height=240):
	"""
	Saves the video to a filename
	
	:param filename: Path of video file to save to
	:param resolution: Time in milliseconds to check rendering progress
	:param timeout: How many checks before considered timed out
	"""

	import clr
	from .mvrt import Core
	clr.AddReference('System.Windows.Forms')
	from System.Windows.Forms import Form

	assert width > 0
	assert height > 0
	path = filename.replace("[CurrentStyle]", Core.GetActiveMVStyle())

	# create winforms window
	with Form(Text='MuFAT Test', Width=width, Height=height, TopMost=True) as f:
		# check progress in separate thread
		def checkProgress():
			prog = -1
			count = timeout
			sleep = resolution/1000.0
			try:
				while prog < 1:
					prog = Core.GetRenderTL2FileProgress()
					assert prog >= 0, "GetRenderTL2FileProgress failed: " + GetLastErrorDescription()
					print "Progress:", prog

					count -= 1
					assert count >= 0, "Timed out after %d repetitions." % timeout
					time.sleep(sleep)
				print "done."
			finally:
				f.Close()

		# stop the rendering if window is closed
		def teardown(*args):
			print 'Stopping.'
			Core.StopRenderTL2FileProc()
		f.Closing += teardown

		# setup and start the rendering
		assert Core.StartRenderTL2FileProc(path, f.Handle, 0, 0, width, height, None) >= 0, \
			("StartRenderTL2FileProc failed: " + GetLastErrorDescription())
		threading.Thread(target=checkProgress).start()
		f.ShowDialog()

@is_a_stub
def PreviewSourceTillDone(src, width=320, height=240):
	"""
	Creates a WinForms Window and renders the video preview to it
	
	:param src: source object to be rendered
	:param width: Width of created window in pixels
	:param height: Height of created window in pixels
	"""

	import clr
	clr.AddReference('System.Windows.Forms')
	from System.Windows.Forms import Form

	assert width > 0
	assert height > 0

	# create winforms window
	with Form(Text='MuFAT Test', Width=width, Height=height, TopMost=True) as f:
		# check progress in separate thread
		def checkProgress():
			prog = -1
			count = timeout = 3600
			sleep = 1
			try:
				while prog < 1.0:
					prog = src.GetRenderProgress()
					assert prog >= 0, "GetRenderProgress failed: " + GetLastErrorDescription()
					print "Progress:", prog,

					count -= 1
					assert count >= 0, "Timed out after %d repetitions." % timeout
					time.sleep(sleep)
				print "done."
			finally:
				f.Close()

		# stop the rendering if window is closed
		def teardown(*args):
			print 'Stopping.'
			src.StopRenderProc()
			src.ShutdownRender()
		f.Closing += teardown

		# setup and start the rendering
		assert src.SetupRender(f.Handle, 0, 0, width, height, None), \
			'SetupRender failed: ' + GetLastErrorDescription()
		src.StartRenderProc()
		threading.Thread(target=checkProgress).start()
		f.ShowDialog()
