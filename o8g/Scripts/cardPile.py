#------------------------------------------------------------
# Table based pile functions
#
# These allow cards on the table to be mapped to a pile
# We extend the Card class to make the code more readable
#------------------------------------------------------------	
remaining = ("cards", "9aef0beb-22e6-49d8-a8a0-4069d50f528e")

def globalName(self):
	return "Pile{}".format(self._id)
	
def getPile(self):
	mute()
	pileName = getGlobalVariable(globalName(self))
	if len(pileName) == 0:
		return None
	for p in me.piles:
		if p == pileName:
			return me.piles[pileName]
	for p in shared.piles:
		if p == pileName:
			return shared.piles[pileName]
	return None
	
def isPile(self):
	return len(getGlobalVariable(globalName(self))) > 0
	
def linkPile(self, pile):
	mute()
	if pile is None:
		setGlobalVariable(globalName(self), None)
		self.markers[remaining] = 0
	else:
		setGlobalVariable(globalName(self), pile.name)
		self.markers[remaining] = len(pile)

def updatePile(self):
	mute()
	pile = getPile(self)
	if pile is None:
		self.markers[remaining] = 0
	elif self.markers[remaining] != len(pile):
		self.markers[remaining] = len(pile)

# Event trigger - need to be set up in your definition.xml
def cardPile(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove):	
	mute()
	piles = [ c for c in table if isPile(c) ]

	# Most of the time we only care if we are the player moving the card
	if player == me:
		if toGroup == table and not isScriptMove and card.pile() is None and card.Type != 'Character':	
			# Check to see if this card has been moved on top of a pile card
			# If so move it to the top or bottom of the pile depending on the location of the card drop (top or bottom half of pile card)
			for c in piles:
				pile = getPile(c)
				px, py = c.position
				if x + c.width()/2 > px and x < px + c.width()/2: # middle of card is over the pile in the x axis
					if y + c.height() >= py and y <= py: # some of the card overlaps the upper half of the pile
						notify("{} moves {} to the top of the {} pile".format(player, card, c))
						card.moveTo(pile)
						break
					elif y > py and y <= py + c.height(): # some of the card overlaps the bottom half of the pile
						notify("{} moves {} to the bottom of the {} pile".format(player, card, c))
						card.moveToBottom(pile)
						break
				
	# The move could affect the size of a pile we are tracking, update all pile cards
	for c in piles:
		c.refresh()

Card.pile = getPile
Card.link = linkPile
Card.refresh = updatePile