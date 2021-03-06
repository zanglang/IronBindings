"""
All function stubs that make up a muFAT run are implemented here. Essentially,
a 'stub' is any function that when called once inside a run performs any number
of tasks, while hiding the underlying nitty gritty details of mucking about with
muvee's COM interfaces.

All of these function stubs will be imported into the 'muvee.*' module namespace.

Example stubs:
- muvee.Init
- muvee.Release
- muvee.AddSourceImage
"""

import inspect, os, re, sys, threading, time
from functools import wraps
from xml.etree import ElementTree as etree
from . import gen_stub, ArType, InitFlags, LoadFlags, MakeFlags, SourceType, \
	TimelineType, IMVExclude, IMVHighlight, IMVImageInfo, IMVOperatorInfo, \
	IMVPrimaryCaption, IMVSource, IMVSource2, IMVStyleCollection, IMVStyleEx, \
	IMVSupportMultiCaptions, IMVTargetRect, IMVTitleCredits
from .testing import detect_media, generate_test, normalize
from .window import Window


def is_a_stub(f):
	"""
	Marks the function as a test stub, so that `muvee.testing.MufatTestRunner`
	can discover and wrap the function as a `unittest.FunctionTestCase`.

	Alternatively, when a testcase is run by `muvee.testing.run`, any functions
	decorated by '@is_a_stub' will be dynamically wrapped as a
	`unittest.FunctionTestCase` before being executed as part of an ongoing
	test suite.
	 """

	@wraps(f)
	def _wrap(*args, **kwargs):
		return generate_test(f, *args, **kwargs)

	setattr(_wrap, "is_a_stub", True)
	return _wrap

def is_true_or_non_zero(ret):
	return ret == None or ret == True or \
		(type(ret) in [ int, float ] and ret >= 0)


@is_a_stub
def Init(flags=InitFlags.DEFAULT):
	"""Initializes MVRuntime.MVCore"""

	from .mvrt import Core
	Core.Init(flags)

@is_a_stub
def Release():
	"""Releases the COM reference to MVRuntime"""

	from . import mvrt
	mvrt.Release()



def AddSource(src, srctype=SourceType.UNKNOWN, loadtype=LoadFlags.VERIFYSUPPORT):
	from .mvrt import Core
	# guess type from source object
	if srctype == SourceType.UNKNOWN:
		srctype = int(src.Type)
	assert Core.AddSource(srctype, src, loadtype), \
			'AddSource failed: ' + GetLastErrorDescription()

def CreateSource(path, srctype):
	"""
	Creates and returns an IMVSource object for the given file and source type.

	:param path: Path to the source file
	:param srctype: `muvee.SourceType` enumeration
	"""

	from .mvrt import Core
	src = Core.CreateMVSource(srctype)
	if srctype in [ SourceType.IMAGE, SourceType.MUSIC, SourceType.VIDEO ]:
		path = normalize(path)
		assert os.path.exists(path), "File %s does not exist" % path
		assert src.LoadFile(path, LoadFlags.VERIFYSUPPORT), \
			'LoadFile failed: ' + GetLastErrorDescription()
	elif srctype == SourceType.OPERATOR:
		assert os.path.exists(path), "File %s does not exist" % path
		assert src.LoadFile(path, LoadFlags.NULL), \
			'LoadFile failed: ' + GetLastErrorDescription()
	else:
		# not a file source type
		src2 = gen_stub(IMVSource2)(src)
		src2.Load(path, int(LoadFlags.CONTEXT))
	return src

@is_a_stub
def EnumAndSetMVStyle(sty):
	from .mvrt import Core
	styname = Core.Styles.EnumMVStyleByMod(sty)
	Core.SetActiveMVStyle(styname)

@is_a_stub
def AddSourceImage(path):
	src = CreateSource(path, SourceType.IMAGE)
	AddSource(src, SourceType.IMAGE, LoadFlags.VERIFYSUPPORT)

@is_a_stub
def AddSourceImageWithCaption(path, caption):
	from . import IMVCaptionCollection
	src = CreateSource(path, SourceType.IMAGE)
	if hasattr(src, 'Captions'):
		supports = src.Captions
	else:
		supports = gen_stub(IMVSupportMultiCaptions)(src).Captions
	captions = IMVCaptionCollection(supports)
	assert captions.AddCaption(caption) is not None, \
		'AddCaption failed: ' + GetLastErrorDescription()
	assert len(captions) > 0
	assert captions.VerifyUserDscrp(), \
		'VerifyUserDscrp failed: ' + GetLastErrorDescription()
	AddSource(src, SourceType.IMAGE, LoadFlags.VERIFYSUPPORT)

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
def AddSourceMusicClip(path, start, stop):
	src = CreateSource(path, SourceType.MUSIC)
	src.Start = start
	src.Stop = stop
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
def AddSourceVideoNoProxy(path):
	from .mvrt import Core
	src = Core.CreateMVSource(SourceType.VIDEO)
	path = normalize(path)
	assert os.path.exists(path), "File %s does not exist" % path
	assert src.LoadFile(path, int(LoadFlags.VERIFYSUPPORT)|int(LoadFlags.DISABLE_LOREZPROXY)), \
		'LoadFile failed: ' + GetLastErrorDescription()
	AddSource(src, SourceType.VIDEO, int(LoadFlags.VERIFYSUPPORT)|int(LoadFlags.DISABLE_LOREZPROXY))

@is_a_stub
def AddSourceVideoWithCapHL(path, caption, start, end):
	src = CreateSource(path, SourceType.VIDEO)
	# cast IMVSource to IMVCaptionHighlight
	from . import IMVCaptionHighlight
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
def AddSourceAnchorOperator(scmfile, music_idx, anchor_value):
	from .mvrt import Core
	assert Core.MusicSources.Count > music_idx, "Music index out-of-range!"
	music = Core.MusicSources[music_idx]

	src = CreateSource(scmfile, SourceType.OPERATOR)
	# setup anchor parameters
	op = gen_stub(IMVOperatorInfo)(src)
	op.SetParam("ANCHOR_MEDIA", music.UniqueID)
	op.SetParam("ANCHOR_TIME", anchor_value)

	AddSource(src, SourceType.OPERATOR, LoadFlags.NULL)


@is_a_stub
def AddCopyright(message, color=None, x=None, y=None, width=None, height=None):
	from .mvrt import Core

	# set copyright message
	primary = gen_stub(IMVPrimaryCaption)(Core)
	primary.PrimaryCaption.Text = message
	fmt = primary.PrimaryCaption.TextDisplayFormat

	# set formatting
	if color is not None:
		fmt.BackgroundColor = color
	if x is not None:
		fmt.TextRectXCoord = x
	if y is not None:
		fmt.TextRectYCoord = y
	if width is not None:
		fmt.TextRectWidth = width
	if height is not None:
		fmt.TextRectHeight = height

	primary.PrimaryCaption.TextDisplayFormat = fmt

@is_a_stub
def AddLogo(path, placement=None, opacity=None, crop=None):
	from . import IMVProductionOverlay
	from .mvrt import Core

	# set logo
	overlay = gen_stub(IMVProductionOverlay)(Core)
	path = normalize(path)
	assert os.path.isfile(path)
	overlay.OverlaySourceFile = path

	if placement is not None and len(placement) == 4:
		assert all(type(arg) in [float, int] for arg in placement), "Arguments must be floats"
		overlay.SetOverlayPlacement(*placement)

	if opacity is not None:
		assert type(opacity) in [float, int]
		overlay.OverlayOpacity = opacity

	if crop is not None:
		assert all(type(arg) in [float, int] for arg in crop), "Arguments must be floats"
		overlay.SetOverlayCropRect(*crop)

@is_a_stub
def ConfigRenderTL2File(path):
	from .mvrt import Core
	# check if file exists
	path = normalize(path)
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
	if hasattr(Core, "ActiveMVStyle"):
		Core.ActiveMVStyle = style
	else:
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
	assert ratio in ArType.__dict__.values()
	Core.AspectRatio = ratio

@is_a_stub
def PutDescriptorFolder(path):
	from .mvrt import Core
	path = normalize(path)
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

def CheckProgress(poll_func, poll_flag=None, timeout=3600, sleep=1, onStop=None):
	"""
	Runs a while loop to check a task's running progress until it completes,
	times out, or stalls from inactivity.
	
	:param poll_func: Function callback to use to fetch the current progress.
		Must return a number.
	:param poll_flag: `threading.Event` flag object to signal if a poll function
		should not be executed anymore (e.g. caller function has stopped a process)
	:param timeout: How many seconds before the polled task is considered to
		have timed out and may be cancelled. Default: 60 minutes.
	:param sleep: How many seconds to wait in between polls. Default: 1 second.
	:param onStop: Function to call when the loop has indicated that the task
		is complete, or has timed out, or has failed due to an exception.
	"""

	last_prog = prog = -1
	last_changed = time.time()
	count = timeout
	try:
		while prog < 1.0:
			if poll_flag is not None and poll_flag.isSet():
				print "Stopping...",
				break

			# fetch current progress from function
			prog = poll_func.__call__()
			print r"Progress: %.2f" % prog

			if prog <= 0.0 or (prog - last_prog) < 0.01:
				# check if progress was stuck in the last 5 minutes
				assert time.time() - last_changed < 300, \
					("Progress stuck at %.2f%% for over 5 minutes!" % prog)
			else:
				last_prog = prog
				last_changed = time.time()

			count -= 1
			assert count >= 0, "Timed out after %d repetitions." % timeout
			time.sleep(sleep)
	except KeyboardInterrupt:
		pass
	finally:
		# cleanup and call teardown function
		print "done."
		if onStop is not None:
			onStop.__call__()

def StartCheckProgress(poll_func, poll_flag=None, timeout=3600, sleep=1, onStop=None):
	"""
	Same as `CheckProgress`, but starts another thread to run it asynchronously.
	"""

	threading.Thread(target=CheckProgress, \
		args=(poll_func, poll_flag, timeout, sleep, onStop)).start()

@is_a_stub
def AnalyseTillDone(resolution=1000, timeout=1800):
	"""
	Starts analyzing all added sources in a separate thread and polls its
	progress until analysis is done. The function will timeout after
	`resolution` x `timeout` milliseconds.
	
	:param resolution: Frequency to poll for progress updates in milliseconds.
		Default: 1000 milliseconds.
	:param timeout: How many polls until the function is considered timed out.
		Default: 1800 polls.
	"""

	from .mvrt import Core

	assert is_true_or_non_zero(Core.StartAnalysisProc(0)), \
		("StartAnalysisProc failed: ", GetLastErrorDescription())
	CheckProgress(lambda: Core.GetAnalysisProgress(), timeout=timeout,
			sleep=resolution/1000.0, onStop=lambda: Core.StopAnalysisProc())

@is_a_stub
def MakeTillDone(mode, duration):
	"""
	Calls `IMVCore.MakeMuveeTimeline` and blocks until making is done.
	
	:param mode: `muvee.MakeFlags` enum
	:param duration: Duration of muvee in seconds
	"""

	from .mvrt import Core
	assert is_true_or_non_zero(Core.MakeMuveeTimeline(mode, duration)), \
		"MakeMuveeTimeline failed: " + GetLastErrorDescription()

@is_a_stub
def ThreadedMakeTillDone(mode, duration):
	"""
	Calls `IMVCore.MakeMuveeTimeline` in a separate thread and polls its
	progress until making is done. The function will timeout after 600 seconds.
	
	:param mode: `muvee.MakeFlags` enum
	:param duration: Duration of muvee in seconds
	"""

	from .mvrt import Core
	mode |= MakeFlags.THREADED

	assert is_true_or_non_zero(Core.MakeMuveeTimeline(mode, duration)), \
		"MakeMuveeTimeline failed: " + GetLastErrorDescription()
	def poll():
		prog = Core.GetMakeProgress()
		assert prog >= 0, "GetMakeProgress failed: " + GetLastErrorDescription()
		return prog
	CheckProgress(poll, timeout=600, onStop=lambda: Core.CancelMake())

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
	Creates a WinForms Window and renders the muvee preview to it. The function
	will timeout after 3600 seconds.
	
	:param timeline: `muvee.TimelineFlag` enum
	:param width: Width of created window in pixels
	:param height: Height of created window in pixels
	"""

	from .mvrt import Core
	assert width > 0
	assert height > 0
	flag = threading.Event()

	# create winforms window
	class Preview(Window):
		def __enter__(self):
			# setup and start the rendering
			assert is_true_or_non_zero(
					Core.SetupRenderTL2Wnd(timeline, self.hwnd, 0, 0, width, height, None)), \
					'SetupRenderTL2Wnd failed: ' + GetLastErrorDescription()
			Core.StartRenderTL2WndProc(timeline)
			StartCheckProgress(self.poll, flag, onStop=lambda: self.close())
			return self

		def poll(self):
			# get preview progress
			prog = Core.GetRenderTL2WndProgress(timeline)
			assert prog >= 0, "GetRenderTL2WndProgress failed: " + GetLastErrorDescription()
			return prog

		def __exit__(self, *args):
			print 'Stopping.'
			flag.set()
			Core.StopRenderTL2WndProc(timeline)
			Core.ShutdownRenderTL2Wnd(timeline)

		def resized(self, *args):
			assert is_true_or_non_zero(
					Core.RefreshTL2Wnd(timeline, self.hwnd, 0, 0, width, height, None)), \
					'RefreshTL2Wnd failed: ' + GetLastErrorDescription()

	with Preview(width, height) as p:
		p.show()


@is_a_stub
def SaveTillDone(filename, resolution=1000, timeout=1800):
	"""
	Saves the video to a filename. The function will timeout after
	`resolution` x `timeout` milliseconds.
	
	:param filename: Path of video file to save to
	:param resolution: Frequency to poll for progress updates in milliseconds.
		Default: 1000 milliseconds.
	:param timeout: How many polls until the function is considered timed out.
		Default: 1800 polls.
	"""

	from .mvrt import Core
	caller = inspect.getouterframes(inspect.currentframe())[1][1]
	runname = os.path.splitext(os.path.basename(caller))[0]
	path = filename.replace("[CurrentStyle]", Core.GetActiveMVStyle()) \
					.replace("[ConfigName]", runname)
	path = normalize(path)

	assert is_true_or_non_zero(
			Core.StartRenderTL2FileProc(path, None, 0, 0, 0, 0, None)), \
			("StartRenderTL2FileProc failed: " + GetLastErrorDescription())
	def poll():
		prog = Core.GetRenderTL2FileProgress()
		assert prog >= 0, "GetRenderTL2FileProgress failed: " + GetLastErrorDescription()
		return prog
	StartCheckProgress(self.poll, timeout=timeout, \
		onStop=lambda: Core.StopRenderTL2FileProc())

@is_a_stub
def SaveTillDoneWithPreview(filename, resolution=1000, timeout=1800, width=320, height=240):
	"""
	Saves the video to a filename. The function will timeout after
	`resolution` x `timeout` milliseconds.
	
	:param filename: Path of video file to save to
	:param resolution: Frequency to poll for progress updates in milliseconds.
		Default: 1000 milliseconds.
	:param timeout: How many polls until the function is considered timed out.
		Default: 1800 polls.
	"""

	from .mvrt import Core
	assert width > 0
	assert height > 0
	caller = inspect.getouterframes(inspect.currentframe())[-1][1]
	runname = os.path.splitext(os.path.basename(caller))[0]
	path = filename.replace("[CurrentStyle]", Core.GetActiveMVStyle()) \
					.replace("[ConfigName]", runname)
	path = normalize(path)
	flag = threading.Event()

	# create winforms window
	class Preview(Window):
		def __enter__(self):
			# setup and start the rendering
			assert is_true_or_non_zero(
				Core.StartRenderTL2FileProc(path, self.hwnd, 0, 0, width, height, None)), \
				("StartRenderTL2FileProc failed: " + GetLastErrorDescription())
			StartCheckProgress(self.poll, flag, timeout=timeout, \
					sleep=resolution/1000.0, onStop=lambda: self.close())
			return self

		def poll(self):
			# get saving progress
			prog = Core.GetRenderTL2FileProgress()
			assert prog >= 0, "GetRenderTL2FileProgress failed: " + GetLastErrorDescription()
			return prog

		def __exit__(self, *args):
			print 'Stopping.'
			flag.set()
			Core.StopRenderTL2FileProc()

		def resized(self, *args):
			assert is_true_or_non_zero(
					Core.RefreshTL2File(self.hwnd, 0, 0, width, height, None)), \
					'RefreshTL2File failed: ' + GetLastErrorDescription()

	with Preview(width, height) as p:
		p.show()

def PreviewSourceTillDone(src, width=320, height=240):
	"""
	Creates a WinForms Window and renders the video preview to it
	
	:param src: source object to be rendered
	:param width: Width of created window in pixels
	:param height: Height of created window in pixels
	"""

	assert width > 0
	assert height > 0
	flag = threading.Event()

	# create winforms window
	class Preview(Window):
		def __enter__(self):
			# setup and start the rendering
			assert is_true_or_non_zero(
					src.SetupRender(self.hwnd, 0, 0, width, height, None)), \
					'SetupRender failed: ' + GetLastErrorDescription()
			src.StartRenderProc()
			StartCheckProgress(self.poll, flag, timeout=3600, onStop=lambda: self.close())
			return self

		def poll(self):
			# get preview progress
			prog = src.GetRenderProgress()
			assert prog >= 0, "GetRenderProgress failed: " + GetLastErrorDescription()
			return prog

		def __exit__(self, *args):
			print 'Stopping.'
			flag.set()
			src.StopRenderProc()
			src.ShutdownRender()

		def resized(self, *args):
			assert is_true_or_non_zero(
					src.RefreshRender(self.hwnd, 0, 0, width, height, None)), \
					'RefreshRender failed: ' + GetLastErrorDescription()

	with Preview(width, height) as p:
		p.show()

@is_a_stub
def AddSourceVideoWithPreviewTillDone(path, height=320, width=240):
	"""
	Adds a video source and previews it.
	
	:param path: Location of video file to be added
	:param width: Width of created window in pixels
	:param height: Height of created window in pixels
	"""

	src = CreateSource(path, SourceType.VIDEO)
	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)
	PreviewSourceTillDone(src, height, width)

def translate_alignment(align):
	"""
	Decodes an integer into a tuple for horizontal and vertical height
	
	:param align: alignment integer to decode
	"""

	h = v = 0
	bits = (align & 0x38) >> 3
	if bits & 0x4 == bits:
		v = 0x1 # top
	elif bits & 0x2 == bits:
		v = 0x10 # center
	elif bits & 0x1 == bits:
		v = 0x2 # bottom
	else:
		return h, v
	bits = align & 0x7
	if bits & 0x4 == bits:
		h = 0x4 # left
	elif bits & 0x2 == bits:
		h = 0x10 # center
	elif bits & 0x1 == bits:
		h = 0x8 # right
	else:
		return h, v
	return h, v

def add_image(xml):
	"""
	Adds an image from a .rvl project file XML node
	"""

	from . import IMVCoreFactory, IMVSourceCaption
	from .mvrt import Core

	# create image source
	path = xml.find('name').text
	assert os.path.isfile(path)
	src = CreateSource(path, SourceType.IMAGE)

	# add magic spot rectangles
	magicspot = xml.find('magicSpot')
	if magicspot is not None:
		rect = gen_stub(IMVTargetRect)(src)
		if int(magicspot.attrib.get('activetype', 0)) > 0:
			for r in magicspot.findall('targetrects/rect'):
				rect.AddTargetRect(float(r.attrib['X1']), float(r.attrib['X2']), \
						float(r.attrib['Y1']), float(r.attrib['Y2']))

	# captions
	caption = xml.find('caption')
	if caption is not None:
		factory = gen_stub(IMVCoreFactory)(Core)
		fmt = factory.CreateMVTextFormatObj()
		fmt.LogFontStr = caption.attrib['font']
		fmt.Color = long(caption.attrib['fontcolor'])
		fmt.TextRectXCoord = float(caption.attrib['offsetX'])
		fmt.TextRectYCoord = float(caption.attrib['offsetY'])
		fmt.TextRectHeight = float(caption.attrib['height'])
		fmt.TextRectWidth = float(caption.attrib['width'])
		fmt.HorAlign, fmt.VertAlign = translate_alignment(long(caption.attrib['align']))
		cap = gen_stub(IMVSourceCaption)(src)
		cap.Caption = caption.attrib['string']
		cap.TextDisplayFormat = fmt

	# orientation and duration
	info = gen_stub(IMVImageInfo)(src)
	info.SetOrientation(float(xml.find('rotation').text), True)
	info.MinImgSegDuration = float(xml.find('minDur').text)

	AddSource(src, SourceType.IMAGE, LoadFlags.VERIFYSUPPORT)

def add_music(xml):
	"""
	Adds a music file from a .rvl project file XML node
	"""

	path = xml.find('name').text
	assert os.path.isfile(path)
	src = CreateSource(path, SourceType.MUSIC)
	start = float(xml.find('cliprange').attrib['start'])
	stop = float(xml.find('cliprange').attrib['stop'])
	if start != stop:
		src.Start, src.Stop = start, stop
	AddSource(src, SourceType.MUSIC, LoadFlags.VERIFYSUPPORT)

def add_video(xml):
	"""
	Adds a video file from a .rvl project file XML node
	"""

	from . import IMVCoreFactory, IMVCaptionHighlight
	from .mvrt import Core

	# create video source
	path = xml.find('name').text
	assert os.path.isfile(path)
	src = CreateSource(path, SourceType.VIDEO)

	# captions
	for caption in xml.findall('captions/caption'):
		factory = gen_stub(IMVCoreFactory)(Core)
		fmt = factory.CreateMVTextFormatObj()
		fmt.LogFontStr = caption.find('font').text
		fmt.Color = long(caption.find('fontcolor').text)
		fmt.TextRectXCoord = float(caption.find('offsetX').text)
		fmt.TextRectYCoord = float(caption.find('offsetY').text)
		fmt.TextRectHeight = float(caption.find('height').text)
		fmt.TextRectWidth = float(caption.find('width').text)
		fmt.HorAlign, fmt.VertAlign = translate_alignment(long(caption.find('align').text))
		cap = gen_stub(IMVCaptionHighlight)(src)
		cap.SetCaptionHighlight(caption.find('string').text,
				float(caption.find('timeStart').text),
				float(caption.find('timeEnd').text),
				fmt)

	# highlights
	for hilite in xml.findall('highlights/highlight'):
		h = gen_stub(IMVHighlight)(src)
		h.SetHighlight(float(hilite.find('start').text), float(hilite.find('stop').text))

	# exclusions
	for exclude in xml.findall('excludes/exclude'):
		e = gen_stub(IMVExclude)(src)
		e.SetIMVExclude(float(exclude.find('start').text), float(exclude.find('stop').text))

	# clipping
	start = float(xml.find('cliprange').attrib['start'])
	stop = float(xml.find('cliprange').attrib['stop'])
	if start != stop:
		src.Start, src.Stop = start, stop

	AddSource(src, SourceType.VIDEO, LoadFlags.VERIFYSUPPORT)

def add_settings(xml):
	"""
	Load project configuration from a .rvl project file XML node
	"""

	from . import IMVCoreFactory
	from .mvrt import Core
	Core.SetActiveMVStyle(xml.find('SelectedStyle').text)
	factory = gen_stub(IMVCoreFactory)(Core)

	# style parameters
	if xml.find('SuperStyles[@default="0"]/parameter') is not None:
		ex = gen_stub(IMVStyleEx)(Core.GetStyleCollection())
		style = xml.find('SelectedStyle').text
		for p in xml.findall('SuperStyles/parameter'):
			ex.SetParam(style, p.attrib['name'], float(p.attrib['value']))

	# style parameter strings
	if xml.find('StyleTextParams/parameter') is not None:
		ex = gen_stub(IMVStyleEx3)(Core.GetStyleCollection())
		style = xml.find('SelectedStyle').text
		for p in xml.findall('StyleTextParams/parameter'):
			ex.SetStringParam(style, p.attrib['name'], p.attrib['value'])

	# titles
	tc = gen_stub(IMVTitleCredits)(Core.Styles)
	if xml.find('EnableTitle').text == '1':
		fmt = factory.CreateMVTextFormatObj()
		fmt.LogFontStr = xml.find('TitleFont').text
		fmt.Color = long(xml.find('TitleColor').text)
		tc.TitleString = xml.find('TitleText').text
		tc.TitleTextFormat = fmt
		type = int(xml.find('TitleBackgroundType').text)
		if type == 1:
			tc.TitleBackgroundColor = long(xml.find('TitleBackgroundColor').text)
		elif type == 2:
			tc.TitleBackgroundImage = xml.find('TitleBackgroundImage').text

	# credits
	if xml.find('EnableCredits').text == '1':
		fmt = factory.CreateMVTextFormatObj()
		fmt.LogFontStr = xml.find('CreditsFont').text
		fmt.Color = long(xml.find('CreditsColor').text)
		tc.CreditsString = xml.find('CreditsText').text
		tc.CreditsTextFormat = fmt
		type = int(xml.find('CreditsBackgroundType').text)
		if type == 1:
			tc.CreditsBackgroundColor = long(xml.find('CreditsBackgroundColor').text)
		elif type == 2:
			tc.CreditsBackgroundImage = xml.find('CreditsBackgroundImage').text

	# volume control
	Core.AudioExtLevel = float(xml.find('AudioMix/Voiceover').text)
	Core.SoundEffectLevel = float(xml.find('AudioMix/SoundFx').text)
	Core.SyncSoundLevel = float(xml.find('AudioMix/Video').text)
	Core.MusicLevel = float(xml.find('AudioMix/Music').text)

@is_a_stub
def LoadRvlProject(path):
	"""
	Loads any image, music or video sources from a .rvl project file as well as
	relevant project settings.

	:param path: Path to .rvl project file
	"""

	path = normalize(path)
	assert os.path.isfile(path) and os.path.splitext(path)[1] == ".rvl"
	xml = etree.parse(path)

	# find all source files
	sources = [(f, SourceType.IMAGE) for f in xml.findall('image/file')] + \
				[(f, SourceType.MUSIC) for f in xml.findall('audio/file')] + \
				[(f, SourceType.VIDEO) for f in xml.findall('video/file')]

	# sort sources by predefined indexes
	def cmp_index(x, y):
		if x[0].find('index') is None:
			return -1
		if y[0].find('index') is None:
			return 1
		return cmp(int(x[0].find('index').text), int(y[0].find('index').text))
	sources.sort(cmp=cmp_index)
	detect_media(*[s[0].find('name').text for s in sources])

	for src, type in sources:
		if type == SourceType.IMAGE:
			add_image(src)
		elif type == SourceType.MUSIC:
			add_music(src)
		elif type == SourceType.VIDEO:
			add_video(src)
		else:
			raise NotImplementedError(str(type))

	# process settings
	add_settings(xml.find('settings'))

@is_a_stub
def VerifyVideo(src_file, expected_width, \
				expected_height, \
				expected_aspect_ratio, \
				expected_aspect_ratio_x, \
				expected_aspect_ratio_y):
	try:
		from . import IMVVideoInfo3
	except:
		# mac doesn't have IMVVideoInfo3
		from . import IMVVideoInfo2 as IMVVideoInfo3

	src = CreateSource(src_file, SourceType.VIDEO)
	vid_info = gen_stub(IMVVideoInfo3)(src)
	assert vid_info.width == expected_width and vid_info.height == expected_height, \
			"Media width/height verification failed: %s" % src_file
	assert vid_info.AspectRatio == int(expected_aspect_ratio), \
			"Media aspect ratio verification failed: %s" % src_file
	assert vid_info.AspectRatioX == expected_aspect_ratio_x and \
			vid_info.AspectRatioY == expected_aspect_ratio_y, \
			"Media aspect ratio verification failed: %s" % src_file

@is_a_stub
def CheckLastTimelineForRange(floor, ceiling):
	from .mvrt import Core
	dur = Core.GetTimelineDuration(TimelineType.FINALPREV)	# TimelineType for backward compatibility
	assert dur <= ceiling, \
		   "dur = " + str(dur) + ", ceiling = " + str(ceiling)
	assert dur >= floor, \
		   "dur = " + str(dur) + ", floor = " + str(floor)

@is_a_stub
def ClearDescriptors():
	from .mvrt import Core
	path = os.path.join(Core.CommonDataFolder, "dscrp")
	if os.path.isdir(path):
		for root, dirs, files in os.walk(path):
			for f in files:
				print "Deleting", os.path.join(root, f)
				os.remove(os.path.join(root, f))
