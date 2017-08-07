form Variables
	sentence filename
	real timestep
	real windowlen
    real minformants
	real maxformants
	real ceiling
	real padding
endform

    #echo 'filename$'
    #echo 'timestep'
    #echo 'windowlen'
    #echo 'minformants'
    #echo 'maxformants'
    #echo 'ceiling'
#writeInfoLine: "Looking at: "
#appendInfoLine: 'filename$'

final_output$ = ""

for nformants from minformants to maxformants
    #echo 'Measuring with'
    #echo 'nformants'
    #echo 'formants.'
    #appendInfoLine: "Measuring with this many nformants: "
    #appendInfo: 'nformants'
    #appendInfoLine: ""
    Read from file... 'filename$'
    To Formant (burg)... 'timestep' 'nformants' 'ceiling' 'windowlen' 50
    frames = Get number of frames


    output$ = "time"

    for i from 1 to nformants
    	formNum$ = string$(i)
    	output$ = output$ + tab$ + "F" + formNum$ + tab$ + "B" + formNum$
    endfor
    output$ = output$ + newline$

    #Measure a third of the way through
    segBeg = Get start time
		segBeg = segBeg + padding
    #appendInfoLine: "Start time:"
    #appendInfo: segBeg
    #appendInfoLine: ""

    segEnd = Get end time
		segEnd = segEnd - padding
    #appendInfoLine: "End time:"
    #appendInfo: segEnd
    #appendInfoLine: ""

    segDur = segEnd - segBeg
    #r = ((segEnd - segBeg) * (0.33)) + segBeg
		r = ((segEnd - segBeg) * (0.33))
		r = r + segBeg
    r$ = fixed$(r, 3)
    #appendInfoLine: "Measurement time (a third through):"
    #appendInfo: r$
    #appendInfoLine: ""

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
