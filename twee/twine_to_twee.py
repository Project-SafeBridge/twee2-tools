

def passageParser(fileName):
	"""
	write a python function which opens it and parses it to return a dict of passages, where the key of each passage is its name 
	(e.g. for the "::PassageFooter <0,undefined>" passage, the key should be "PassageFooter", 
	and for the "::intro.aboutstella.1 <0,undefined>" passage the key should be "intro.aboutstella.1") 
	and the value of each passage is a string containing its contents 
	(e.g. for the "::PassageFooter" passage, the value should be "<p>Footer goes here</p>\n\n")
	"""
	output = {}
	with open(fileName) as f:
		currentKey = ""
		currentVal = ""
		while True:
			line = f.readline()

			if (line == "\n"): #skip blank line
				continue
			
			if not line: #end of file
				break

			if "::" in line: #extract key
				if not (currentKey == "" and currentVal == ""):
					output[currentKey] = currentVal
					currentVal = ""

				pos = line.find(" ")
				if (pos == -1):
					currentKey = line[2:]
				else:
					currentKey = line[2:pos]

			else: #add to currentVal
				currentVal += line

		print ("Adding to dict: key", currentKey)
		print ("val", currentVal)
		output[currentKey] = currentVal 

	return output

#passageParser("script.txt")