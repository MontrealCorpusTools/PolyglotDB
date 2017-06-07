
form Variables
	sentence filename sibilant.wav
endform

fast=1
power=2

Read from file... 'filename$'

dur = Get total duration
quarter = dur / 4
begin = quarter
end = quarter * 3

Extract part... 'begin' 'end' "rectangular" 1 "yes"
To Spectrum... 'fast'

cog = Get centre of gravity... 'power'
cog$ = fixed$(cog, 2)


echo 'cog$'
