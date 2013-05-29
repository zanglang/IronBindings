import threading, time

class Watchdog(threading.Thread):
	def __init__(self, process, timeout):
		super(Watchdog, self).__init__()
		self.process = process
		self.timeout = timeout
		self.daemon = True

	def run(self):
		print "Starting watchdog ..."
		time.sleep(self.timeout)

		# still alive
		if self.process is not None and \
				self.process.poll() is None:
			print "Process %d is still alive! Killing ..." % self.process.pid
			self.process.kill()
