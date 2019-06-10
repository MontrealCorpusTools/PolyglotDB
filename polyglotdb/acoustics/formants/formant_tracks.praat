form Variables
	sentence filename
	real begin
	real end
	integer channel
	real padding
	real timestep
	real windowlen
    positive nformants
	integer ceiling
endform
Open long sound file... 'filename$'

duration = Get total duration

seg_begin = begin - padding
if seg_begin < 0
    seg_begin = 0
endif

seg_end = end + padding
if seg_end > duration
    seg_end = duration
endif

Extract part... seg_begin seg_end 1
channel = channel + 1
Extract one channel... channel

Rename... segment_of_interest

#Measure a third of the way through

segDur = end - begin



selectObject: "Sound segment_of_interest"
To Formant (burg)... 'timestep' 'nformants' 'ceiling' 'windowlen' 50
frames = Get number of frames

output$ = "time"
output$ = output$ + tab$

for i from 1 to nformants
    formNum$ = string$(i)
    output$ = output$ + "F" + formNum$ + tab$ + "B" + formNum$ 
    if i <> nformants
        output$ = output$ + tab$
    endif
endfor
output$ = output$ + newline$

for f from 1 to frames
    t = Get time from frame number... 'f'
    t$ = fixed$(t, 3)
    output$ = output$ + t$ + tab$
    for j from 1 to nformants
        formant = Get value at time... 'j' 't' Hertz Linear
        formant$ = fixed$(formant, 2)

        bw = Get bandwidth at time... 'j' 't' Hertz Linear
        bw$ = fixed$(log10(bw), 4)
        output$ = output$ + formant$ + tab$ + bw$
        if j <> nformants
            output$ = output$ + tab$
        endif
    endfor
    output$ = output$ + newline$
endfor

echo 'output$'
