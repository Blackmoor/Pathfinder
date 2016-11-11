#
# Routines for writing out updated decks based on either the player piles or the shared piles
#

#Returns the section the card should be stored in
def getSection(sections, card):
	if card.Type is not None and card.Type in sections:
		if card.Type == 'Ship' and card.Name in eval(getGlobalVariable('Fleet')):
			return 'Fleet'
		return card.Type
	elif card.Subtype is not None:
		if card.Subtype in sections:
			return card.Subtype
		if card.Subtype == 'Loot' and card.Subtype2 in sections:
			return card.Subtype2
	return None

#Mavaro is strange and wonderful. He treats some card types as others. It's kinda annoying.
def getMMMavaroSection(sections, card):
	cardType = getSection(sections,card)
	if cardType in ['Weapon','Spell','Armor']:
		return 'Item'
	else:
		return cardType
		
#Ezren from MM is also pretty weird. He treats non-Divine blessings as items.
def getMMEzrenSection(section, card):
	cardType = getSection(sections, card)
	traits = card.Traits.split()
	if cardType == 'Blessing':
		if 'Divine' in traits:
			return cardType
		else:
			return 'Item'

#Save the player deck - it is named after the character 	
def saveDeck(group, x=0, y=0): #me.hand or table
	sections = { "Character":{},
				"Weapon":{},
				"Spell":{},
				"Armor":{},
				"Item":{},
				"Ally":{},
				"Blessing":{},
				"Feat":{} }
				
	#Add in the character sheet card (from the table)
	character = None
	for card in table:
		if card.owner == me:
			if card.Type == 'Character':
				character = card
				sections["Character"][(card.name, card.model)] = 1
			if card.Type == 'Feat':
				sections["Feat"][(card.name, card.model)] = 1
			
	if character is None: #It may be in the hand
		for card in me.hand:
			if card.Type == 'Character':
				character = card
				break
	
	if character is None:
		whisper("Failed to find character to save")
		return

	piles = [ me.piles[p] for p in me.piles ]
	piles.append(me.hand)
	if character.name == 'Mavaro' and character.Path == 'MM':
		filename = savePiles(character.name+'-saved.o8d',sections, piles, getMMMavaroSection, False)
	elif character.name == 'Ezren' and character.Path == 'MM':
		filename = savePiles(character.name+'-saved.o8d',sections, piles, getMMEzrenSection, False)
	else:
		filename = savePiles(character.name+'-saved.o8d', sections, piles, getSection, False)
	if filename is None:
		whisper("Failed to save deck")
	else:
		notify("{} saves deck to {}".format(me, filename))

#Save the box (shared piles and table)		
def saveBox(group, x=0, y=0): #table
	sections = { "Story":{},
				"Henchman":{},
				"Monster":{},
				"Barrier":{},
				"Armor":{},
				"Weapon":{},
				"Spell":{},
				"Item":{},
				"Ally":{},
				"Blessing":{},
				"Loot":{},
				"Cohort":{},
				"Location":{},
				"Villain":{} }
	piles = [ shared.piles[p] for p in shared.piles if p != 'Internal' ]
	#Add in player piles
	for pl in getPlayers():
		piles.append(pl.hand)
		for p in pl.piles:
			piles.append(pl.piles[p])
	#And finally any cards on the table
	piles.append(table)	
	
	filename = savePiles('Box-Campaign-saved.o8d', sections, piles, getSection, True)
	if filename is None:
		whisper("Failed to save Box")
	else:
		notify("{} saves the box to {}".format(me, filename))
		
	if len(shared.piles['Ship']) > 0: # Save the Fleet deck too
		sections = { "Fleet":{}, "Ship":{} }
		filename = savePiles('Fleet-saved.o8d', sections, piles, getSection, True)
		if filename is None:
			whisper("Failed to save Fleet")
		else:
			notify("{} saves the Fleet to {}".format(me, filename))
			
	if len(shared.piles['Support']) > 0: #Save the Support deck too
		sections = { "Support":{}}
		filename = savePiles('Support-saved.o8d',sections, piles, getSection, True)
		if filename is None: 
			whisper("Failed to save Support")
		else: 
			notify("{} saves the Support deck to {}".format(me, filename))
		

# Generic deck saver
# Loops through the piles and count how many cards there are of each type in each section
# Calls the routine getSection (passed as a parameter) to determine which section a card should be stored in	
def savePiles(name, sections, piles, getSection, isShared):
	internal = shared.piles['Internal']
	if not lockPile(internal): return None
	for p in piles:
		if len(p) > 0:
			moveThem = p[0].Type == '?' # Do we have visibility of the cards in this pile
			if moveThem:
				controller = p.controller
				if controller != me:
					p.setController(me)
					sync()
				for card in p:
					card.moveTo(internal)
				pile = internal	
			else:
				pile = p
			for card in pile:
				if pile == table and card.Subtype == 'Blessing' and card.pile() is not None: #This is a temporary copy of the top of the blessing deck and should be ignored
					continue
				s = getSection(sections, card)					
				if s is None:
					pass #whisper("Ignoring unknown card {}".format(card))
				elif (card.name, card.model) in sections[s]:
					sections[s][(card.name, card.model)] += 1
				else:
					sections[s][(card.name, card.model)] = 1
				if moveThem:
					card.moveTo(p)
			if moveThem and controller != me:
				p.setController(controller)
	unlockPile(internal)
	dir = wd(name)
	if 'GameDatabase' in dir:
		filename = dir.replace('GameDatabase','Decks').replace('d2e34ee4-b26b-4bcd-9709-1c45feb12d40','Pathfinder - Adventure Card Game')
	else:
		filename = "Decks\Pathfinder - Adventure Card Game".join(dir.rsplit('OCTGN',1))
	with open(filename, 'w+') as f:
		f.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
		f.write('<deck game="d2e34ee4-b26b-4bcd-9709-1c45feb12d40">\n')
		for s in sections:
			if len(sections[s]) > 0:
				f.write(" <section name=\"{}\" shared=\"{}\">\n".format(s, isShared))
				count = 0
				for t in sorted(sections[s].keys()):
					f.write("  <card qty=\"{}\" id=\"{}\">{}</card>\n".format(sections[s][t], t[1], t[0]))
					count += sections[s][t]
				f.write(" </section>\n")
				whisper("{} - {}".format(s, count))
		f.write("</deck>\n")
		return filename
	return None