form Variables
   sentence filename
   integer chunk
endform

# Constants
length = 0.005
padding = 0.1
maxf = 5000
f1ref = 500
f2ref = 1485
f3ref = 2475
f4ref = 3465
f5ref = 4455
freqcost = 1
bwcost = 1
transcost = 1

# Initialize output variable with column titles
output$ = "time" + tab$ + "H1_H2" + tab$ + "H1_A1" + tab$ + "H1_A2" + tab$+ "H1_A3" + newline$

# Load the specified sound file:
Read from file... 'filename$'
soundname$ = selected$ ("Sound", 1)
sound = selected("Sound")
select 'sound'
begin = Get start time
begin = begin + padding
end = Get end time
end = end - padding
Resample... 16000 50
sound_16khz = selected("Sound")
To Formant (burg)... 0.01 5 'maxf' 0.025 50
Rename... 'soundname$_beforetracking'
formant_beforetracking = selected("Formant")

xx = Get minimum number of formants
if xx > 2
   Track... 3 'f1ref' 'f2ref' 'f3ref' 3465 4455 'freqcost' 'bwcost' 'transcost'
else
   Track... 2 'f1ref' 'f2ref' 'f3ref' 3465 4455 'freqcost' 'bwcost' 'transcost'
endif

Rename... 'soundname$_aftertracking'
formant_aftertracking = selected("Formant")
select 'sound'
To Spectrogram... 'length' 4000 0.002 20 Gaussian
spectrogram = selected("Spectrogram")
select 'sound'
To Pitch... 0 60 350
pitch = selected("Pitch")
Interpolate
Rename... 'soundname$_interpolated'
pitch_interpolated = selected("Pitch")

# Divide the interval into chunks:
n_d = end - begin
for kounter from 1 to chunk
   n_seg = n_d / chunk
   n_md = begin + ((kounter - 1) * n_seg) + (n_seg / 2)

   # Get the f1,f2,f3 measurements.
   select 'formant_aftertracking'
   f1hzpt = Get value at time... 1 n_md Hertz Linear
   f2hzpt = Get value at time... 2 n_md Hertz Linear
   if f1hzpt = undefined or f2hzpt = undefined
      # do nothing skip the chunk
   else
      if xx > 2
         f3hzpt = Get value at time... 3 n_md Hertz Linear
      else
         f3hzpt = 0
      endif

      select 'sound_16khz'
      spectrum_begin = begin + ((kounter - 1) * n_seg)
      spectrum_end = begin + (kounter * n_seg)
      Extract part...  'spectrum_begin' 'spectrum_end' Hanning 1 no
      Rename... 'name$'_slice
      sound_16khz_slice = selected("Sound")
      To Spectrum (fft)
      spectrum = selected("Spectrum")
      To Ltas (1-to-1)
      ltas = selected("Ltas")

      select 'pitch_interpolated'
      n_f0md = Get value at time... 'n_md' Hertz Linear

      if n_f0md <> undefined

         p10_nf0md = 'n_f0md' / 10
         select 'ltas'
         lowerbh1 = 'n_f0md' - 'p10_nf0md'
         upperbh1 = 'n_f0md' + 'p10_nf0md'
         lowerbh2 = ('n_f0md' * 2) - ('p10_nf0md' * 2)
         upperbh2 = ('n_f0md' * 2) + ('p10_nf0md' * 2)
         h1db = Get maximum... 'lowerbh1' 'upperbh1' None
         h1hz = Get frequency of maximum... 'lowerbh1' 'upperbh1' None
         h2db = Get maximum... 'lowerbh2' 'upperbh2' None
         h2hz = Get frequency of maximum... 'lowerbh2' 'upperbh2' None
         rh1hz = round('h1hz')
         rh2hz = round('h2hz')

         # Get the a1, a2, a3 measurements.
         p10_f1hzpt = 'f1hzpt' / 10
         p10_f2hzpt = 'f2hzpt' / 10
         p10_f3hzpt = 'f3hzpt' / 10
         lowerba1 = 'f1hzpt' - 'p10_f1hzpt'
         upperba1 = 'f1hzpt' + 'p10_f1hzpt'
         lowerba2 = 'f2hzpt' - 'p10_f2hzpt'
         upperba2 = 'f2hzpt' + 'p10_f2hzpt'
         lowerba3 = 'f3hzpt' - 'p10_f3hzpt'
         upperba3 = 'f3hzpt' + 'p10_f3hzpt'
         a1db = Get maximum... 'lowerba1' 'upperba1' None
         a1hz = Get frequency of maximum... 'lowerba1' 'upperba1' None
         a2db = Get maximum... 'lowerba2' 'upperba2' None
         a2hz = Get frequency of maximum... 'lowerba2' 'upperba2' None
         a3db = Get maximum... 'lowerba3' 'upperba3' None
         a3hz = Get frequency of maximum... 'lowerba3' 'upperba3' None

         # Calculate potential voice quality correlates.
         h1mnh2 = 'h1db' - 'h2db'
         h1mna1 = 'h1db' - 'a1db'
         h1mna2 = 'h1db' - 'a2db'
         h1mna3 = 'h1db' - 'a3db'
         rh1mnh2 = round('h1mnh2')
         rh1mna1 = round('h1mna1')
         rh1mna2 = round('h1mna2')
         rh1mna3 = round('h1mna3')

      # Append result line
      spectrum_mid = ( spectrum_end + spectrum_begin ) /2
      output$ = output$ + string$(spectrum_mid) + tab$ + string$(h1mnh2) + tab$ + string$(h1mna1) + tab$ + string$(h1mna2) + tab$ + string$(h1mna3) + newline$
      else
      endif
   endif
endfor

# Print all results at once
echo 'output$'
select all
Remove
