form Variables
    sentence filename
    # add more arguments here
endform

# Read the sound file
Read from file... 'filename$'

# Extract the pitch
To Pitch... 0 75 600

# Compute the mean F0
averageF0 = Get mean... 0 0 Hertz

# Print the result
output$ = "mean_pitch" + newline$ + string$(averageF0)
echo 'output$'

# Clean up
select all
Remove
