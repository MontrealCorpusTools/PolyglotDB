
form Variables
	sentence filename sibilant.wav
endform

fast=1
power=2

Read from file... 'filename$'
#Extract part... 'begin' 'end' "rectangular" 1 "yes"
To Spectrum... 'fast'

cog = Get centre of gravity... 'power'
cog$ = fixed$(cog, 2)
cog_header$ = "cog"

echo 'cog_header$'
echo 'cog$'
