"""
Miscellaneous enumerators
"""

def enum(cls):
	"""
	Decorator that generates a dummy Python class with static members imported
	from MVRuntimeLib's enumerator flags. Example usage:
	
	@enum
	class SourceType:
		# imports all MV_SRC_TYPE_ENUM flags which names are prefixed with "SRC_TYPE_"
		_src = MV_SRC_TYPE_ENUM
		_prefix = 'SRC_TYPE_'
	"""

	for name in filter(lambda n: n.startswith(cls._prefix), dir(cls._src)):
		setattr(cls, name.replace(cls._prefix, ''), getattr(cls._src, name))
	return cls

#==== Start definitions ====

from MVRuntimeLib import *

@enum
class SourceType:
	# imports all MV_SRC_TYPE_ENUM flags which names are prefixed with "SRC_TYPE_"
	_src = MV_SRC_TYPE_ENUM
	_prefix = 'SRC_TYPE_'

@enum
class InitFlags:
	_src = MV_INIT_ENUM
	_prefix = 'INIT_'

@enum
class LoadFlags:
	_src = MV_LOAD_FLAGS
	_prefix = 'LOAD_'

@enum
class MakeFlags:
	_src = MV_MAKE_ENUM
	_prefix = 'MAKE_'

@enum
class TimelineType:
	_src = MV_TL_TYPE_ENUM
	_prefix = 'TL_TYPE_'

@enum
class ArType:
	_src = MV_AR_TYPE_ENUM
	_prefix = 'AR_TYPE'
