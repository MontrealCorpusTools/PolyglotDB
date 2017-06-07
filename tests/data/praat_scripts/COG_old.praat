
form Variables
	sentence filename sibilant.wav
	real begin
	real end
	boolean fast 1
	integer power 2
endform

Read from file... 'filename$'
Extract part... 'begin' 'end' "rectangular" 1 "yes"
To Spectrum... 'fast'

cog = Get centre of gravity... 'power'
cog$ = fixed$(cog, 2)


echo 'cog$'
