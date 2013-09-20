import json, redis, Queue

class RedisQueue(Queue.Queue):
	"""
	Redis-based fifo queue, used for passing muFAT results between multiple
	processes, e.g. celery worker task and child muFAT runner
	"""
	def _init(self, key): #@UnusedVariable
		self.cache = redis.StrictRedis(host='thrall.muvee.com', port=6379, db=15)
		self.key = key

	def _qsize(self, len=len): #@ReservedAssignment
		return self.cache.llen(self.key)

	def _put(self, item):
		self.cache.expire(self.key, 3600)
		return self.cache.rpush(self.key, \
			isinstance(item, basestring) and item or json.dumps(item))

	def _get(self):
		self.cache.expire(self.key, 3600)
		item = self.cache.lpop(self.key)
		try:
			if item:
				item = json.loads(item)
		except:
			pass
		finally:
			return item

	Empty = Queue.Empty
