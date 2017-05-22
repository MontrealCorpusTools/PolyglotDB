import sys
import os
from textgrid import TextGrid, IntervalTier
from polyglotdb.io.parsers.mfa import MfaParser

# Unit testing for fixes to the MFA parser
testDir = sys.argv[1]

counter = 0
incorrect = 0

for file in os.listdir(os.path.abspath(testDir)):
	counter = counter + 1
	if file.endswith(".TextGrid"):
		path = os.path.join(testDir, file)
		print ("Testing ", file, "...")
		parser = MfaParser("a", "b")
		curTg = TextGrid()
		curTg.read(path)
		value = parser._is_valid(curTg)

		if file.endswith("yes.TextGrid"):
			if value == True:
				print("Correct")
			else:
				print("Incorrect")
				incorrect = incorrect + 1
		if file.endswith("no.TextGrid"):
			if value == False:
				print("Correct")
			else:
				print("Incorrect")
				incorrect = incorrect + 1

		print ("------------")

print(incorrect, "total errors.")