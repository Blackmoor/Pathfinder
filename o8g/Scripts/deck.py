#
# Routines for writing out updated decks based on either the player piles or the shared piles
#

#Returns the section the card should be stored in
def getSection(sections, card):
	if card.Type is not None and card.Type in sections:
		return card.Type
	elif card.Subtype is not None:
		if card.Subtype in sections:
			return card.Subtype
		if card.Subtype == 'Loot' and card.Subtype2 in sections:
			return card.Subtype2
	return None

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
				"Location":{},
				"Villain":{} }
	piles = [ shared.piles[p] for p in shared.piles if p != 'Internal' ]
	piles.append(table)	
	filename = savePiles('Box-Campaign-saved.o8d', sections, piles, getSection, True)
	if filename is None:
		whisper("Failed to safe Box")
	else:
		notify("{} saves the box to {}".format(me, filename))

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
				for card in p:
					card.moveTo(internal)
				pile = internal	
			else:
				pile = p
			for card in pile:
				s = getSection(sections, card)					
				if s is None:
					whisper("Ignoring unknown card {}".format(card))
				elif (card.name, card.model) in sections[s]:
					sections[s][(card.name, card.model)] += 1
				else:
					sections[s][(card.name, card.model)] = 1
				if moveThem:
					card.moveTo(p)
					
	unlockPile(internal)
	filename = wd(name).replace('GameDatabase','Decks').replace('d2e34ee4-b26b-4bcd-9709-1c45feb12d40','Pathfinder - Adventure Card Game')
	
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