form Variables
	sentence filename
	real begin
	real end
	integer channel
	real padding
	real timestep
	real windowlen
    integer minformants
	integer maxformants
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
r = segDur * (0.33)
r = r + begin
r$ = fixed$(r, 3)

final_output$ = ""

for nformants from minformants to maxformants
    selectObject: "Sound segment_of_interest"
    To Formant (burg)... 'timestep' 'nformants' 'ceiling' 'windowlen' 50


    output$ = ""

    for i from 1 to nformants
    	formNum$ = string$(i)
    	output$ = output$ + "F" + formNum$ + tab$ + "B" + formNum$
        if i <> nformants
            output$ = output$ + tab$
        endif
    endfor
    output$ = output$ + newline$


    output$ = output$

    for j from 1 to nformants
        formant = Get value at time... 'j' 'r' Hertz Linear
        formant$ = fixed$(formant, 2)

        bw = Get bandwidth at time... 'j' 'r' Hertz Linear
        bw$ = fixed$(bw, 2)

        output$ = output$ + formant$ + tab$ + bw$

        if i <> nformants
            output$ = output$ + tab$
        endif
    endfor

    output$ = output$ + newline$
    final_output$ = final_output$ + newline$ + output$
endfor

echo 'final_output$'
