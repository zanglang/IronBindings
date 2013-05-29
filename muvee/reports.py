from __future__ import with_statement
import json, MySQLdb, os, zlib
try:
	import memcache
except:
	memcache = None

class Report:
	def __init__(self, **kwargs):
		def __add(key):
			if kwargs.has_key(key):
				setattr(self, key, kwargs[key])
		for key in kwargs.keys():
			__add(key)

	def save(self, db=None, key=None):
		if [k for k in ("name", "report", "svn_rev") if not hasattr(self, k)] or \
			(not db and not hasattr(self, "db")) or \
			(not key and not hasattr(self, "key")):
			raise Exception("Report is missing attributes!")

		db = db or self.db
		key = key or self.key
		data = zlib.compress(json.dumps(self.report), 9)
		with connect() as cursor:
			cursor.execute(
					"""
					INSERT INTO %s (`key`, `name`, `report`, `svn_rev`)
						VALUES (%%s, %%s, %%s, %%s)
						ON DUPLICATE KEY UPDATE report = VALUES(report)
					""" % db,
					(key, self.name, data, self.svn_rev)
				)

		# flush key from cache
		if memcache:
			cachekey = "_".join(["REPORT", db, key, self.name])
			memcache.Client(['192.168.81.119:11211'], debug=1).delete(cachekey)

def load(db, key, machine=None):
	# convert SQLite file path to MySQL table name
	if db.endswith(".db"):
		db = os.path.splitext(os.path.basename(db))[0]
	if memcache:
		_cache = memcache.Client(['192.168.81.119:11211'], debug=1)

	reports = []

	# test memcache
	if memcache and machine:
		cachekey = "_".join(["REPORT", db, key, machine])
		data = _cache.get(cachekey)
		if data:
			return [data, ]

	with connect() as cursor:
		if machine:
			cursor.execute("""SELECT * FROM %s
							WHERE `key` = %%s AND `name` = %%s""" % db,
							(key, machine))
		else:
			cursor.execute("""SELECT * FROM %s
							WHERE `key` = %%s""" % db, (key,))
		columns = ("key", "name", "report", "svn_rev", "timestamp")

		for row in cursor.fetchall():
			data = dict(zip(columns, row))
			data["db"] = db
			data["report"] = json.loads(zlib.decompress(data["report"]))
			rep = Report(**data)
			if memcache:
				cachekey = "_".join(["REPORT", db, key, rep.name])
				_cache.set(cachekey, rep, 3600)
			reports.append(rep)

	return reports

def connect():
	return MySQLdb.connect(host="elrond", user="releasemaster",
						passwd="releasemaster", db="mufat")

def getdays(db):
	if db.endswith(".db"):
		db = os.path.splitext(os.path.basename(db))[0]
	with connect() as cursor:
		cursor.execute("SELECT DISTINCT `key` FROM %s ORDER BY `key` DESC" % db)
		return [row[0] for row in cursor.fetchall()]

def getmachinedays(db):
	machinedict = {}

	def _add(name, date):
		if not machinedict.has_key(name):
			machinedict[name] = []
		machinedict[name].append(date)

	if db.endswith(".db"):
		db = os.path.splitext(os.path.basename(db))[0]
	with connect() as cursor:
		cursor.execute("SELECT name, `key` FROM %s ORDER BY name, `key` ASC" % db)
		for name, date in cursor.fetchall():
			_add(name, date)
	return machinedict
