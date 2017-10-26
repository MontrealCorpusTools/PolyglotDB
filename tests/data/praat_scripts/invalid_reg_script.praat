
form Variables
    real begin
    real end
	sentence filename
endform

fast=1
power=2

Read from file... 'filename$'
#Extract part... 'begin' 'end' "rectangular" 1 "yes"
To Spectrum... 'fast'

cog = Get centre of gravity... 'power'
cog$ = fixed$(cog, 2)


output$ = "cog" + newline$ + cog$
echo 'output$'
