form Variables
	sentence filename
	real timestep
	real windowlen
	real nformants
	real ceiling
	real padding
endform

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
r = ((segEnd - segBeg) * (0.33))
r = r + segBeg
r$ = fixed$(r, 3)
#appendInfoLine: "Measurement time (a third through):"
#appendInfo: r$
#appendInfoLine: ""


output$ = output$ + r$

for i from 1 to nformants
    formant = Get value at time... 'i' 'r' Hertz Linear
    formant$ = fixed$(formant, 2)
    if formant = undefined
        #echo "error"
    endif
    bw = Get bandwidth at time... 'i' 'r' Hertz Linear
    bw$ = fixed$(bw, 2)
    output$ = output$ + tab$ + formant$ + tab$ + bw$
endfor
output$ = output$ + newline$

echo 'output$'
