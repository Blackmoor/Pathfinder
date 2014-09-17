d4 = ("d4", "72fdca01-ff61-4dd2-a6b8-43f567f90ff7")
d6 = ("d6", "1f1a643b-2aea-48b2-91c8-96f0dffaad48")
d8 = ("d8", "4165d32c-7b07-4040-8e57-860a95a0dc69")
d10 = ("d10", "3b7cbb3a-4f52-4445-a4a5-65d5dfd9fa23")
d12 = ("d12", "53d1f6b4-03f6-4b8b-8065-d0759309e00d")
plus = ("+", "1b08a785-f745-4c93-b0f1-cdd64c89d95d")
minus = ("-", "b442c012-023f-42d1-9d28-e85168a4401a")
timer = ("Timer", "d59b44ba-cddf-49f9-88f5-1176a305f3d3")

BoardWidth = 700
BoardHeight = 300
StoryY = -BoardHeight/2
LocationY = StoryY + 190

showDebug = False #Can be changed to turn on debug

#This function replaces update() which does not wait for async fns like shuffle to complete
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
	
#Return the default x coordinate of the players hero
#We Leave space for 5 piles (Adventure Path, Adventure, Scenario, Ship, Blessings) then place the characters
def PlayerX(player):
	room = int(BoardWidth / (len(getPlayers()) + 5))
	return  room*(player+5) - room/2 - 32 - BoardWidth/2

def LocationX(i, nl):
	room = int(BoardWidth / nl)
	return room*i - room/2 - 32 - BoardWidth/2
	
def numLocations(): #2 more locations than players but modified by the extra locations counter in the shared tab
	n = len(getPlayers())+2+shared.ExtraLocations
	if n < 1:
		return 1
	if n > 8:
		return 8
	return n
	
def num(s):
   if not s: return 0
   try:
      return int(s)
   except ValueError:
      return 0

def eliminated(p, setVal=None):
	val = list(getGlobalVariable("Eliminated"))	
	if setVal is None:
		return val[p._id] == '1'
	if setVal == True:
		val[p._id] = '1'
	else:
		val[p._id] = '0'
	setGlobalVariable("Eliminated", "".join(val))
	return setVal
	
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
		if dest.controller != me:
			card.setController(dest.controller) #Pass control to the pile controller and ask them to move it
			remoteCall(dest.controller, "moveCard", [card, dest, index])
		else:
			card.moveTo(dest, index)
	
	if locked:
		unlockPile(shared.piles['Internal'])

# Called remotely to move a card to a pile we control
def moveCard(card, pile, index):
	mute()
	card.moveTo(pile, index)
	
def isOpen(card):
	if card is None or card.Type != 'Location':
		return False
	return (card.orientation == Rot0 and card.alternate != "B")

def deleteCard(card):
	mute()
	if card is not None:
		card.delete()
	
#Any card loaded into the player area must be removed from the box otherwise we end up with duplicates
#Find an exact match based on the card model, if none look for a name match
def inUse(pile):
	mute()
	for card in pile:
		if card.Subtype in shared.piles:
			found = findCard(shared.piles[card.Subtype], card.model)
			if found is None:
				found = findCardByName(shared.piles[card.Subtype], card.name)
			if found is not None:
				if found.controller != me:
					remoteCall(found.controller, "deleteCard", [found])
					sync()
				else:
					found.delete()
			else:
				notify("{} is using '{}' which is not in the box".format(me, card))

def rollDice(card): #Roll the dice based on the number of tokens
	mute()
	rolled = 0
	dice = ""
	detail = ""
	for die in [ d12, d10, d8, d6, d4 ]:
		count = card.markers[die]
		if count > 0:
			dice += " + {}{}".format(count, die[0])
			detail += " + ["
			while count > 0:
				roll = 1 + int(random() * num(die[0][1:]))
				detail ="{}{}{}".format(detail,roll,"+" if count > 1 else "]")
				rolled += roll
				count -= 1
			card.markers[die] = 0
	
	if card.markers[plus] > 0:
		rolled += card.markers[plus]
		dice = "{} + {}".format(dice, card.markers[plus])
		detail = "{} + {}".format(detail, card.markers[plus])
		card.markers[plus] = 0
	if card.markers[minus] > 0:
		rolled -= card.markers[minus]
		dice = "{} - {}".format(dice, card.markers[minus])
		detail = "{} - {}".format(detail, card.markers[minus])
		card.markers[minus] = 0
	
	if len(dice) > 0:
		playSound("dice")
		notify("{} rolls {} on {}".format(me, dice[3:], card))
		notify("{} = {}".format(detail[3:], rolled))
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
	tokens(card, 3)

def plusTwo(card, x=0, y=0):
	tokens(card, 2)
	
def plusOne(card, x=0, y=0):
	tokens(card, 1)	
	
def minusThree(card, x=0, y=0):
	tokens(card, -3)

def minusTwo(card, x=0, y=0):
	tokens(card, -2)

def minusOne(card, x=0, y=0):
	tokens(card, -1)

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
	
	if perm == False:
		card.orientation = Rot90
		notify("{} temporarily closes '{}'".format(me, card))
		return True
		
	# Move cards from location pile back to box
	# If we find the Villain then the location is not closed and the Villain is displayed
	# We need to use a pile with full visibility to access the card type
	pile = card.pile()
	visible = shared.piles['Internal']
	if not lockPile(visible): return
	
	debug("Cleaning up pile '{}'".format(pile.name))
	for c in pile:
		c.moveTo(visible)
	
	villain = [ c for c in visible if c.Subtype == 'Villain' ]
	for c in villain:
		notify("You find {} while attempting to close this location".format(c))
		c.moveTo(pile)
		
	for c in visible: #Banish the remaining cards (unless we are at the Garrison)
		debug("Unexplored ... '{}'".format(c))
		if len(villain) == 0 and card.name == 'Garrison' and c.Subtype in ['Weapon','Armor']:
			c.moveTo(pile)
		else:
			banishCard(c)
	
	unlockPile(visible)
				
	if len(pile) > 1:
		shuffle(pile)
	
	if len(villain) > 0: # Close fails - we temporarily close it instead
		card.orientation = Rot90 
		return False
	
	notify("{} permanently closes '{}'".format(me, card))
	if len(card.Attr4) > 0 and card.Attr4 != "No effect.":
		notify(card.Attr4)
	flipCard(card)
	return True
	
def cleanupGame(cleanupStory=False):
	for p in getPlayers():
		if p == me:
			cleanupPiles(cleanupStory)
		else:
			remoteCall(p, "cleanupPiles", [cleanupStory])

def cleanupPiles(cleanupStory=False): #Clean up the cards that we control
	for card in table:
		if card.controller == me:
			#Remove the pile link on cards leaving the table
			if card.pile() is not None:
				card.link(None)
			shipFound = 0	
			if card.Type == 'Character':
				if card.Subtype == 'Token':
					card.moveTo(card.owner.hand)
				else:
					card.switchTo() # Display side A of the card as it shows the deck makeup
			elif not cleanupStory and card.Type == 'Boon': # Return displayed cards to the controller's hand
				card.moveTo(me.hand)
			elif card.Type == 'Ship':
				shipFound = 1
			elif cleanupStory or card.Type != 'Story':
				returnToBox(card)

	for i in range(8): # Loop through 8 location decks
		pile = shared.piles["Location{}".format(i+1)]
		if pile.controller == me:
			for card in pile:
				returnToBox(card)

	for p in [ 'Blessing Deck', 'Blessing Discard', 'Special', 'Scenario' ]:
		pile = shared.piles[p]
		if pile.controller == me:
			for card in pile:
				returnToBox(card)
	
#------------------------------------------------------------
# Global variable manipulations function
#------------------------------------------------------------	

# A Global variable is created for each location pile named after the location
# No functional interface is supplied for this however personal globals needed for reconnect are

def storeHandSize(h):
	me.setGlobalVariable('HandSize', str(h))

def getHandSize(p=me):
	#Press Ganged uses the scenario pile to determine the hand size
	scenario = [m.Name for m in table if m.Subtype == 'Scenario']
	if len(scenario) == 1 and scenario[0] == 'Press Ganged!' and len(shared.piles['Scenario']) <= num(p.getGlobalVariable('HandSize')):
		return len(shared.piles['Scenario'])
	return num(p.getGlobalVariable('HandSize'))
	
def storeFavoured(f):
	me.setGlobalVariable('Favoured', f)

def getFavoured():
	return me.getGlobalVariable('Favoured')
	
def storeCards(s):
	me.setGlobalVariable('Cards', s)
	
def getCards():
	return me.getGlobalVariable('Cards')

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
		
	if pile.controller != me:
		pile.setController(me)
		sync()
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

#Look at the global variables to determine who was the active player on the given turn
def getPlayer(turn):
	for var in [ 'Current Turn', 'Previous Turn' ]:
		info = getGlobalVariable(var)
		if len(info) > 0:
			t, p = info.split('.')
			if int(t) == turn:
				for player in getPlayers():
					if player.name == p:
						return player
	return None
	
#---------------------------------------------------------------------------
# Call outs
#---------------------------------------------------------------------------

def deckLoaded(player, groups):
	mute()

	if player != me:
		return
		
	isShared = False
	isFleet = False
	for p in groups:
		if p.name == 'Fleet':
			isFleet = True
		if p.name in shared.piles:
			isShared = True
		
	if isFleet and isShared: # Allow player to choose a ship from their fleet deck and put it onto the table
		fleet = [ card.name for card in shared.piles['Fleet'] if card.Type == 'Ship' ]
		debug("Fleet cards found: {}".format(fleet))
		if len(fleet) > 1:
			choice = askChoice("Choose Your Ship", fleet)
		elif len(fleet) == 1:
			choice = 1
		else:
			whisper("Fleet card not loaded")
		if choice:
			activeShip = findCardByName(shared.piles['Fleet'], fleet[choice-1])
			activeShip.moveToTable(PlayerX(-1), StoryY)
		
	if not isShared: # Player deck loaded
		playerSetup()
	
def startOfTurn(player, turn):
	mute()
	debug("Start of Turn {} for player {}".format(turn, player))
	
	clearTargets()
	if player == me: # Store my details in the global variable
		setGlobalVariable("Previous Turn", getGlobalVariable("Current Turn"))
		setGlobalVariable("Current Turn", "{}.{}".format(turn, player.name))
			
	lastPlayer = getPlayer(turn-1)
	debug("Last Player = {}, player = {}, me = {}".format(lastPlayer, player, me))
	if lastPlayer is not None and me == lastPlayer:
		drawUp(me.hand)
		
	# Pass control of the shared piles and table cards to the new player
	debug("Processing table ...")
	for card in table: 
		if card.controller == me: # We can only update cards we control	
			if card.orientation != Rot0: #Re-open any temporarily closed locations
				card.orientation = Rot0	
			if card.Type == 'Character':
				if card.owner == me: #Highlight my avatar
					if player == me: # I am the active player
						card.sendToFront()
						card.highlight = "#82FA58" # Green
					elif eliminated(me):
						card.highlight = "#FF0000" # Red
					else:
						card.highlight = None
			elif player != me: #Pass control of all non-character cards to the new active player
				card.setController(player)
	
	debug("Processing shared piles ...")	
	for name in shared.piles:
		if shared.piles[name].controller == me and player != me: # Hand over control to the new player
			shared.piles[name].setController(player)
		
	if player == me:
		sync() # wait for control of cards to be passed to us
		# Perform scenario specific actions
		scenario = [ c for c in table if c.Subtype == 'Scenario' ]
		if len(scenario) == 1:
			fn = scenario[0].Name.replace(' ','').replace('!','')
			if fn in globals():
				globals()[fn]()
		advanceBlessingDeck()	
		
#
# Scenario specific functions - called at the start of each turn and must be named exactly as the Scenario card with the spaces removed
#
def HereComestheFlood():
	mute()
	#Pick a random location
	locs = [ c for c in table if c.Type == 'Location' ]
	loc = locs[int(random()*len(locs))]
	#Move 1d4 cards from that location to the table
	moved = 0
	toMove = 1+int(random()*4)
	for c in loc.pile().bottom(toMove):
		c.moveTo(shared.piles['Special'])
		moved += 1
	if toMove == moved:
		notify("{} moves {} cards from {} to Black Magga".format(me, moved, loc))
	else:
		notify("{} moves {} cards (rolled {}) from {} to Black Magga".format(me, moved, toMove, loc))

def SandpointUnderSiege():
	mute()
	#Pick a random open location
	locs = [ c for c in table if isOpen(c) ]
	loc = locs[int(random()*len(locs))]
	if len(loc.pile()) == 0:
		notify("Random open location '{}' has no cards".format(loc))
	else:
		c = loc.pile().top()
		x, y = loc.position
		c.moveToTable(x, y+14)
		notify("{} reveals '{}' as the top card of '{}'".format(me, c, loc))
		if c.Type == 'Boon':
			banishCard(c)
		elif c.Type == 'Bane':
			notify("{} shuffles '{}' back into '{}'".format(me, c, loc))
			c.moveTo(loc.pile())
			shuffle(loc.pile(), True)
	
#
#Card Move Event
# We only care if we have just moved our avatar from hand to the table
# or if the blessing discard pile changes
# We also stop a player moving the avatar from the table
#
def checkMovement(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove, highlight=None, markers=None):
	mute()
	bd = shared.piles['Blessing Discard']
	if fromGroup == bd or toGroup == bd or me.isActivePlayer: #Check to see if the current blessing card needs to change
		bx = PlayerX(0)
		by = StoryY	
		bc = None #Temp blessing card	
		for c in table:
			if c.pile() == shared.piles['Blessing Deck']:
				bx, by = c.position
				if fromGroup == bd or toGroup == bd: # Tidy up the temp blessing card
					if c.controller == me:
						c.link(None)
						c.delete()
				else:
					bc = c
				break
					
		if me.isActivePlayer and len(bd) > 0 and bc is None: # Create a copy of the top card
			bc = table.create(bd.top().model, bx, by)
			bc.link(shared.piles['Blessing Deck'])
	
	#We only care if we moved the avatar
	if isScriptMove or player != me or card.Type != 'Character' or card.Subtype != 'Token':
		return
	
	if fromGroup == table and toGroup != table: # Did we move the avatar off the table
		# Don't allow this
		card.moveToTable(oldX, oldY)
		return
	
	if fromGroup != table and toGroup == table: # Did we move the avatar onto the table
		# If the scenario hasn't been set up yet return the avatar to hand and issue a warning
		locs = [ c for c in table if c.Type == 'Location' ]
		if len(locs) == 0:
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
		if favoured == 'Your choice':
			#Make a list of card types in the deck
			choices = []
			for card in me.Discarded:	
				if card.Subtype not in choices:
					choices.append(card.Subtype)
				if card.Subtype == 'Loot': # Loots have a secondary type too
					if card.Subtype2 not in choices:
						choices.append(card.Subtype2)
			#Prompt user to select favoured card type
			choice = None
			if len(choices) > 0:
				while choice == None or choice == 0:
					choice = askChoice("Favoured Card Type", choices)
				favoured = choices[choice-1]
		handSize = getHandSize()
		ci = 0
		for card in me.Discarded:
			if card.Subtype == favoured or (card.Subtype == 'Loot' and card.Subtype2 == favoured): break
			ci += 1
			
		if ci >= size:
			ci = 0
			notify("{} has an invalid deck - no favoured cards ({})".format(me, favoured))
		
		if ci > 0: #Move the top cards to deck so that the favoured card is at the top of the Discarded pile
			for card in me.Discarded.top(ci):
				card.moveToBottom(me.Discarded)

		for c in me.Discarded.top(handSize):
			c.moveTo(me.hand)
		#Move the rest of the cards into the deck
		for card in me.Discarded:
			card.moveTo(me.deck)
		
		sync()
		#The first player to drag to the table becomes the active player
		tokens = [ c for c in table if c.Subtype == 'Token' ]
		if len(tokens) == 1:
			#Check to see who the active player is
			active = None
			for p in getPlayers():
				if p.isActivePlayer:
					active = p
					break
			if active is None: # At the start of a game no one is active but anyone can set the active player
				makeActive(me)
			else:
				remoteCall(active, "makeActive", [me])

def makeActive(who):
	mute()
	if who != me:
		debug("{} passes control to {}".format(me, who))
	who.setActivePlayer()

# Called when a player draws an arrow between two cards (or clears an arrow)
# If the source card has dice on it, they are moved to the destination
# This is done in two parts, the controller of the dst card adds dice based on the src
# Then the controller of the src card removes the dice on it
def passDice(player, src, dst, targeted):
	mute()
	if targeted and dst.controller == me:	
		whisper("dst controller is {}".format(dst.controller))
		dice=""
		for m in [ d12, d10, d8, d6, d4 ]:
			if src.markers[m] > 0:
				dice = "{} + {}{}".format(dice, src.markers[m], m[0])
				dst.markers[m] += src.markers[m]
		if src.markers[plus] > 0:
			dice = "{} + {}".format(dice, src.markers[plus])
			dst.markers[plus] += src.markers[plus]
		if src.markers[minus] > 0:
			dice = "{} - {}".format(dice, src.markers[minus])
			dst.markers[minus] += src.markers[minus]
		if src.controller != me:
			remoteCall(src.controller, "clearDice", [src])
		else:
			clearDice(src)
		notify("{} Moves {} from {} to {}".format(player, dice[3:], src, dst))

# Remove all dice from the card
def clearDice(card):
	mute()
	whisper("Clearing dice on {}".format(card))
	for m in [ d12, d10, d8, d6, d4, plus, minus ]:
		if card.markers[m] > 0:
			card.markers[m] = 0	
		
#---------------------------------------------------------------------------
# Table group actions
#---------------------------------------------------------------------------

# Remove targeting arrows after a check
def clearTargets(group=table, x=0, y=0):
	for c in group:
		if c.controller == me or (c.targetedBy is not None and c.targetedBy == me):
			c.target(False)
			
#Table action - prompts the player to pick an adventure path, an adventure and a scenario
#If there is already a scenario on the table clear it away
def pickScenario(group=table, x=0, y=0):
	mute()
	
	#If any of the players haven't loaded their deck we abort
	for p in getPlayers():
		if getHandSize(p) == 0:
			whisper("Please wait until {} has loaded their deck and then try again".format(p))
			return
	
	#Take control of the shared piles
	for name in shared.piles:
		if shared.piles[name].controller != me:
			shared.piles[name].setController(me)
	sync()
	
	story = [ card for card in group if card.Type == 'Story' ]
	if len(story) > 0:
		if not confirm("Clear the current game?"):
			return
		cleanupGame(True)
		sync() #wait for other players to tidy up their cards
	
	rise = False # Rise of the Runelords adventure path has special rules for banishing cards with the Basic and Elite traits
	setGlobalVariable('Previous Turn', '')
	setGlobalVariable('Current Turn', '')
	setGlobalVariable('Remove Basic', '')
	setGlobalVariable('Remove Elite', '')
	
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
		rise = 0
		skull = 0
	else:
		path = findCardByName(shared.piles['Story'], paths[choice-1])
		path.moveToTable(PlayerX(-4),StoryY)
		rise = path.Name == 'Rise of the Runelords'
		skull = path.Name == 'Skull and Shackles'
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
		#If playing Skull and Shackles, make sure Fleet card has been loaded, otherwise abort
		if skull:
			fleetLoaded = 0
			for card in table:
				if card.Type == 'Ship':
					fleetLoaded = 1
			if fleetLoaded == 0:
				whisper("Please load the Fleet deck before playing the Skull and Shackles adventure".format(p))
				return
		adventure = findCardByName(shared.piles['Story'], adventures[choice-1])
		adventure.moveToTable(PlayerX(-3), StoryY)
		if rise or skull:
			if num(adventure.Abr) >= 3:
				setGlobalVariable("Remove Basic", "1")
			if num(adventure.Abr) >= 5:
				setGlobalVariable("Remove Elite", "1")
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
		scenario.moveToTable(PlayerX(-2),StoryY)
		scenarioSetup(scenario)

def nextTurn(group=table, x=0, y=0):
	mute()
	# Only the current active player can do this
	if not me.isActivePlayer:
		whisper("Only the active player may perform this operation")
		return
	players = getPlayers()
	nextID = (me._id % len(players)) + 1
	while nextID <> me._id:
		for p in players:
			if p._id == nextID and not eliminated(p):
				p.setActivePlayer()
				return
		nextID = (nextID % len(players)) + 1
	me.setActivePlayer()
	
def randomHiddenCard(group=table, x=0, y=0):
	pile, trait = cardTypePile()
	if pile is None: return
	if pile.controller != me:
		remoteCall(pile.controller, "randomCardN", [me, pile, trait, x, y, 1, True])
	else:
		randomCardN(me, pile, trait, x, y, 1, True)
	
def randomCard(group=table, x=0, y=0):
	pile, trait = cardTypePile()
	if pile is None: return
	if pile.controller != me:
		remoteCall(pile.controller, "randomCardN", [me, pile, trait, x, y, 1])
	else:
		randomCardN(me, pile, trait, x, y, 1)

def randomCards(group=table, x=0, y=0):
	quantity = [ "One", "Two", "Three", "Four", "Five", "Six" ]
	choice = askChoice("How many?", quantity)
	if choice <= 0:
		return
	pile, trait = cardTypePile()
	if pile is None: return
	if pile.controller != me:
		remoteCall(pile.controller, "randomCardN", [me, pile, trait, x, y, choice])
	else:
		randomCardN(me, pile, trait, x, y, choice)

def hasTrait(card, trait):
	if card is None:
		return False
	if trait == "Any":
		return True
	if card.Traits is None or len(card.Traits) == 0:
		return False
	return trait in card.Traits.splitlines()
	
def randomCardN(who, pile, trait, x, y, n, hide=False):
	mute()
	if y > 0:
		y -= 50
	cards = [ c for c in pile if hasTrait(c, trait) ]
	while n > 0 and len(cards) > 0:
		card = cards[int(random()*len(cards))]
		cards.remove(card)
		card.moveToTable(x, y, hide or n > 1)
		if who != me:
			card.setController(who)
		x = x + 10
		n -= 1	

def cardTypePile():
	mute()
	types = ["Henchman", "Monster", "Barrier", "Armor", "Weapon", "Spell", "Item", "Ally", "Blessing", "Ship"]
	choice = askChoice("Pick card type", types)
	if choice <= 0:
		return None, None	
	pile = shared.piles[types[choice-1]]
	
	# Ask for an optional trait
	traits = [ ]	
	for c in pile:
		for t in c.Traits.splitlines():
			if t != "and" and t not in traits:
				traits.append(t)
	traits.sort()
	traits.insert(0, "Any")
	choice = 1
	if len(traits) > 1:
		choice = askChoice("Pick a trait", traits)
		if choice <= 0:
			choice = 1
	return pile, traits[choice-1]
	
#---------------------------------------------------------------------------
# Menu items - called to see if a menu item should be shown
#---------------------------------------------------------------------------
def isPile(cards):
	for c in cards:
		if c.pile() is None:
			return False
	return True

def isLocation(cards):
	for c in cards:
		if c.Type != 'Location':
			return False
	return True

def isVillain(cards):
	for c in cards:
		if c.Subtype != 'Villain':
			return False
	return True
	
def isBoon(cards):
	for c in cards:
		if c.Type != 'Boon':
			return False
	return True
	
def isBoxed(cards):
	for c in cards:
		if c.Type not in ('Boon', 'Bane', 'Feat', 'Ship'):
			return False
	return True
	
def hasDice(cards):
	for c in cards:
		count = 0
		for die in [ d12, d10, d8, d6, d4 ]:
			count += c.markers[die]
		if count == 0:
			return False
	return True

#---------------------------------------------------------------------------
# Table card actions
#---------------------------------------------------------------------------
def exploreLocation(card, x=0, y=0):
	mute()
	if card.type != 'Location':
		whisper("This is not a location ....")
		return
	#Ensure all locations that were temporarily closed are re-opened
	for c in table:
		if c.Type == 'Location' and c.orientation != Rot0:
			c.orientation = Rot0
			
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
		clearTargets()
		return
	if card.pile() is not None and (card.Type == 'Location' or len(card.pile()) > 0):
		if card.Type == 'Location': # Explore location
			if len(card.pile()) > 0:
				exploreLocation(card)
			else:
				closePermanently(card)
		elif card.pile() == shared.piles['Blessing Deck']: # Reveal the next blessing
			advanceBlessingDeck()
		else:
			t = card.pile().top()
			x, y = card.position
			t.moveToTable(x, y+14)
			notify("{} reveals {}".format(me, t))
	elif card.Subtype == 'Villain':
		hideVillain(card)
	elif card.Type == 'Bane': # Assume it is undefeated and shuffle back into location
		shuffleCard(card)
	elif card.type == 'Boon': # Assume it is acquired
		acquireCard(card)
	else:
		flipCard(card, x, y)

def donateDice(card, x=0, y=0):
	# Move any dice on this card to the card targeted by me
	# If there is no target, default to the avatar of the active player
	# The actual dice movement is handled by the event callout when a card is targeted
	t = [ c for c in table if c.targetedBy is not None and c.targetedBy == me ]
	if len(t) == 0:
		t = [ c for c in table if c.Type == 'Character' and c.Subtype == 'Token' and c.highlight is not None ]

	if len(t) != 1:
		whisper("Unsure where to donate dice: target one card and try again")
	elif t[0] == card:
		whisper("You cannot donate dice to yourself")
	else:
		card.arrow(t[0]) # This triggers a callback (passDice)
				
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
		
def tokens(card, num):
	mute()
	total = card.markers[plus] - card.markers[minus] + num
	if total > 0:
		card.markers[plus] = total
		card.markers[minus] = 0
	else:
		card.markers[minus] = -total
		card.markers[plus] = 0
		
def revealCard(card, x=0, y=0):
	mute()
	notify("{} reveals '{}'".format(me, card))
	
def rechargeCard(card, x=0, y=0):
	mute()
	notify("{} recharges '{}'".format(me, card))
	card.moveToBottom(me.deck)
	
def displayCard(card, x=0, y=0):
	mute()
	notify("{} displays '{}'".format(me, card))

def acquireCard(card, x=0, y=0):
	mute()
	card.moveTo(me.hand)
	notify("{} acquires '{}'".format(me, card))
	
def banishCard(card, x=0, y=0): #Move to correct pile in box
	mute()
	
	if card.Subtype == 'Villain': # This is probably not what the player wanted to do
		hideVillain(card, x, y, True)
		return
	
	if not isBoxed([card]):
		return
	
	if card.pile() == shared.piles['Blessing Deck']:
		if confirm("Are you sure?") != True: # This is unusual
			return
		card = shared.piles['Blessing Discard'].top()
		card.link(None)
		
	removeBasic = (getGlobalVariable("Remove Basic") == "1")
	removeElite = (getGlobalVariable("Remove Elite") == "1")
	remove = ((removeBasic and hasTrait(card, "Basic")) or (removeElite and hasTrait(card, "Elite")))

	if remove and ((card.Type == 'Boon' and confirm("Remove {} from box?".format(card.Name)) == True) or card.Type == 'Bane'):
		removeCard(card)
	else:
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
	card.delete()

def shuffleCard(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None: # This is a normal card - if it is over a pile we shuffle it into the pile
		c = overPile(card)
		if c is None: return
		pile = c.pile()
		notify("{} moves '{}' into '{}' deck".format(me, card, pile.name))
		card.moveTo(pile)
	shuffle(pile)
	
def peekTop(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None or len(pile) == 0: return
	notify("{} looks at the top card of the '{}' deck".format(me, card))
	src = pile.top()
	src.peek() # This doesn't seem to reveal the card id as expected
	#Move the top card to a pile with full visibility
	if lockPile(shared.piles['Internal']):
		src.moveTo(shared.piles['Internal'])	
		whisper("{} looks at '{}'".format(me, src))
		src.moveTo(pile)
		unlockPile(shared.piles['Internal'])	

def peekTop2(card, x=0, y=0):
	peekTopN(card, 2)

def peekTop3(card, x=0, y=0):
	peekTopN(card, 3)

def peekTop5(card, x=0, y=0):
	peekTopN(card, 5)
	
def peekTopN(card, n):
	mute()
	pile = card.pile()
	if pile is None: return
	notify("{} looks at the top {} cards of the '{}' deck".format(me, n, card))
	pile.lookAt(n)
		
def peekBottom(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None: return
	notify("{} looks at the bottom card of the '{}' deck".format(me, card))
	src = pile.bottom()
	src.peek() # This doesn't seem to reveal the card id as expected
	#Move the bottom card to a pile with full visibility
	if lockPile(shared.piles['Internal']):
		src.moveTo(shared.piles['Internal'])	
		whisper("{} looks at '{}'".format(me, src))
		src.moveToBottom(pile)
		unlockPile(shared.piles['Internal'])
	
def peekBottom2(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None: return
	notify("{} looks at the bottom 2 cards of the '{}' deck".format(me, card))
	pile.lookAt(2, False)
	
def peekBottom3(card, x=0, y=0):
	mute()
	pile = card.pile()
	if pile is None: return
	notify("{} looks at the bottom 3 cards of the '{}' deck".format(me, card))
	pile.lookAt(3, False)

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
	if closeLocation(card, True):
		local = findCardByName(table, 'Local Heroes')
		if local is not None or card.Name in [ 'Death Zone', 'Sunken Treasure']: # These scenarios are only won when the last location is closed
			open = [ c for c in table if isOpen(c) ]
			if len(open) == 0:
				gameOver(True)
		return True
	return False

def closeTemporarily(card, x=0, y=0):
	closeLocation(card, False)
	
def hideVillain(villain, x=0, y=0, banish=False):
	mute()
	if villain.Subtype != 'Villain':
		notify("This is not a Villain ...")
		return
	
	choices = [ 'Evaded', 'Defeated', 'Undefeated' ]
	if banish:
		choices.append('Banished')
	choice = askChoice("Was the villain ....", choices)
	if choice is None or choice == 0:
		return
	
	if villain.pile() is not None:
		villain.link(None)
		
	if choices[choice-1] == 'Evaded':
		shuffleCard(villain, x, y)
		return
		
	if choices[choice-1] == 'Banished':
		notify("{} banishes '{}'".format(me, villain))
		returnToBox(villain)
		return
	
	# We need to hide the villain in an open location
	defeated = choices[choice-1] == 'Defeated'		
	blessing = shared.piles['Blessing'] if defeated else shared.piles['Blessing Deck']		
	location = overPile(villain) #Determine the location of the Villain (based on the if it is over a pile on the table)
	closed = True
	if defeated: # We get to close the location
		if location is None or location.Type != 'Location': # Not sure which location to close
			if not confirm("Did you close the location?"):
				whisper("Close the location manually, then hide the villain")
				return
		elif isOpen(location): # Ensure location is closed
			closed = closePermanently(location) # Villains found in pile so game is not over
	
	#If there are no open locations the villain has been cornered
	open = [ card for card in table if isOpen(card) ]
	if len(open) == 0:
		returnToBox(villain)
		if closed:
			gameOver(True)
		else: # There are more villains left in the pile
			notify("{} returns {} to the box".format(me, villain))			
		return
	
	# The villain has escaped
	debug("Villain has {} open locations".format(len(open)))
	hidden = shared.piles['Internal']
	if not lockPile(hidden):
		return	
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
			
	unlockPile(hidden)
	
#---------------------------------------------------------------------------
# Pile Group Actions
#---------------------------------------------------------------------------
	
def rechargeRandom(group, x=0, y=0): # Discarded pile
	mute()
	if len(group) == 0: return
	card = group.random()
	notify("{} recharges '{}'".format(me, card))
	card.moveToBottom(me.deck)

def buryRandom(group, x=0, y=0): # Discarded pile
	mute()
	if len(group) == 0: return
	card = group.random()
	notify("{} buries '{}'".format(me, card))
	card.moveTo(me.Buried)

def discardRandom(group, x=0, y=0): # Hand
	mute()
	if len(group) == 0: return
	card = group.random()
	notify("{} discards '{}'".format(me, card))
	card.moveTo(me.Discarded)
	
def returnToBlessingDeck(group, x=0, y=0): # Blessing Discard
	mute()
	if len(group) == 0:
		notify("No cards to return")
		return
	destination = shared.piles['Blessing Deck']
	group.random().moveTo(destination, int(random()*(1+len(destination))))
	notify("{} returns a card to the Blessing Deck".format(me))

def revealRandom(group, x=0, y=0): # Most shared piles use this
	if len(group) == 0: return
	group.random().moveToTable(x, y)
	
def shufflePile(group, x=0, y=0): # Most piles use this
	mute()
	if len(group) == 0: return
	shuffle(group)
	
def addPlunder(group, x=0, y=0):
	mute()
	options = [ 'weapon', 'spell', 'armor' , 'item', 'ally' ]
	choice = int(random()*6)
	if choice >= 5:
		choice = askChoice("Plunder Type", options)
		if choice is None or choice == 0:
			return
		choice -= 1
	notify("{} adds {} to {}".format(me, options[choice], group.name))
	shared.piles[options[choice]].random().moveTo(group)
	
#---------------------------------------------------------------------------
# Hand Group Actions
#---------------------------------------------------------------------------

def drawUp(group): # group == me.hand
	mute()
	handSize = getHandSize()
	if len(group) > handSize:
		notify("{} already has too many cards ({}), max {}".format(me, len(group), handSize))
		return
	
	toDraw = handSize - len(group)
	for c in me.deck.top(toDraw):
		c.moveTo(group)
	
	if len(group) < handSize: #We ran out of cards ... and died
		eliminated(me, True)
		notify("{} has run out of cards".format(me))
	elif toDraw == 1:
		notify("{} draws a card".format(me))
	elif toDraw > 0:
		notify("{} draws {} cards".format(me, toDraw))

#---------------------------------------------------------------------------
# Deck Group Actions
#---------------------------------------------------------------------------

def drawCard(group, x=0, y=0): # me.deck
	mute()
	card = group.top()
	if card is None:
		return	
	card.moveTo(me.hand)
	notify("{} draws '{}'".format(me, card))
	
#---------------------------------------------------------------------------
# Game logic and set up
#---------------------------------------------------------------------------
def playerSetup():
	id = me._id
	debug("Player {}: Setup ....".format(id))
	
	sync() # Make sure all other processing is complete
	inUse(me.Discarded) #Remove all the loaded player cards from the box (shared piles)
	
	handSize = 4
	favoured = 'Your choice'
	cardTypes = [ 'Weapon', 'Spell', 'Armor', 'Item', 'Ally', 'Blessing' ]
	minC = { 'Weapon':0, 'Spell':0, 'Armor':0, 'Item':0, 'Ally':0, 'Blessing':0 }
	maxC = { 'Weapon':0, 'Spell':0, 'Armor':0, 'Item':0, 'Ally':0, 'Blessing':0 }
	custom = False
	#Move Character Card to the table
	for card in me.hand:
		if card.Type == 'Character':
			if card.Subtype != 'Token': # Extract information about the hand size and favoured card type
				custom = card.name == 'Custom'
				if len(card.Attr3) > 0:
					favoured = card.Attr3
					debug("Favoured = {}".format(favoured))
				#Store Card counts
				for line in card.Attr2.splitlines():
					type, rest = line.split(':',1)
					counts = rest.split()
					minC[type] = num(counts[0])
					maxC[type] = num(counts[len(counts)-1])
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
		elif card.Subtype == 'Favoured':
			favoured = card.name
			debug("Favoured override - {}".format(favoured))
		elif card.Subtype == 'Card':
			type, count = card.name.split()
			minC[type] = num(count)
	
	#Check loaded deck matches expected card distribution. Add missing Card feats if required
	hexmap = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f' ]
	counts = { 'Weapon':0, 'Spell':0, 'Armor':0, 'Item':0, 'Ally':0, 'Blessing':0 }
	for c in me.Discarded:
		if c.Subtype == 'Loot':
			type = c.Subtype2
		else:
			type = c.Subtype
		counts[type] += 1
		
	i = 0
	dist=""
	for type in cardTypes:
		dist = dist + "{}:{} ".format(type, counts[type])
		if counts[type] > maxC[type] and not custom:
			notify("{} has more '{}' cards than allowed".format(me, type))
		if counts[type] < minC[type]:
			whisper("You don't have enough '{}' cards in your deck. Found {}, expected {}".format(type, counts[type], minC[type]))
		elif counts[type] > minC[type]:
			whisper("You have more '{}' cards than expected - updating your card feat to {}".format(type, counts[type]))
			#Delete the current card feat (if any)
			for c in me.Buried:
				if c.Type == 'Feat' and c.Subtype == 'Card' and type in card.name:
					c.delete()
			id = '7c5d69b1-b5ec-47f2-ba25-5a839291c3' + hexmap[i] + hexmap[counts[type]]
			table.create(id, 0, 0, 1, True).moveTo(me.Buried)
		i += 1	
	
	storeHandSize(handSize)
	storeFavoured(favoured)
	storeCards(dist)
	eliminated(me, False)
	debug("HandSize {}, Favoured type {}".format(handSize, favoured))
	whisper("Drag avatar to your starting location once the scenario is set up")
	
#Set up the scenario
#Move each location to the table and create its deck
#Create the Blessing deck and reveal the top card
def scenarioSetup(card):
	mute()
	
	card.link(shared.piles['Scenario'])
	hidden = shared.piles['Internal']
	if not lockPile(hidden): return
	
	if card.Name == 'The Black Tower':
		bonus = 1 # Add a bonus spell to each location
	else:
		bonus = 0
	locations = card.Attr1.splitlines()
	nl = numLocations()
	if card.Name == 'Rimeskull':
		nl = 8
	elif card.Name == 'Into the Runeforge':
		nl -= 1
	elif card.Name == 'Scaling Mhar Massif':
		nl -= 2
	elif card.Name == 'Press Ganged!':
		nl = 1
		
	if nl < 1:
		nl = 1
	if nl > len(locations):
		nl = len(locations)
	for i in range(nl):
		debug("Processing Location '{}'".format(locations[i]))
		pileName = "Location{}".format(i+1)
		location = findCardByName(shared.piles['Location'], locations[i])
		if location is None:
			whisper("Failed to find location {}".format(locations[i]))
		else:
			locPile = shared.piles[pileName]
			debug("Moving '{}' to table ...".format(location))
			location.moveToTable(LocationX(i+1, nl), LocationY)
			#Create deck based on location distribution 
			deck = location.Attr1.splitlines()
			for entry in deck:
				details = entry.split(' ') # i.e. Monster 3
				if len(details) == 2 and details[0] in shared.piles:
					debug("Adding {} cards of type {}".format(details[1], details[0]))
					pile = shared.piles[details[0]]
					cards = num(details[1])
					#if playing Press Ganged!, add 5 extra Barriers
					if details[0] == 'Barrier' and card.Name == 'Press Ganged!':
						cards += 5
					if details[0] == 'Spell':
						cards += bonus
					for count in range(cards):
						c = pile.random()
						if c is None:
							whisper("No more {} cards to deal to location {}".format(details[0], location))
							break
						c.moveTo(locPile)
				else:
					whisper("Location error: Failed to parse [{}]".format(details[0]))
			location.link(locPile)
			if location.Name == 'The Leng Device':
				location.markers[timer] = 12
			
	#Put the Villain and henchmen in a new pile, then shuffle and deal out to the locations
	flipCard(card) # Villain info is on Side B
	villain = None
	if len(card.Attr2) > 0 and card.Attr2 != 'None':
		for v in card.Attr2.splitlines():
			villain = findCardByName(shared.piles['Villain'], v)
			if villain is None:
				whisper("Setup error: failed to find '{}'".format(v))
			else:
				debug("Moving '{}' to hidden pile".format(villain))
				villain.moveTo(hidden)
	# Some adventures set the villain aside
	if villain is not None and card.Name in ('Here Comes the Flood', 'The Road through Xin-Shalast'):
		villain.moveToTable(PlayerX(-4),StoryY)
		villain.link(shared.piles['Special'])
			
	debug("Hide Henchmen '{}'".format(card.Attr3))
	if 'Per Location: ' in card.Attr3 or ' per location' in card.Attr3: # Special instructions for this one
		henchmen = card.Attr3.replace('Per Location: ','').replace(' per location', '').replace('1 ','').replace('Random ','').split(', ')
		cardsPerLocation = len(henchmen)
		repeat = len(henchmen)		
	elif card.Name == 'Press Ganged!': #For the Press Ganged! scenario, pull one random henchman from the pile and deal it into a new banes pile
		henchmen = card.Attr3.splitlines()
		randIndex = int(random()*len(henchmen))
		randHench = findCardByName(shared.piles['Henchman'], henchmen[randIndex])
		del henchmen[randIndex] #Remove the random henchman from our list - the remaining ones are added to the location
		cardsPerLocation = len(henchmen)
		repeat = 1
		# Move the Random henchman to the banes pile (this is our scenario pile) 
		randHench.moveTo(shared.piles['Scenario'])
	else:
		henchmen = card.Attr3.splitlines()
		cardsPerLocation = 1
		repeat = 1
		if card.Name == 'Into the Eye':
			cardsPerLocation += len(getPlayers())
				
	index = 0
	while len(hidden) < nl * cardsPerLocation:
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
		index += 1
		if index == len(henchmen): #Repeat the last named entry if there are not enough named unique henchmen
			index -= repeat

	debug("Deal from hidden deck ...")
	
	#Now deal them to each location pile
	index = 0
	while len(hidden) > 0:
		pile = shared.piles["Location{}".format(index+1)]
		for i in range(cardsPerLocation):
			if index == 0 and card.Name in ('Rimeskull', 'Into the Runeforge'):
				hidden.bottom().moveTo(pile) # Ensure Villain is in first location
			else:
				hidden.random().moveTo(pile)
		shuffle(pile)
		index += 1
	unlockPile(hidden)
	
	#Create the Blessing deck
	if card.Name != "Into the Eye":
		src = shared.piles['Blessing']
		dst = shared.piles['Blessing Deck']
		if card.Name == 'Sandpoint Under Siege':
			blessings = 25
		else:
			blessings = 30
		blessings += shared.ExtraBlessings
		if blessings < 0:
			blessings = 1
		while len(src) > 0 and len(dst) < blessings:
			src.random().moveTo(dst)		
		
	notify("{} starts '{}'".format(me, card))

def advanceBlessingDeck():
	#Move the top card of the Blessing deck to the discard pile	
	pile = shared.piles['Blessing Deck']	
	if len(pile) == 0:
		#If we are playing the adventure "Into the Eye" then there is no blessing deck
		if findCardByName(table, "Into the Eye") is None:
			# Out of time - the players have lost
			gameOver(False)	
		return
		
	pile.top().moveTo(shared.piles['Blessing Discard'])
	notify("{} advances the Blessing Deck".format(me))
	
	# Here comes the flood has special end conditions
	flood = findCardByName(table, 'Here Comes the Flood')
	if flood is not None:
		# Check to see if all locations are empty
		cardsToExplore = 0
		for i in range(8): # Loop through 8 location decks
			cardsToExplore += len(shared.piles["Location{}".format(i+1)])
		if cardsToExplore > 0 and len(pile) > 0:
			flood = None
	if flood is not None: # Compare dead allies to rescued allies
		died = 0
		for c in shared.piles['Special']:
			returnToBox(c)
			if c.Subtype == 'Ally':
				died += 1
		saved = len(shared.piles['Scenario'])
		notify("You saved {} allies and lost {} allies".format(saved, died))
		gameOver(saved >= died)
			
def gameOver(won):
	if won:
		loot = [ c for c in shared.piles['Scenario'] ]
		
	cleanupGame()				
	for p in getPlayers():
		if p == me:
			displayHand(me)
		else:
			remoteCall(p, "displayHand", [me])
			
	if won:
		x = -300
		for c in loot:
			c.moveToTable(x, 0)
			x += 32
		notify("You won the scenario")
	else:
		notify("You lost the scenario")
		
#Move all my cards back into my hand ordered by type
def displayHand(who):
	mute()
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
			if c.Subtype == type or (c.Subtype == 'Loot' and c.Subtype2 == type):
				c.moveTo(me.hand)
	whisper("Expected card distribution is {}".format(getCards()))