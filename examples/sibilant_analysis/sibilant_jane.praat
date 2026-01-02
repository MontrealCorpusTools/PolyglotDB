form Choices
sentence wav_file (leave unchanged to test in editor)
sentence options
sentence exclude
endform

# put the values of any parameters you need here
operations$ = "sibilant_jane(from_time=0.25,to_time=0.75,window=Hamming,filter_low=1000,filter_high=11000)"
interactive_session = 1

# these args are not used by PolyglotDB but are needed to keep the one_script sibilant code the same (they could be removed with a bit of effort)
transport.phone$ = "test"
transport.word$ = "test"

Read from file... 'wav_file$'
sound_name$ = selected$ ("Sound")
transport.phone_start = Get start time
transport.phone_end = Get end time
transport.duration = Get total duration
textgrid_name$ = "consonant"
#^this line may not actually work and/or is not needed

#output CSV file (unnecessary if your script doesn't produce one: below I've commented all the lines out that were using this, because it was giving me errors)
writePath$ = "C:\Users\samih\Documents\0_SPADE_labwork\"
outfile$ = "one_script_test.csv"
outfile$ = writePath$+outfile$
filedelete 'outfile$'



isComplete = 0
isHeader = 0
@makeMeasurements
isComplete = 1
@makeMeasurements


#define your procedure here
#arguments use the following format: var_name=value,var_name=value....

procedure sibilant_jane (.argString$)

    @parseArgs (.argString$)
    .from_time = 0.0
    .to_time = 1.0
    .window$ = "Rectangular"
    .filter_low = 0
    .filter_high = 22050
    .filtering = 0

    #PARSE THE ARGUMENTS TO THE PROCEDURE
    for i to parseArgs.n_args
        if parseArgs.var$[i] == "from_time"
            .from_time = number(parseArgs.val$[i])
        elif parseArgs.var$[i] == "to_time"
            .to_time = number(parseArgs.val$[i])
        elif parseArgs.var$[i] == "window"
            .window$ = parseArgs.val$[i]
        elif parseArgs.var$[i] == "filter_low"
            .filter_low = number(parseArgs.val$[i])
            .filtering = 1
        elif parseArgs.var$[i] == "filter_high"
            .filter_high = number(parseArgs.val$[i])
            .filtering = 1
        elif parseArgs.var$[i] == "filter_high"
            .filter_high = number(parseArgs.val$[i])
            .filtering = 1
        elif parseArgs.var$[i] != ""
            if isHeader == 1
                .unknown_var$ = parseArgs.var$[i]
                printline skipped unknown argument '.unknown_var$'
            endif
        endif
    endfor

    #THIS PROCEDURE WILL BE CALLED ONCE TO MAKE THE HEADER, ONCE AT THE END, AND ONCE FOR EACH MATCHING TOKEN...
    if isHeader = 1
        fileappend 'outfile$' ,peak,slope,cog,spread
	if interactive_session == 1
            echo
            printline peak slope cog spread
        endif
    elif isComplete == 1
	#printline FINISHED
    else
        #EXTRACT AND FILTER
        select Sound 'sound_name$'
        .extract_start = transport.phone_start + transport.duration*.from_time
        .extract_end = transport.phone_start + transport.duration*.to_time
        Extract part: '.extract_start', '.extract_end', .window$, 1.0, "yes"
        if .filtering == 1
            .newsamplerate = .filter_high*2
            Resample: '.filter_high'*2, 50
            Filter (pass Hann band): '.filter_low', '.filter_high', 100
        endif

        #MEASURE THE SPECTRUM
        To Spectrum... yes
        .cog = Get centre of gravity... 2
        .spread = Get standard deviation... 2

        #MEASURE THE LONG-TERM AVERAGE SPECTRUM
        To Ltas (1-to-1)
        .peak = Get frequency of maximum... 0 0 Parabolic
        .slope = Get slope... 0 1000 1000 4000 energy

        #WRITE TO THE OUTPUT FILE
#        fileappend 'outfile$' ,'.peak:3','.slope:3','.cog:3','.spread:3'

        #REMOVE OBJECTS
        select Sound 'sound_name$'_part
        if .filtering == 1
            plus Sound 'sound_name$'_part_'.newsamplerate'
            plus Sound 'sound_name$'_part_'.newsamplerate'_band
            plus Spectrum 'sound_name$'_part_'.newsamplerate'_band
            plus Ltas 'sound_name$'_part_'.newsamplerate'_band
        else
            plus Spectrum 'sound_name$'_part
            plus Ltas 'sound_name$'_part
        endif
        Remove

        #SHOW THE NUMBERS IF THIS IS RUNNING IN THE GUI
        if interactive_session == 1
            cog$ = fixed$(.cog, 4)
            peak$ = fixed$(.peak, 4)
            slope$ = fixed$(.slope, 4)
            spread$ = fixed$(.spread, 4)
            echo peak slope cog spread
            printline 'peak$' 'slope$' 'cog$' 'spread$'
        endif
    endif

endproc

##################################################################

#helpers taken from one_script

##################################################################

procedure parseOperations
    #SPLIT UP THE FUNCTIONS
    @split ("),", operations$)
    .n_ops = split.length
    if split.array$[1] != ""
        .n_ops = split.length
        for .i to .n_ops
            ops_array$[.i] = split.array$[.i]
        endfor

        for .i to .n_ops
            funWithArgs$ = ops_array$[.i]
            #SEPARATE THE FUNCTION NAME FROM ITS ARGUMENTS
            if index (funWithArgs$, "(") > 0
                @split ("(", funWithArgs$)
                funOnly$ = split.array$[1]
                argString$ = split.array$[2]
                argString$ = replace$(argString$, ")", "", 0)
                argString$ = replace$(argString$, ", ", ",", 0)

                if isHeader == 1
                    printline FUNCTION: 'funOnly$'
                endif

            endif

            @'funOnly$' (argString$)
        endfor
    endif
endproc

##################################################################

procedure parseArgs (.argString$)

    #SPLIT UP THE ARGUMENTS
    @split (",", argString$)
    .n_args = split.length
    for .i to .n_args
        .allArgs$[.i] = split.array$[.i]
    endfor

    for .i to .n_args
        @split ("=", .allArgs$[.i])
        .var$[.i] = split.array$[1]
        .val$[.i] = split.array$[2]
        #vv1$ = .var$[.i]
        #vv2$ = .val$[.i]
        #printline ***'vv1$'***'vv2$'***
        if isHeader == 1
            .currentVar$ = .var$[.i]
            .currentVal$ = .val$[.i]
            if .currentVar$ != ""
                printline --ARG: '.currentVar$' = '.currentVal$'
            endif
        endif
    endfor

endproc

############################################################

#Split Procedure Written by Jose J. Atria 20 Feb 2014
#http://www.ucl.ac.uk/~ucjt465/scripts/praat/split.proc.praat

procedure split (.sep$, .str$)
  .seplen = length(.sep$)
  .length = 0
  repeat
    .strlen = length(.str$)
    .sep = index(.str$, .sep$)
    if .sep > 0
      .part$ = left$(.str$, .sep-1)
      .str$ = mid$(.str$, .sep+.seplen, .strlen)
    else
      .part$ = .str$
    endif
    .length = .length+1
    .array$[.length] = .part$
  until .sep = 0
endproc

###################################################

procedure makeMeasurements

    if isHeader == 1
        fileappend 'outfile$' speaker,textgrid,sound,phonetier,word_id,token_id
        fileappend 'outfile$' ,leftword,word,rightword,phone,phonestart,phoneend,left2,left1,left,right,right1,right2

        @parseOperations (operations$)
    elif isComplete == 1
        @parseOperations (operations$)
    else
        word_id$ = textgrid_name$+"_"+"'phone_tier'"+"_"+transport.word$+"_"+"'transport.word_start:3'"
        token_id$ = textgrid_name$+"_"+"'phone_tier'"+"_"+transport.word$+"_"+transport.phone$+"_"+"'transport.phone_start:3'"

#        fileappend 'outfile$' 'speaker$','textgrid_name$','sound_name$','phone_tier','word_id$','token_id$'
#        fileappend 'outfile$' ,'transport.lastword$','transport.word$','transport.nextword$','transport.phone$','transport.phone_start:3','transport.phone_end:3','transport.lastphone2$','transport.lastphone1$','transport.lastphone$','transport.nextphone$','transport.nextphone1$','transport.nextphone2$'

        #VARIABLES AVAILABLE TO MEASUREMENT PROCEDURES:
        # - transport.phone$            the phone we're measuring
        # - transport.word$             the word it's in
        # - transport.phone_start       the time the phone starts
        # - transport.phone_end         the time the phone ends
        # - transport.duration          the duration of the target phone
        # - transport.lastphone$        the preceding phone
        # - transport.nextphone$        the following phone
        # - transport.lastphone1$       the phone preceding the preceding phone
        # - transport.nextphone1$       the phone following the following phone
        # - transport.lastphone2$       the third preceding phone
        # - transport.nextphone2$       the third following phone
        # - transport.lastphone_start   the time the preceding phone starts
        # - transport.nextphone_end     the time the following phone ends
        # - transport.word_start        the time the word starts
        # - transport.word_end          the time the word ends
        # - transport.lastword_start    the time the preceding word starts
        # - transport.nextword_end      the time the next word ends
        # - transport.lastword$         the preceding word
        # - transport.nextword$         the following word

        @parseOperations (operations$)

        print .
    endif
#    fileappend 'outfile$' 'newline$'

endproc
