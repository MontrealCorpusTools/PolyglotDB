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

# SELECT A SMALL CLIP AND MAKE AN LTAS FOR MEASURING FORMANT AMPLITUDE
max_fb_for_a = 300
selectObject: "Sound segment_of_interest"
sound_samplerate = Get sampling frequency
#ltas_bandwidth = ceiling(sound_samplerate/2048)
ltas_bandwidth = ceiling(sound_samplerate/512)
ltas_window_start = max(begin,r-0.025)
ltas_window_end = min(r+0.025,end)
Extract part: ltas_window_start, ltas_window_end, "rectangular", 1, "yes"
Rename: "amplitude_window"
To Ltas: ltas_bandwidth



#for nformants from minformants to maxformants
for ncoefficients from minformants*2 to maxformants*2
    halfcoefficients = ncoefficients / 2
    nformants = floor(halfcoefficients)

    selectObject: "Sound segment_of_interest"
    To Formant (burg)... 'timestep' 'halfcoefficients' 'ceiling' 'windowlen' 50


    output$ = ""
    output$ = output$ + "num_formants" + tab$

    for i from 1 to nformants
    	formNum$ = string$(i)
    	output$ = output$ + "F" + formNum$ + tab$ + "B" + formNum$ + tab$ + "A" + formNum$
        if i <> nformants
            output$ = output$ + tab$
        endif
    endfor
    output$ = output$ + newline$

    output$ = output$ + "'halfcoefficients'" + tab$

    for j from 1 to nformants
        selectObject: "Formant segment_of_interest"
        formant = Get value at time... 'j' 'r' Hertz Linear
        formant$ = fixed$(formant, 2)

        bw = Get bandwidth at time... 'j' 'r' Hertz Linear
        bw$ = fixed$(log10(bw), 4)

        if formant == undefined
            amp$ = "'undefined'"      
        else
            # LIMIT THE DISTANCE AWAY FROM THE CENTER TO LOOK FOR A MAXIMUM (EVEN IF THE BANDWIDTH IS LARGE)
            halfwindow_up_for_a = min(bw, max_fb_for_a)/2
            halfwindow_down_for_a = halfwindow_up_for_a

            # DON'T GO MORE THAN HALFWAY TOWARD THE CENTER OF ANOTHER FORMANT
            if j < nformants
                formant_up = Get value at time... j+1 r Hertz Linear
                if formant_up != undefined
                    halfwindow_up_for_a = min(halfwindow_up_for_a, (formant_up-formant)/2)
                endif
            else
                formant_up = formant + 500
            endif

            if formant_up != undefined
                formant_up = formant + 500
            endif

            if j == 1
                #TRY TO AVOID F0
                formant_down = max(formant/2, 200)
            else
                formant_down = Get value at time... j-1 r Hertz Linear
            endif
            if formant_down != undefined
                halfwindow_down_for_a = min(halfwindow_down_for_a, (formant-formant_down)/2)
            endif

            arange_low = formant - halfwindow_down_for_a
            arange_high = formant + halfwindow_up_for_a

            selectObject: "Ltas amplitude_window"
            amp = Get maximum: arange_low, arange_high, "None"

            amp$ = fixed$(amp, 4)

        endif

        #fileappend /phon/MontrealCorpusTools/spadedebug.txt time 'r' 'halfcoefficients' F'j' 'arange_low:0'-'arange_high:0' 'formant$' 'bw$' 'amp$''newline$'

        output$ = output$ + formant$ + tab$ + bw$ + tab$ + amp$

        if i <> nformants
            output$ = output$ + tab$
        endif
    endfor

    output$ = output$ + newline$
    final_output$ = final_output$ + newline$ + output$
endfor

echo 'final_output$'
