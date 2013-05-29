import memcache, Queue

class MemcacheQueue(Queue.Queue):
	"""
	Memcached-based fifo queue, used for passing muFAT results between multiple
	processes, e.g. celery worker task and child muFAT runner
	"""
	def _init(self, key): #@UnusedVariable
		self.cache = memcache.Client(['wsm-miniserver.sg.muvee.net:11211'], debug=1)
		self.key = key

	def _qsize(self, len=len): #@ReservedAssignment
		queue = self.cache.get(self.key) or []
		return len(queue)

	def _put(self, item):
		queue = self.cache.get(self.key) or []
		queue.append(item)
		self.cache.set(self.key, queue, 3600)

	def _get(self):
		queue = self.cache.get(self.key) or []
		try:
			return queue.pop(0)
		finally:
			self.cache.set(self.key, queue, 3600)

	Empty = Queue.Empty
