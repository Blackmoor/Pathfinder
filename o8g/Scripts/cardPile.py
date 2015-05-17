#------------------------------------------------------------
# Table based pile functions
#
# These allow cards on the table to be mapped to a pile
# We extend the Card class to make the code more readable
#------------------------------------------------------------	
remaining = ("cards", "9aef0beb-22e6-49d8-a8a0-4069d50f528e")
	
def getPile(self):
	mute()
	cardPiles = eval(getGlobalVariable("cardPiles"))
	if self._id not in cardPiles:
		return None
	pileName = cardPiles[self._id]
	for p in me.piles:
		if p == pileName:
			return me.piles[pileName]
	for p in shared.piles:
		if p == pileName:
			return shared.piles[pileName]
	return None
	
def isAPile(self):
	cardPiles = eval(getGlobalVariable("cardPiles"))
	return self._id in cardPiles
	
def linkPile(self, pile):
	mute()
	cardPiles = eval(getGlobalVariable("cardPiles"))
	if pile is None:
		if self._id in cardPiles:
			del cardPiles[self._id]
			setGlobalVariable("cardPiles", str(cardPiles))
		self.markers[remaining] = 0
	else:
		cardPiles[self._id] = pile.name
		self.markers[remaining] = len(pile)
		setGlobalVariable("cardPiles", str(cardPiles))

def updatePile(self):
	mute()
	pile = getPile(self)
	if pile is None:
		self.markers[remaining] = 0
	elif self.markers[remaining] != len(pile):
		self.markers[remaining] = len(pile)

#Event trigged by card movement - needs to be registered in your definition.xml
def cardPile(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove, highlight=None, markers=None):	
	cardPileMove(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, False, highlight, markers)

def cardScriptPile(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove, highlight=None, markers=None):	
	cardPileMove(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, True, highlight, markers)

def cardPileMove(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove, highlight=None, markers=None, faceup=None):	
	mute()
	#Get a list of cards acting as piles - order by their index (0=bottom = last in list)
	piles = sorted([ c for c in table if c.controller == me and isAPile(c) ], key=lambda c: -c.getIndex)
	
	if player == me and toGroup == table and not isScriptMove and card.pile() is None and card.Type in [ 'Boon', 'Bane', '?' ]:	
		for c in piles:
			pile = getPile(c)		
			# Check to see if this card has been moved on top of a pile card
			# If so move it to the top or bottom of the pile depending on the location of the card drop (top or bottom half of pile card)				
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
					
	# The move could affect the size of a pile we are tracking, update all pile cards we control
	for c in piles:
		pile = getPile(c)
		if c.markers[remaining] != len(pile):
			c.markers[remaining] = len(pile)

Card.pile = getPile
Card.link = linkPile
Card.refresh = updatePile