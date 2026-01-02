form Choices
	sentence filename
	real begin
	real end
	integer channel
	real padding
endform

from_percent = 0.25
to_percent = 0.75
filter_low = 1000
filter_high = 11000


Open long sound file... 'filename$'

duration = Get total duration

seg_duration = end - begin
seg_begin = begin + (seg_duration * from_percent)


seg_end = begin + (seg_duration * to_percent)

Extract part... seg_begin seg_end 1
channel = channel + 1
Extract one channel... channel

Rename... segment_of_interest

Filter (pass Hann band)... filter_low filter_high 100


#MEASURE THE SPECTRUM
To Spectrum... yes
cog = Get centre of gravity... 2
spread = Get standard deviation... 2

#MEASURE THE LONG-TERM AVERAGE SPECTRUM
To Ltas (1-to-1)
peak = Get frequency of maximum... 0 0 Parabolic
slope = Get slope... 0 1000 1000 4000 energy







cog$ = fixed$(cog, 4)
peak$ = fixed$(peak, 4)
slope$ = fixed$(slope, 4)
spread$ = fixed$(spread, 4)
output$ = "peak slope cog spread" + newline$ + peak$ + " " + slope$ + " "+ cog$+ " " + spread$
echo 'output$'
