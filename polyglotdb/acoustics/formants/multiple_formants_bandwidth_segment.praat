form Variables
	sentence filename
	real begin
	real end
	integer channel
	real timestep
	real windowlen
    integer minformants
	integer maxformants
	integer ceiling
	real padding
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
    #echo 'Measuring with'
    #echo 'nformants'
    #echo 'formants.'
    #appendInfoLine: "Measuring with this many nformants: "
    #appendInfo: 'nformants'
    #appendInfoLine: ""
    selectObject: "Sound segment_of_interest"
    To Formant (burg)... 'timestep' 'nformants' 'ceiling' 'windowlen' 50


    output$ = "time"

    for i from 1 to nformants
    	formNum$ = string$(i)
    	output$ = output$ + tab$ + "F" + formNum$ + tab$ + "B" + formNum$
    endfor
    output$ = output$ + newline$


    output$ = output$ + r$

    for j from 1 to nformants
        #appendInfoLine: "Getting F"
        #appendInfo: 'j'
        #appendInfoLine: ""
        formant = Get value at time... 'j' 'r' Hertz Linear
        formant$ = fixed$(formant, 2)
        if formant = undefined
            #echo "formant error"
            #formant$ = "undef"
        endif
        bw = Get bandwidth at time... 'j' 'r' Hertz Linear
        bw$ = fixed$(bw, 2)
        if bw = undefined
            #echo "bandwidth error"
            #bw$ = "undef"
        endif
        output$ = output$ + tab$ + formant$ + tab$ + bw$
        #appendInfoLine: "End of loop, finishing nformants "
        #appendInfo: 'j'
        #appendInfoLine: ""
    endfor

    output$ = output$ + newline$
    final_output$ = final_output$ + newline$ + output$
    #echo 'output$'
    #appendInfoLine: 'output$'
    #echo 'final_output$'
endfor

#final_output$ = "hello world"
echo 'final_output$'
