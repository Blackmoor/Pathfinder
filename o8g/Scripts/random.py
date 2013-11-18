# A Replacement for the Random module that runs locally in iron python

seed = 0, 0, 0

def random():
	global seed

	x, y, z = seed
	if 0 == x == y == z:
		import time
		t = long(time.time() * 256)
		t = int((t&0xffffff) ^ (t>>24))
		t, x = divmod(t, 256)
		t, y = divmod(t, 256)
		t, z = divmod(t, 256)
		# Zero is a poor seed, so substitute 1
		seed = (x or 1, y or 1, z or 1)
		x, y, z = seed
	x = (171 * x) % 30269
	y = (172 * y) % 30307
	z = (170 * z) % 30323
	seed = x, y, z
	return (x/30269.0 + y/30307.0 + z/30323.0) % 1.0

def localShuffle(pile):
	if pile is None or len(pile) == 0: return
	i = len(pile)
	while i >= 0:
		pile[int(random()*i)].moveToBottom(pile)
		i -= 1
		
def localRandom(pile):
	if len(pile) == 0: return None
	return pile[int(random()*len(pile))]

Group.random = localRandom
#Pile.shuffle = localShuffle
