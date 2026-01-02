# This script computes the mean F0 (pitch) over a sound file.
# It is designed to be used with PolyglotDB's analyze_script function.
# The script takes a sound file as input and outputs the mean pitch value.

form Variables
    sentence filename  # path to the sound file
    real begin # actual begin time (not including the padding)
    real end # actual end time (not including the padding)
    integer channel # Channel number of the speaker (for discourse with multiple speakers)
    real padding # Padding time around the segment (s)
endform

# Load the long sound file
Open long sound file... 'filename$'

# Adjust segment boundaries with padding
seg_begin = begin - padding
if seg_begin < 0
    seg_begin = 0
endif

seg_end = end + padding
duration = Get total duration
if seg_end > duration
    seg_end = duration
endif

# Extract padded segment
Extract part... seg_begin seg_end 1
channel = channel + 1
Extract one channel... channel

# Extract pitch from full padded segment
# Padding is added specifically for this step because pitch extraction
# requires a minimum window length, which could be too short for certain
# segments (e.g. a phone/word segment)
To Pitch... 0 75 600

# Compute the mean F0 only over the **unpadded** segment
averageF0 = Get mean... begin end Hertz

# Print the result in the required format
output$ = "mean_pitch" + newline$ + string$(averageF0)
echo 'output$'

# Clean up
select all
Remove
