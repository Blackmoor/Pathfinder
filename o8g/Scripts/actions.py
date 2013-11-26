d4 = ("d4", "72fdca01-ff61-4dd2-a6b8-43f567f90ff7")
d6 = ("d6", "1f1a643b-2aea-48b2-91c8-96f0dffaad48")
d8 = ("d8", "4165d32c-7b07-4040-8e57-860a95a0dc69")
d10 = ("d10", "3b7cbb3a-4f52-4445-a4a5-65d5dfd9fa23")
d12 = ("d12", "53d1f6b4-03f6-4b8b-8065-d0759309e00d")
plus = ("+", "1b08a785-f745-4c93-b0f1-cdd64c89d95d")
minus = ("-", "b442c012-023f-42d1-9d28-e85168a4401a")

BoardWidth = 700
BoardHeight = 300
StoryY = -BoardHeight/2
LocationY = StoryY + 200

showDebug = False #Can be changed to turn on debug

#HACK
#This function replaces update() which is not quite working as expected in the current release of OCTGN
def sync():
	i = rnd(0,1)
	
#------------------------------------------------------------
# Utility functions
#------------------------------------------------------------

def debug(str):
	if showDebug:
		whisper(str)
		
def toggleDebug(group, x=0, y=0):
	global showDebug
	showDebug = not showDebug
	if showDebug:
		notify("{} turns on debug".format(me))
	else:
		notify("{} turns off debug".format(me))

def shuffle(pile, synchronise=False):
	mute()
	if pile is None or len(pile) == 0: return
	pile.shuffle()
	if synchronise:
		sync()
	notify("{} shuffles '{}'".format(me, pile.name))

def cardType(card):
	if card.Subtype2 is not None and len(card.Subtype2) > 0 and card.Subtype2 != 'Front' and card.Subtype2 != 'Back':
		return card.Subtype2
	elif card.Subtype is not None:
		return card.Subtype
	return None
	
#Return the default x coordinate of the players hero
#We Leave space for 4 piles (Adventure Path, Adventure, Scenario, Blessings) then place the characters
def PlayerX(player):
	room = int(BoardWidth / (len(getPlayers()) + 4))
	return  room*(player+4) - room/2 - 32 - BoardWidth/2

def LocationX(i):
	room = int(BoardWidth / (len(getPlayers())+2))	#2 more locations than players
	return room*i - room/2 - 32 - BoardWidth/2
	
def num(s):
   if not s: return 0
   try:
      return int(s)
   except ValueError:
      return 0

#Check see if a card at x1,y1 overlaps a card at x2,y2
#Both have size w, h	
def overlaps(x1, y1, x2, y2, w, h):
	#Four checks, one for each corner
	if x1 >= x2 and x1 <= x2 + w and y1 >= y2 and y1 <= y2 + h: return True
	if x1 + w >= x2 and x1 <= x2 and y1 >= y2 and y1 <= y2 + h: return True
	if x1 >= x2 and x1 <= x2 + w and y1 + h >= y2 and y1 <= y2: return True
	if x1 + w >= x2 and x1 <= x2 and y1 + h >= y2 and y1 <= y2: return True
	return False
	
def cardHere(x, y, checkOverlap=True, group=table):
	cw = 0
	ch = 0
	for c in group:
		cx, cy = c.position
		if checkOverlap:
			cw = c.width()
			ch = c.height()
		if overlaps(x, y, cx, cy, cw, ch):
			return c
	return None

def cardX(card):
	x, y = card.position
	return x
	
def cardY(card):
	x, y = card.position
	return y

def clearTargets(group=table, x=0, y=0):
	for c in group:
		if c.controller == me or (c.targetedBy is not None and c.targetedBy == me):
			c.target(False)

def findCard(group, model):
	for c in group:
		if c.model == model:
			return c
	return None

#Work out which of the shared piles a card comes from based on its type/subtype
def comesFrom(card):
	if card is None:
		return None
	if card.Type is not None and card.Type in shared.piles:
		return shared.piles[card.Type]
	if card.Subtype is not None and card.Subtype in shared.piles:
		return shared.piles[card.Subtype]
	return None
	
def returnToBox(card):
	locked = False
	if card.Type == '?': # Not visible
		locked = lockPile(shared.piles['Internal'])
		if not locked: return
		group = card.group
		if group == table:
			x, y = card.position
		card.moveTo(shared.piles['Internal']) # Ensures the card properties are visible
	
	dest = comesFrom(card)		
	if dest is None: # Don't know where to put it
		notify("{} Fails to find place for '{}' in the box".format(me, card))
		if locked: # We moved it, so return it to where it started
			if group == table:
				card.moveToTable(x, y)
			else:
				card.moveTo(group)
	else: # Move to the correct pile - aiming to keep in alphabetical order
		index = 0
		for c in dest:
			if c.name >= card.name:
				break
			index += 1
		card.moveTo(dest, index)
	
	if locked:
		unlockPile(shared.piles['Internal'])

def isOpen(card):
	if card is None or card.Type != 'Location':
		return False
	return (card.orientation == Rot0 and card.alternate != "B")
	
#Any card loaded into the player area must be removed from the box and put into the "InUse" pile
#Find an exact match based on the card model, if none look for a name match
def inUse(card):
	mute()
	if card.Subtype in shared.piles:
		found = findCard(shared.piles[card.Subtype], card.model)
		if found is None:
			found = findCardByName(shared.piles[card.Subtype], card.name)
		if found is not None:
			found.moveTo(shared.piles['InUse'])
		else:
			notify("{} is using '{}' which is not in the box".format(me, card))

def rollDice(card): #Roll the dice based on the number of tokens
	mute()
	roll = 0
	dice=""
	for die in [ d12, d10, d8, d6, d4 ]:
		count = card.markers[die]
		if count > 0:
			dice = "{} + {}{}".format(dice, count, die[0])
			while count > 0:
				roll += 1 + int(random() * num(die[0][1:]))
				#roll += rnd(1, num(die[0][1:]))
				count -= 1
			card.markers[die] = 0
	
	if card.markers[plus] > 0:
		roll += card.markers[plus]
		dice = "{} + {}".format(dice, card.markers[plus])
		card.markers[plus] = 0
	if card.markers[minus] > 0:
		roll -= card.markers[minus]
		dice = "{} - {}".format(dice, card.markers[minus])
		card.markers[minus] = 0
	
	if len(dice) > 0:
		playSound("dice")
		notify("{} rolls {} and gets {}".format(me, dice[3:], roll))
		return True
	
	return False

def findCardByName(group, name):
	debug("Looking for '{}' in '{}'".format(name, group.name))
	for card in group:
		if card.name == name:
			return card
	return None
		
def d12Add(card, x=0, y=0):
	addToken(card, d12)

def d12Sub(card, x=0, y=0):
	subToken(card, d12)
	
def d10Add(card, x=0, y=0):
	addToken(card, d10)

def d10Sub(card, x=0, y=0):
	subToken(card, d10)	
	
def d8Add(card, x=0, y=0):
	addToken(card, d8)

def d8Sub(card, x=0, y=0):
	subToken(card, d8)	
	
def d6Add(card, x=0, y=0):
	addToken(card, d6)

def d6Sub(card, x=0, y=0):
	subToken(card, d6)	
	
def d4Add(card, x=0, y=0):
	addToken(card, d4)

def d4Sub(card, x=0, y=0):
	subToken(card, d4)	

def plusThree(card, x=0, y=0):
	plusOne(card, x, y)
	plusOne(card, x, y)
	plusOne(card, x, y)

def plusTwo(card, x=0, y=0):
	plusOne(card, x, y)
	plusOne(card, x, y)
	
def minusThree(card, x=0, y=0):
	minusOne(card, x, y)
	minusOne(card, x, y)
	minusOne(card, x, y)

def minusTwo(card, x=0, y=0):
	minusOne(card, x, y)
	minusOne(card, x, y)
	
def plusOne(card, x=0, y=0):
	if card.markers[minus] > 0:
		subToken(card, minus)
	else:
		addToken(card, plus)

def minusOne(card, x=0, y=0):
	if card.markers[plus] > 0:
		subToken(card, plus)
	else:
		addToken(card, minus)

# Find the pile under this card
def overPile(card):
	debug("Checking to see if '{}' is over a pile".format(card))
	piles = [ c for c in table if c.pile() is not None ]
	x, y = card.position
	return cardHere(x, y, True, piles)
	
def closeLocation(card, perm):
	mute()
	if card.Type != 'Location':
		notify("This is not a location ...")
		return False
	if perm:
		# Move cards from location pile back to box
		# If we find the Villain then the location is not closed and the Villain is displayed
		# We need to use a pile with full visibility to access the card type
		pile = card.pile()
		visible = shared.piles['Internal']
		if not lockPile(visible): return
		
		debug("Cleaning up pile '{}'".format(pile.name))
		for c in pile:
			c.moveTo(visible)

		for c in visible:
			debug("Unexplored ... '{}'".format(c))
			if c.Subtype == 'Villain':
				c.moveTo(pile)
			else:
				returnToBox(c)
		
		unlockPile(visible)
		
		if len(pile) > 0: # Villain was left in the pile
			notify("You find a Villain while attempting to close this location")
			card.orientation = Rot90
			return False
			
		flipCard(card)
		notify("{} Permanently closes '{}'".format(me, card))
		return True
	else:
		card.orientation = Rot90
		notify("{} temporarily closes '{}'".format(me, card))
		return True
		
def clearupGame(cleanupStory=False):
	for card in table:
		#Remove the pile link on cards leaving the table
		if card.pile() is not None:
			card.link(None)
			
		if card.Type == 'Character':
			if card.Subtype == 'Token':
				card.moveTo(card.owner.hand)
			else:
				card.switchTo() # Display side A of the card as it shows the deck makeup
		elif cleanupStory or card.Type != 'Story':
			returnToBox(card)

	for i in range(8): # Loop through 8 location decks
		for card in shared.piles["Location{}".format(i+1)]:
			returnToBox(card)

	for pile in [ 'Blessing Deck', 'Blessing Discard' ]:
		for card in shared.piles[pile]:
			returnToBox(card)
			
#------------------------------------------------------------
# Global variable manipulations function
#------------------------------------------------------------	

# A Global variable is created for each location pile named after the location
# No functional interface is supplied for this however personal globals needed for reconnect are

def storeHandSize(h):
	me.setGlobalVariable('HandSize', str(h))

def getHandSize():
	return num(me.getGlobalVariable('HandSize'))
	
def storeFavoured(f):
	me.setGlobalVariable('Favoured', f)

def getFavoured():
	return me.getGlobalVariable('Favoured')

def lockInfo(pile):
	if pile is None: return (None, 0)
	lock = getGlobalVariable(pile.name)
	if len(lock) == 0:
		return (None, 0)
	info = lock.split()
	return (info[0], num(info[1]))
	
def lockPile(pile):
	mute()
	if pile is None: return False
	# Attempt to lock the shared pile
	# Write the player name and count into a global named after the pile
	who, count = lockInfo(pile)
	if who != None and who != me.name:
		whisper("{} has temporarily locked the game - please try again".format(who))
		return False

	setGlobalVariable(pile.name, "{} {}".format(me.name, count+1))
	return True

def unlockPile(pile):
	mute()
	if pile is None: return False
	who, count = lockInfo(pile)
	if who is None:
		debug("{} tries to unlock pile '{}' - not locked".format(me, pile.name))
		return False
	if who != me.name:
		debug("{} tries to unlock pile '{}' - locked by {}".format(me, pile.name, info[0]))
		return False
	if count <= 1:
		setGlobalVariable(pile.name, None)
	else:
		setGlobalVariable(pile.name, "{} {}".format(me.name, count-1))
	return True
	
#---------------------------------------------------------------------------
# Call outs
#---------------------------------------------------------------------------

def deckLoaded(player, groups):
	mute()

	if player != me:
		return
		
	isShared = False	
	for p in groups:
		if p.name in shared.piles:
			isShared = True
	
	if isShared:
		for p in groups:
			if p.controller != me:
				p.setController(me)
	else: # Player deck loaded
		playerSetup()
	
def startOfTurn(player, turn):
	mute()
	# Pass control of the shared decks and current Blessing card
	debug("Start of Turn for player {}".format(player))
	wasMyTurn = False
	for card in table: #Re-open any temporarily closed locations
		if card.orientation != Rot0 and card.controller == me:
			card.orientation = Rot0	
	
	#The shared piles should be controlled by the last player
	#Some may have been taken control of manually so determine the last player as
	#the player controlling the majority of the shared piles
	counts = {}
	for name in shared.piles:
		if shared.piles[name].controller in counts:
			counts[shared.piles[name].controller] += 1
		else:
			counts[shared.piles[name].controller] = 1
		if shared.piles[name].controller == me and player != me: # Hand over control to the new player
			shared.piles[name].setController(player)
	
	lastPlayer = None
	for p in counts:
		if lastPlayer is None or counts[p] > counts[lastPlayer]:
			lastPlayer = p
	if lastPlayer == me:
		drawUp(me.hand)
	
	#Pass control of the cards on the table - skip the current blessing as this causes timing issues
	blessing = None
	handover = [ c for c in table if c.Type != 'Character' ]
	for card in handover:
		if card.controller == me and player != me and (card.pile() is None or card.pile() != shared.piles['Blessing Deck']):
			card.setController(player)
	
	#Advance the Blessing deck if we are the new player
	if player == me:
		advanceBlessingDeck()
		#Highlight my avatar
		for c in table:
			if c.Type == 'Character' and c.Subtype == 'Token':
				if c.owner == me:
					c.sendToFront()
					c.highlight = "#82FA58" # Green
				else:
					c.highlight = None
					
def deleteCard(card):
	mute()
	card.link(None)
	debug("{} Trying to delete {} owned by {}".format(me, card, card.controller))
	card.delete()
	
#
#Card Move Event
# We only care if we have just moved our avatar from hand to the table
# or if the blessing discard pile changes
#
def checkMovement(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove):	
	if me.isActivePlayer: # The active player is allowed to update the blessing discard pile card
		bd = shared.piles['Blessing Discard']
		x = PlayerX(0)
		y = StoryY
		deleted = False
		if fromGroup == bd or toGroup == bd: # The blessing discard pile changed - we must update the current blessing card
			for c in table:
				if c.pile() == shared.piles['Blessing Deck'] and ((len(bd) > 0 and c.model != bd.top().model) or len(bd) == 0):
					x, y = c.position
					if c.controller != me:
						remoteCall(c.controller, "deleteCard", [c])
					else:
						deleteCard(c)
					deleted = True
					
		found = False
		if not deleted: # check to see if the blessing card is on the table
			for c in table:
				if c.pile() == shared.piles['Blessing Deck']:
					found = True
					break
		# Create a copy of the top card
		if len(bd) > 0 and not found:
			table.create(bd.top().model, x, y).link(shared.piles['Blessing Deck'])

	if player != me:
		return
		
	if card.Type == 'Character' and card.Subtype == 'Token' and fromGroup == me.hand and toGroup == table:
		mute()
		# If the scenario hasn't been set up yet return the avatar to hand and issue a warning
		if len(shared.piles['Blessing Deck']) == 0:
			whisper("Ensure the scenario is set up before placing {} at your starting location".format(card))
			card.moveTo(fromGroup)
			return
		
		#Ensure side B of the character card is face up
		for c in table:
			if c.owner == me and c.Type == 'Character' and c != card:
				c.switchTo('B')

		debug("{} is ready".format(me))
		#Move all player card (Boons) to Discarded pile - then shuffle ready for dealing
		for pile in [ me.hand, me.Buried, me.deck ]:
			for c in pile:
				if c.Type == 'Character':
					c.moveTo(me.hand)
				elif c.Type == 'Feat':
					c.moveTo(me.Buried)
				else:
					c.moveTo(me.Discarded)
		shuffle(me.Discarded, True)
		size = len(me.Discarded)
		favoured = getFavoured()
		handSize = getHandSize()
		ci = 0
		for card in me.Discarded:
			if card.Subtype == favoured: break
			ci += 1
			
		if ci >= size:
			ci = 0
			notify("{} has an invalid deck - no favoured cards ({})".format(me, favoured))
		
		if ci > 0: #Move the top cards to deck so that the favoured card is at the top of the Discarded pile
			for card in me.Discarded.top(ci):
				card.moveToBottom(me.Discarded)

		for c in me.Discarded.top(handSize):
			c.moveTo(me.hand)
		#Move the rest of the cards into the deck and re-shuffle
		for card in me.Discarded:
			card.moveTo(me.deck)
		
		#The first player to drag to the table becomes the active player
		if len(shared.piles['Blessing Deck']) == 30:
			#Check to see who the active player is
			active = None
			for p in getPlayers():
				if p.isActivePlayer:
					active = p
					break
			if active is None: # At the start of a game no one is active but anyone can set the active player
				me.setActivePlayer()
			else:
				remoteCall(active, "makeActive", [me])

def makeActive(who):
	if who != me:
		debug("{} passes control to {}".format(me, who))
	who.setActivePlayer()

#---------------------------------------------------------------------------
# Table group actions
#---------------------------------------------------------------------------
		
#Table action - prompts the player to pick an adventure path, an adventure and a scenario
#If there is already a scenario on the table clear it away
def pickScenario(group=table, x=0, y=0):
	mute()
	story = [ card for card in group if card.Type == 'Story' ]
	if len(story) > 0:
		if not confirm("Clear the current game?"):
			return
		clearupGame(True)
						
	#Pick the new Scenario
	paths = [ card.name for card in shared.piles['Story'] if card.Subtype == 'Adventure Path' ]
	if len(paths) > 0:
		paths.append("None")
		choice = askChoice("Choose Adventure Path", paths)
	else:
		choice = 0
	if choice <= 0 or paths[choice-1] == 'None': # Not using an adventure path
		adventures = [ card.name for card in shared.piles['Story'] if card.Subtype == 'Adventure' ]
		adventures.append("None")
	else:
		path = findCardByName(shared.piles['Story'], paths[choice-1])
		path.moveToTable(PlayerX(-3),StoryY)
		flipCard(path)
		loaded = [ card.name for card in shared.piles['Story'] if card.Subtype == 'Adventure' ]
		adventures = []
		for o in path.Attr1.splitlines(): # Build up a list of options that have been loaded and in the order given
			if o in loaded:
				adventures.append(o)
	if len(adventures) < 2:
		choice = len(adventures)
	else:
		choice = askChoice("Choose Adventure", adventures)
	if choice <= 0 or adventures[choice-1] == 'None': # Not using an adventure card
		scenarios = [ card.name for card in shared.piles['Story'] if card.Subtype == 'Scenario' ]
	else:
		adventure = findCardByName(shared.piles['Story'], adventures[choice-1])
		adventure.moveToTable(PlayerX(-2), StoryY)
		flipCard(adventure)
		loaded = [ card.name for card in shared.piles['Story'] if card.Subtype == 'Scenario' ]
		scenarios = []
		for o in adventure.Attr1.splitlines(): # Build up a list of options that have been loaded and in the order given
			if o in loaded:
				scenarios.append(o)
	if len(scenarios) < 2:
		choice = len(scenarios)
	else:
		choice = askChoice("Choose Scenario", scenarios)
	if choice > 0:
		scenario = findCardByName(shared.piles['Story'], scenarios[choice-1])
		scenario.moveToTable(PlayerX(-1),StoryY)
		scenarioSetup(scenario)

def randomHiddenCard(group=table, x=0, y=0):
	pile = cardTypePile()
	if pile is None: return
	randomCardN(pile, x, y, 1, True)
	
def randomCard(group=table, x=0, y=0):
	pile = cardTypePile()
	if pile is None: return
	randomCardN(pile, x, y, 1)

def randomCards(group=table, x=0, y=0):
	pile = cardTypePile()
	if pile is None: return
	quantity = [ "One", "Two", "Three", "Four", "Five", "Six" ]
	choice = askChoice("How many?", quantity)
	randomCardN(pile, x, y, choice)

def randomCardN(pile, x, y, n, hide=False):
	while n > 0 and len(pile) > 0:
		card = pile.random()
		card.setController(me)
		if y < 0:
			card.moveToTable(x, y, hide or n > 1)
		else:
			card.moveToTable(x, y-card.height(), hide or n > 1)
		x = x + 10
		n -= 1

def cardTypePile():
	mute()
	types = ["Henchman", "Monster", "Barrier", "Armor", "Weapon", "Spell", "Item", "Ally", "Blessing"]
	choice = askChoice("Pick card type", types)
	if choice <= 0:
		return None
	return shared.piles[types[choice-1]]

#---------------------------------------------------------------------------
# Table card actions
#---------------------------------------------------------------------------

def exploreLocation(card, x=0, y=0):
	mute()
	if card.type != 'Location':
		whisper("This is not a location ....")
		return
	notify("{} explores '{}'".format(me, card))
	pile = card.pile()
	if pile is None:
		whisper("Nothing to see here")
		return
	if len(pile) == 0:
		whisper("Location is fully explored")
		return
	x, y = card.position
	pile.top().moveToTable(x, y+14)
	
def defaultAction(card, x = 0, y = 0):
	mute()

	if rollDice(card): # If it has dice on - roll them
		return
	if card.pile() is not None:
		if card.Type == 'Location': # Explore location
			if len(card.pile()) > 0:
				exploreLocation(card)
			else:
				closePermanently(card)
		elif card.pile() == shared.piles['Blessing Deck']: # Reveal the next blessing
			advanceBlessingDeck()
	elif card.Subtype == 'Villain':
		hideVillain(card)
	elif card.Type == 'Bane': # Assume it is undefeated and shuffle back into location
		shuffleCard(card)
	elif card.type == 'Boon': # Assume it is acquired
		acquireCard(card)
	else:
		flipCard(card, x, y)
                                
def flipCard(card, x = 0, y = 0):
	mute()
	if card.Subtype == 'Token': return
	
	if card.alternates is not None and "B" in card.alternates:
		if card.alternate == "B":
			card.switchTo("")
		else:
			card.switchTo("B")
		debug("{} flips '{}'".format(me, card))
	elif card.isFaceUp:
		card.isFaceUp = False
		debug("{} turns '{}' face down.".format(me, card))        
	else:
		card.isFaceUp = True
		debug("{} turns '{}' face up.".format(me, card))   

def addToken(card, tokenType):
	mute()
	card.markers[tokenType] += 1

def subToken(card, tokenType):
    mute()
    card.markers[tokenType] -= 1

def revealCard(card, x=0, y=0):
	mute()
	notify("{} reveals '{}'".format(me, card))
	
def rechargeCard(card, x=0, y=0):
	mute()
	notify("{} recharges '{}'".format(me, card))
	sync()
	card.moveToBottom(me.deck)
	
def displayCard(card, x=0, y=0):
	mute()
	notify("{} displays '{}'".format(me, card))

def acquireCard(card, x=0, y=0):
	mute()
	card.moveTo(me.hand)
	notify("{} acquires '{}'".format(me, card))
	
def banishCard(card, x=0, y=0): #Move to correct pile in box (shared)
	mute()
	if card.pile() == shared.piles['Blessing Deck']:
		if confirm("Are you sure?") != True: # This is unusual
			return
		card = shared.piles['Blessing Discard'].top()
	notify("{} banishes '{}'".format(me, card))
	returnToBox(card)
		
def buryCard(card, x=0, y=0): #Move to bury pile
	mute()
	notify("{} buries '{}'".format(me, card))
	card.moveTo(me.Buried)
	
def discardCard(card, x=0, y=0): #Move to discard pile
	mute()
	notify("{} discards '{}'".format(me, card))
	card.moveTo(me.Discarded)
	
def removeCard(card, x=0, y=0):
	mute()
	notify("{} removes '{}' from play".format(me, card))
	sync()
	card.delete()

def shuffleCard(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None: # This is a normal card - if it is over a pile we shuffle it into the pile
		c = overPile(card)
		if c is None: return
		pile = c.pile()
		notify("{} moves '{}' into '{}' deck".format(me, card, pile.name))
		sync()
		card.moveTo(pile)
	shuffle(pile)
	
def peekTop(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None or len(pile) == 0: return
	notify("{} looks at the top card of the '{}' deck".format(me, card))
	sync()
	src = pile.top()
	#Move the top card to a pile with full visibility
	if lockPile(shared.piles['Internal']):
		src.moveTo(shared.piles['Internal'])
		whisper("{} looks at '{}'".format(me, src))
		src.moveTo(pile)
		unlockPile(shared.piles['Internal'])

def peekTop2(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None: return
	notify("{} looks at the top 2 cards of the '{}' deck".format(me, card))
	sync()
	if lockPile(shared.piles['Internal']):
		for i in range(2):
			#Move the card to a pile with full visibility
			src = pile[i]
			src.moveTo(shared.piles['Internal'])
			whisper("{} looks at '{}'".format(me, src))
			src.moveTo(pile, i)
		unlockPile(shared.piles['Internal'])
		
def peekBottom(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None: return
	notify("{} looks at the bottom card of the '{}' deck".format(me, card))
	sync()
	src = pile.bottom()
	#Move the top card to a pile with full visibility
	if lockPile(shared.piles['Internal']):
		src.moveTo(shared.piles['Internal'])
		whisper("{} looks at '{}'".format(me, src))
		src.moveToBottom(pile)
		unlockPile(shared.piles['Internal'])

def pileMoveTB(card, x=0, y=0):
	mute()
	#Move the top card to the bottom
	pile = card.pile()
	if pile is None or len(pile) == 0: return
	notify("{} moves the top card of the '{}' pile to the bottom".format(me, card))
	c = pile.top()
	c.moveToBottom(pile)

def pileMoveBT(card, x=0, y=0):
	mute()
	#Move the bottom card to the top
	pile = card.pile()
	if pile is None or len(pile) == 0: return
	notify("{} moves the bottom card of the '{}' pile to the top".format(me, card))
	pile.bottom().moveTo(pile)
	
def pileSwap12(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None or len(pile) < 2: return
	notify("{} swaps to the top 2 cards of the '{}' pile".format(me, card))
	pile[1].moveTo(pile)
	
def closePermanently(card, x=0, y=0):
	closeLocation(card, True)
	#If there are no open locations the players have won
	open = [ card for card in table if isOpen(card) ]
	if len(open) == 0:
		gameOver()
		notify("You have won ..... claim your reward")		

def closeTemporarily(card, x=0, y=0):
	closeLocation(card, False)
	
def hideVillain(villain, x=0, y=0):
	mute()
	if villain.Subtype != 'Villain':
		notify("This is not a Villain ...")
		return
	
	defeated = confirm("Did you defeat the villain?")
	if defeated is None:
		return
		
	blessing = shared.piles['Blessing'] if defeated else shared.piles['Blessing Deck']		
	location = overPile(villain) #Determine the location of the Villain (based on the if it is over a pile on the table)
	if defeated: # We get to close the location
		if location is None or location.Type != 'Location': # Not sure which location to close
			if not confirm("Did you close the location?"):
				whisper("Close the location manually, then hide the villain")
				return
		elif isOpen(location): # Ensure location is closed
			closePermanently(location)
			
	open = [ card for card in table if isOpen(card) ]
	if len(open) == 0:
		return
	
	hidden = shared.piles['Internal']
	if not lockPile(hidden):
		return
	
	debug("Villain has {} open locations".format(len(open)))	
	villain.moveTo(hidden)
	#Add a Blessing for each other open location
	for i in range(len(open)-1):
		card = blessing.random()
		if card is not None:
			card.moveTo(hidden)

	for loc in open:
		pile = loc.pile()
		card = hidden.random()
		if card is not None:			
			card.moveTo(pile)
		shuffle(pile)
	
	# Re-open temporarily closed locations
	for card in table:
		if card.Type == 'Location' and card.orientation != Rot0:
			card.orientation = Rot0
	update()	
	unlockPile(hidden)
	
#---------------------------------------------------------------------------
# Pile Group Actions
#---------------------------------------------------------------------------
	
def rechargeRandom(group, x=0, y=0): # Discarded pile
	mute()
	if len(group) == 0: return
	card = group.random()
	notify("{} recharges '{}'".format(me, card))
	sync()
	card.moveToBottom(me.deck)
	
def returnToBlessingDeck(group, x=0, y=0): # Blessing Discard
	mute()
	if len(group) == 0:
		notify("No cards to return")
		return
	destination = shared.piles['Blessing Deck']
	group.random().moveToBottom(destination)
	notify("{} returns a card to the Blessing Deck".format(me))

def revealRandom(group, x=0, y=0): # Most shared piles use this
	if len(group) == 0: return
	group.random().moveToTable(x, y)
	
def shufflePile(group, x=0, y=0): # Location piles use this
	mute()
	if len(group) == 0: return
	shuffle(group)
	
#---------------------------------------------------------------------------
# Hand Group Actions
#---------------------------------------------------------------------------

def drawUp(group): # group == me.hand
	if len(me.deck) == 0: return
	handSize = getHandSize()
	if len(group) > handSize:
		notify("{} already has too many cards ({}), max {}".format(me, len(group), handSize))
		return
	
	toDraw = handSize - len(group)
	for c in me.deck.top(toDraw):
		c.moveTo(group)
	
	if len(group) < handSize: #We ran out of cards ... and died
		notify("{} has run out of cards".format(me))
	elif toDraw > 0:
		notify("{} draws {} cards".format(me, toDraw))

#---------------------------------------------------------------------------
# Deck Group Actions
#---------------------------------------------------------------------------
def shuffleDeck(group, x=0, y=0): # me.deck
	mute()
	shuffle(group, True)

def drawCard(group, x=0, y=0): # me.deck
	mute()
	card = group.top()
	if card is None:
		return
	notify("{} draws '{}'".format(me, card))
	card.moveTo(me.hand)
	
#---------------------------------------------------------------------------
# Game logic and set up
#---------------------------------------------------------------------------
def playerSetup():
	id = me._id
	debug("Player {}: Setup ....".format(id))
	#Remove all the player cards from the box area (into the InUse area)
	for card in me.Discarded:
		inUse(card)
	
	handSize = 4
	favoured = 'Your choice'
	#Move Character Card to the table
	for card in me.hand:
		if card.Type == 'Character':
			if card.Subtype != 'Token': # Extract information about the hand size and favoured card type
				if len(card.Attr3) > 0:
					favoured = card.Attr3
					debug("Favoured = {}".format(favoured))	
				card.moveToTable(PlayerX(id), StoryY)
				update()
				flipCard(card)
				if len(card.Attr3) > 0:
					handSize = num(card.Attr3[0])
					debug("Hand Size = {}".format(handSize))
				notify("{} places {} on the table".format(me, card))
		else:
			whisper("Unexpected card '{}' loaded into hand".format(card))
	
	#Process feats - these override default values extracted from basic character sheet
	debug("Processing feats ....")
	for card in me.Buried:
		if card.name[:9] == "Hand Size":
			handSize = num(card.name[10:])
			debug("HandSize override - {}".format(handSize))			
		elif card.subtype == 'Favoured':
			favoured = card.name
			debug("Favoured override - {}".format(favoured))
			
	if favoured == 'Your choice':
		#Make a list of card types in the deck
		choices = []
		for card in me.Discarded:
			type = cardType(card)		
			if type is not None and type not in choices:
				choices.append(type)
		#Prompt user to select favoured card type
		choice = None
		if len(choices) > 0:
			while choice == None or choice == 0:
				choice = askChoice("Favoured Card Type", choices)
			favoured = choices[choice-1]
	
	storeHandSize(handSize)
	storeFavoured(favoured)
	debug("HandSize {}, Favoured type {}".format(handSize, favoured))
	whisper("Drag avatar to your starting location once the scenario is set up")
	
#Set up the scenario
#Move each location to the table and create its deck
#Create the Blessing deck and reveal the top card
def scenarioSetup(card):
	mute()
	hidden = shared.piles['Internal']
	if not lockPile(hidden): return
				
	locations = card.Attr1.splitlines()
	for i in range(len(getPlayers())+2):
		debug("Processing Location '{}'".format(locations[i]))
		pileName = "Location{}".format(i+1)
		setGlobalVariable(locations[i], pileName)
		location = findCardByName(shared.piles['Location'], locations[i])
		if location is not None:
			locPile = shared.piles[pileName]
			debug("Moving '{}' to table ...".format(location))
			location.moveToTable(LocationX(i+1), LocationY)
			#Create deck based on location distribution
			deck = location.Attr1.splitlines()
			for entry in deck:
				details = entry.split(' ') # i.e. Monster 3
				if len(details) == 2 and details[0] in shared.piles:
					debug("Adding {} cards of type {}".format(details[1], details[0]))
					pile = shared.piles[details[0]]
					for count in range(num(details[1])):
						pile.random().moveTo(locPile)
				else:
					whisper("Location error: Failed to parse [{}]".format(details[0]))
			location.link(locPile)
			
	#Put the Villain and henchmen in a new pile, then shuffle and deal out to the locations
	flipCard(card) # Villain info is on Side B
	if len(card.Attr2) > 0 and card.Attr2 != 'None':
		villain = findCardByName(shared.piles['Villain'], card.Attr2)
		if villain is None:
			whisper("Setup error: failed to find '{}'".format(card.Attr2))
		else:
			debug("Moving '{}' to hidden pile".format(villain))
			villain.moveTo(hidden)
	henchmen = card.Attr3.splitlines()
	debug("Hide Henchmen '{}'".format(card.Attr3))
	index = 0
	while len(hidden) < len(getPlayers()) + 2:
		if henchmen[index] in shared.piles: # A card type has been supplied
			man = shared.piles[henchmen[index]].random()
		else:
			man = findCardByName(shared.piles['Henchman'], henchmen[index])
			if man is None and henchmen[index][-1] == 's': # The last henchman entry might be pluralised - remove the trailing "s"
				man = findCardByName(shared.piles['Henchman'], henchmen[index][:-1])
		if man is None:
			whisper("Setup error: failed to find '{}'".format(henchmen[index]))
			if index == len(henchmen) - 1: # Stop a possible infinite loop if the final bandit is not loaded
				break;
		else:
			man.moveTo(hidden)
		if index < len(henchmen) - 1: #Repeat the last named entry if there are not enough named unique henchmen
			index += 1

	debug("Deal from hidden deck ...")
	#Now deal them to each location pile
	index = 0
	while len(hidden) > 0:
		pile = shared.piles["Location{}".format(index+1)]
		hidden.random().moveTo(pile)
		shuffle(pile)
		index += 1
	update()
	
	#Create the Blessing deck
	src = shared.piles['Blessing']
	dst = shared.piles['Blessing Deck']
	while len(src) > 0 and len(dst) < 30:
		src.random().moveTo(dst)		
	
	unlockPile(hidden)
	notify("{} starts the scenario '{}'".format(me, card.name))

def advanceBlessingDeck():
	#Move the top card of the Blessing deck to the discard pile	
	pile = shared.piles['Blessing Deck']	
	if len(pile) == 0:
		# Out of time - the players have lost
		gameOver()
		notify("You have failed to complete the scenario in time")		
	else:
		shared.piles['Blessing Deck'].top().moveTo(shared.piles['Blessing Discard'])
		notify("{} advances the Blessing Deck".format(me))
			
def gameOver():
	clearupGame()
	for p in getPlayers():
		remoteCall(p, "displayHand", [me])	
		
#Move all my cards back into my hand ordered by type
def displayHand(who):
	debug("Display hand")
	for pile in [ me.hand, me.Buried, me.deck ]:
		for c in pile:
			if c.Type == 'Feat':
				c.moveTo(me.Buried)
			else:
				c.moveTo(me.Discarded)
				
	#Now order the cards - in turn move cards of the given type to the hand
	for type in ["Token","Weapon","Spell","Item","Armor","Ally","Blessing"]:
		for c in me.Discarded:
			if cardType(c) == type:
				c.moveTo(me.hand)