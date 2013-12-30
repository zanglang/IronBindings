import codecs, json, os, re, requests, shutil, socket, subprocess, sys, time
from hashlib import sha1
from lxml import etree
from queue import RedisQueue
from testing import normalize
from watchdog import Watchdog
import boto

DB = "dailygrid_MacSDK"
DBKEY = None
HOST = socket.gethostname().split(".")[0]
PRINT_OUTPUT = True
MUVEEDEBUG = "/muveedebug"
SERVER_URL = "http://mufat.muvee.com/"

# Amazon login details
AWS_ACCESS_KEY = "***REMOVED***"
AWS_SECRET_KEY = "***REMOVED***"


def get_asserts(data):
	"""
	:param data: Blob of text containing a test run's console output
	:rtype: A tuple containing the number of assertions found in the log file,
			and second, a dictionary containing a unique set of assertions
			found.
	"""

	uniques = {}
	asserts = re.findall("^\s*([0-9\-\:\.\s]*)\s*([\-\_.\w\d\(\)]*)" \
			"\s*ASSERT FAILED\s*:\s*(.*?)\n", \
			data, re.MULTILINE | re.DOTALL)
	for k in asserts:
		key = sha1(k[1] + k[2]).hexdigest()
		count = uniques.has_key(key) and (uniques[key]["occurances"] + 1) or 1
		uniques[key] = { "file": k[1], "message": k[2] , "occurances": count }
	return len(asserts), uniques


def load_suite(name, from_file="runconfig.xml"):
	"""
	Parse run configuration file and load the appropriate tests to run given a
	muFAT suite name.

	:param name: Name of muFAT suite to load runs for
	"""

	xml = etree.parse(from_file).getroot()
	suites = xml.xpath("suite[@name='%s' and not(@enabled='false')]" % name)
	if not suites:
		raise Exception("Suite '%s' not found in runconfig.xml" % name)
	suite = suites[0]
	runs = suite.xpath("run[not(@enabled='false')]/@name")
	runs = map(str, runs)
	if suite.get("directory") is not None:
		# runfiles in these folders will be ignored
		ignored = set(["include", "ignore", "includes", "__init__"])
		path = normalize(os.path.join(r"y:\mufat\testruns\regressionpaths", suite.get("directory")))
		for root, dirs, files in os.walk(path): #@UnusedVariable
			for f in files:
				if os.path.splitext(f)[1] != ".py" or \
						os.path.splitext(f)[0] in ignored or \
						set(root.lower().split(os.path.sep)).intersection(ignored):
					continue
				runs.append(os.path.join(root, f))

	assert len(runs), "No runs found in suite '%s'!" % name
	return runs


def do_child(runname, debug=False):
	"""
	Run a test inside the child process.

	@param runname:	Name of muFAT run
	@param debug:	Whether to actually store results
	"""

	# load and execute tests
	from .mvrt import Core
	from runpy import run_path

	# pre-clean data folders
	if os.path.isdir(Core.UserDataFolder):
		print "Cleaning folder:", Core.UserDataFolder
		shutil.rmtree(Core.UserDataFolder)

	path = normalize(os.path.join(r"Y:\mufat\testruns\regressionpaths", runname))
	sys.path.append(os.path.dirname(path))
	results = run_path(path, run_name="__main__")

	# return results to parent for processing
	if not debug:
		q = RedisQueue("_".join(["Q", DBKEY, HOST]))
		q.put({
			'pass': results["passed"],
			'fail': results["failed"],
			'untested': results["skipped"],
			'summary': results["logfile"],
			'shutdown': True,
			'crash': results["skipped"],
			'retained_samples': [],
			'return_code': 0,
			'timeout': False,
			'svn_rev': Core.GetRuntimeSpecialBuild()
		})

	Core.Release()
	sys.exit(0)


def main(suites_or_runs, debug=False):
	"""
	Runs a list of suites of runs inside the parent process.

	:param suites_or_runs: A list of suite names or run names to be executed
	:param debug: Whether to actually store results
	"""

	suites = {}
	# argument is just a single string
	if isinstance(suites_or_runs, basestring):
		suites_or_runs = [suites_or_runs]
	for arg in suites_or_runs:
		if os.path.splitext(arg)[1] != ".py":
			if not suites.has_key(arg):
				suites[arg] = set()
			suites[arg].update(load_suite(arg))
		else:
			if not suites.has_key("mac"):
				suites["mac"] = set()
			suites["mac"].add(arg)

	global DBKEY
	DBKEY = DBKEY or time.strftime("%Y-%m-%d,%H-%M-%S")

	# cleanup/create necessary folders
	if not os.path.exists(MUVEEDEBUG):
		os.makedirs(MUVEEDEBUG)
	cachedir = os.path.expanduser("~/Library/Application\ Support/muvee\ Technologies/071203")
	if os.path.exists(cachedir):
		shutil.rmtree(cachedir)

	# python command to launch the child process
	svn_rev = 0
	cmd = [sys.executable, "-u", "-m", "muvee.runner"]
	if sys.platform == "darwin":
		cmd = ["arch -i386"] + cmd

	# prepare to upload logfiles to Amazon S3
	new_key = boto.connect_s3(AWS_ACCESS_KEY, AWS_SECRET_KEY) \
			.get_bucket("mufat").new_key
	subkey = time.strftime("%Y-%m-%d_%H_%M", time.strptime(DBKEY, "%Y-%m-%d,%H-%M-%S"))

	global PRINT_OUTPUT
	for suite, runs in suites.iteritems():
		for run in runs:
			shortname = os.path.splitext(os.path.basename(run))[0]
			start = time.time()
			logfile = os.path.join(MUVEEDEBUG, "(%s)%s_Log.txt" % \
					(time.strftime("%Y%m%d%H%M%S", time.localtime(start)), shortname))

			# run child process
			print "Starting muFAT process for %s (%s)." % (run, suite)
			p = subprocess.Popen(" ".join(cmd + ['"' + run + '"', "--child", "--key", DBKEY]),
								shell=True,
								stdout=subprocess.PIPE,
								stderr=subprocess.STDOUT)

			# start a watchdog to kill the child if it takes too long
			Watchdog(p, 3600).start()

			# collect output text for processing later
			with codecs.open(logfile, "w+", "utf-8") as f:
				while True:
					line = unicode(p.stdout.readline(), errors="replace")
					if not line:
						break
					f.write(line)
					if PRINT_OUTPUT:
						print line.encode("ascii", errors="replace"),

			# block until process completes and record running time
			p.communicate()
			minutes, seconds = divmod(time.time() - start, 60)
			hours, minutes = divmod(minutes, 60)

			# read results from child
			try:
				q = RedisQueue("_".join(["Q", DBKEY, HOST]))
				result = q.get_nowait()
			except RedisQueue.Empty:
				# no results - child probably died?
				result = {
					'pass': 0,
					'fail': 0,
					'untested': 0,
					'summary': '',
					'shutdown': False,
					'crash': True,
					'retained_samples': [],
					'return_code':-1,
					'timeout': False
				}

			# parse log file for assertions and upload to Amazon S3
			try:
				with open(logfile, "r") as f:
					asserts, assertdict = get_asserts(f.read())
					result.update({
						'assert': asserts,
						'unique_asserts': assertdict,
						'time': (hours, minutes, seconds)
					})
					key = new_key("%s/%s/(%s)%s_Log.txt" % (HOST.upper(), subkey, \
						time.strftime("%Y%m%d%H%M%S", time.localtime(start)), shortname))
					key.set_contents_from_file(f, reduced_redundancy=True, rewind=True)
					key.make_public()
					result["log"] = "https://mufat.s3.amazonaws.com/" + key.key
			finally:
				os.remove(logfile)

			# upload summary file to Amazon S3
			if result.get("summary"):
				summary = result["summary"]
				try:
					key = new_key("%s/%s/%s" % (HOST.upper(), subkey, shortname + ".txt"))
					key.set_contents_from_filename(summary, reduced_redundancy=True)
					key.make_public()
					result["summary"] = "https://mufat.s3.amazonaws.com/" + key.key
				finally:
					os.remove(summary)

			if result.get("svn_rev"):
				svn_rev = result["svn_rev"]

			if not debug:
				print "Uploading intermediate results..."
				r = requests.post(SERVER_URL + "%s/%s/%s/submit" % (DB, DBKEY, HOST), {
					'suite': suite,
					'runname': run,
					'results': json.dumps(result)
				}, headers={ "X-NO-LOGIN": "1" })
				r.raise_for_status()


if __name__ == "__main__":
	import argparse
	p = argparse.ArgumentParser()
	p.add_argument("-c", "--child", action="store_true")
	p.add_argument("-d", "--debug", action="store_true")
	p.add_argument("--key", help="Database key to use")
	p.add_argument("suites_or_runs", help="Suites or runs to run")
	args = p.parse_args()

	if not args.suites_or_runs:
		p.error("No suites or runs defined!")
	if args.key:
		DBKEY = args.key

	import logging
	logging.getLogger("boto").setLevel(logging.CRITICAL)

	# child process
	if args.child:
		do_child(args.suites_or_runs, debug=args.debug)
	else:
		main(args.suites_or_runs, debug=args.debug)
