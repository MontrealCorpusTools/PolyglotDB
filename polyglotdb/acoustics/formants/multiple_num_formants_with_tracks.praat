form Variables
	sentence filename
	real begin
	real end
	integer channel
	real padding
	real timestep
	real windowlen
    positive minformants
	positive maxformants
	integer ceiling
    positive number_of_points
endform
#MULTIPLE_TRACKS
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


for ncoefficients from minformants*2 to maxformants*2
    halfcoefficients = ncoefficients / 2
    nformants = floor(halfcoefficients)

    selectObject: "Sound segment_of_interest"
    To Formant (burg)... 'timestep' 'halfcoefficients' 'ceiling' 'windowlen' 50


    output$ = "n_formants"+ tab$  + "'halfcoefficients'" + newline$
    output$ = output$ + "time" + tab$

    for i from 1 to nformants
    	formNum$ = string$(i)
    	output$ = output$ + "F" + formNum$ + tab$ + "B" + formNum$ 
        if i <> nformants
            output$ = output$ + tab$
        endif
    endfor
    output$ = output$ + newline$

    for n from 1 to number_of_points
        selectObject: "Formant segment_of_interest"
        t = n*(segDur/number_of_points) + begin
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
    final_output$ = final_output$ + output$ + newline$
endfor

echo 'final_output$'
