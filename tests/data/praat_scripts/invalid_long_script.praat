
form Choices
	real begin
	real end
	integer channel
	real padding
	sentence filename
endform

fast=1
power=2
Open long sound file... 'filename$'

seg_duration = end - begin
seg_begin = begin + (seg_duration * from_percent)


seg_end = begin + (seg_duration * to_percent)

Extract part... seg_begin seg_end 1
channel = channel + 1
Extract one channel... channel

Rename... segment_of_interest

To Spectrum... 'fast'

cog = Get centre of gravity... 'power'
cog$ = fixed$(cog, 2)


output$ = "cog" + newline$ + cog$
echo 'output$'
