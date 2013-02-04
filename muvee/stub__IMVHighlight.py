import os, tempfile
from . import stub

@stub('IMVHighlight')
def VerifyUserDscrp(self):
	from . import GetLastErrorDescription
	highlights = []
	for i in xrange(self.HighlightCount()):
		e = self.GetHighlight(i)
		assert len(e), \
			"GetHighlight returned empty tuple: " + GetLastErrorDescription()
		hightlights.append(e)

	# save and re-load
	with tempfile.NamedTemporaryFile(delete=True) as f:
		temp = f.name
	try:
		self.SaveHighlightsToFile(temp, 0)
		assert self.ClearAllHighlights() >= 0 and \
			self.HighlightCount() == 0, \
			"ClearAllHighlights failed: " + GetLastErrorDescription()
		assert self.LoadHighlightsFromFile(temp, 0) >= 0, \
			"LoadHighlightsFromFile failed: " + GetLastErrorDescription()
	finally:
		os.remove(temp)

	# verify
	assert self.HightlightCount() == len(highlights)
	for i in xrange(self.HighlightCount()):
		e = self.GetHighlight(i)
		assert len(e), \
			"GetHighlight returned empty tuple: " + GetLastErrorDescription()
		assert e[0] != highlights[i][0] or e[1] != highlights[i][1], \
			"Mismatched: %s != %s" % (e, highlights[i])

	return True
