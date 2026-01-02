## Script to create SPADE datasets of multitaper normalized spectrum measurements.
##
## This script requires an auxiliary/ subdirectory to run, which is
## essentially identical to the spectRum and wavefoRm packages by
## Patrick Riedy (which we do not have permission to distribute):
## https://github.com/patrickreidy/spectRum
## https://github.com/patrickreidy/wavefoRm
##
## Input: a SPADE-format sibilants dataset file, such as
## spade-Buckeye_sibilants.csv
##
## Output: a file of multi-taper normalized-spectrum measurements,
## such as spade-Buckeye_mts_sibilants_normalized.csv
##
## see README.txt for more detail
##
## Authors:Jeff Mielke, Jane Stuart-Smith, James Tanner, Michael Goodale,
## working from an original script by Patrick Reidy
## Date:    2018-2020



started_at <- date()

library(ggplot2)
library(magrittr)
library(multitaper)
library(tibble)
library(tuneR)
library(doParallel)
library(foreach)
library(argparse)
library(stringr)
library(svMisc)

## Process comamand-line arguments
parser <- ArgumentParser(description = "Generate multitaper measurements")
parser$add_argument("input_file", help = "CSV file containing observations to measure")
parser$add_argument("sound_dir", help = "Path to the top-level directory containg the audio files")
parser$add_argument("output_dir", help = "Directory to write the mts-measured CSV file")
parser$add_argument("--directories", "-d", help = "The audio file contains speaker-level subdirectories", action = "store_true", default = FALSE)
parser$add_argument("--numbers", "-n", help = "Speaker names are defined with numbers (integers) instead of letters", action = "store_true", default = FALSE)
parser$add_argument("--wav_column", "-w", help = "The name of the column listing the wav file", default = "choose")
parser$add_argument("--speakers", "-s", help = "Use speaker codes for audio file names (same as \"-w speaker\")", action = "store_true", default = FALSE)
parser$add_argument("--rate", "-r", help = "Sampling rate to downsample to before measuring", default = "22050")
parser$add_argument("--procedure", "-p", help = "Measurement procedure to apply to the CSV file", default = "sibilant")
parser$add_argument("--frame", "-f", help = "Window length to use for measurements (in seconds)", default = "0.020")
parser$add_argument("--alpha", "-a", help = "Preemphasis alpha", default = "0")
parser$add_argument("--normalize", "-z", help = "Normalize spectra based on utterances and silences", action = "store_true", default = FALSE)
parser$add_argument("--measure_at", "-m", help = "List of timepoints to calculate MTS at", type = "double", nargs = "*", default = seq(0, 1, length.out = 17))
parser$add_argument("--n_cores", "-j", help = "Number of CPU cores to use", type = "integer", default = 8)

args <- parser$parse_args()

preemphasis_alpha <- as.numeric(args$alpha)

print (paste('procedure:',args$procedure))
# The R files in the ./auxiliary subdirectory of this demo define a handful of
# S4 classes, generics, and methods that wrap functionality from the tuneR and
# multitaper packages.
# You'll need to source the R files in this order because, e.g., definitions
# in later files depend on S4 classes defined in earlier files.
source('./auxiliary/Waveform.R') # For reading .wav files.
source('./auxiliary/Spectrum.R') # Base methods shared by all spectrum-like objects.
source('./auxiliary/Periodogram.R') # For estimating spectra using the periodogram.
source('./auxiliary/DPSS.R') # Windowing functions for multitaper spectra.
source('./auxiliary/Multitaper.R') # For estimating spectra using multitaper method.

# https://stackoverflow.com/questions/7824912/max-and-min-functions-that-are-similar-to-colmeans
colMax <- function (colData) {
    apply(colData, MARGIN=c(2), max)
}

colMin <- function (colData) {
    apply(colData, MARGIN=c(2), min)
}

colSD <- function (colData) {
    apply(colData, MARGIN=c(2), sd)
}

rowMax <- function (colData) {
    apply(colData, MARGIN=c(1), max)
}

colQuantile <- function (colData, q=50, na.rm=FALSE) {
    my_quantile <- function(x) quantile(x, q, na.rm=na.rm)
    apply(colData, MARGIN=c(2), my_quantile)
}



get_file_path <- function(corpus_data, row, sound_file_directory, subdirs){

    #JM: this seems like a more straightforward way to open and downsample, but I may be misunderstanding why it was originally done differently
    # print (paste0("one_window.x <- readWave(filename = ",file_path,", from = ",file_midpoint," - 0.0125, to = ",file_midpoint," + 0.0125, units='seconds')"))

    #JM: to handle column names of csv files made by sibilant.py:
    if (args$speakers){
        sound_file <- paste0(corpus_data[row, "speaker"], '.wav')
    }else if (args$wav_column!='choose'){
        sound_file <- paste0(gsub(".WAV", "", corpus_data[row, args$wav_column]), '.wav')
    }else if ('sound_file_name'%in%names(corpus_data)){
        sound_file <- paste0(gsub(".WAV", "", corpus_data[row, "sound_file_name"]), '.wav')
    # }else if ('recording'%in%names(corpus_data)){
    #     sound_file <- paste0(corpus_data[row, "recording"], '.wav')
    }else{
        sound_file <- paste0(corpus_data[row, "discourse"], '.wav')
    }
    sound_file <- gsub('.wav.wav','.wav',sound_file) # because some of them already have .wav at the end
    if (subdirs){
       file.path(sound_file_directory, corpus_data[row, "speaker"], sound_file)
    }else{
       file.path(sound_file_directory, sound_file)
    }
}

getWaveForClip <- function(file_path, clip_start, clip_end, downsample_to=22050){

    window.x <- readWave(filename = file_path, from = clip_start, to = clip_end, units='seconds')
    original_rate <- window.x@samp.rate

    window.x <- downsample(window.x, downsample_to)
    # if it's a 32-bit wav file it will be opened as a WaveMC object which has the .Data slot instead of left and possibly also right
    if (window.x@bit==32) window.x <- Wave(window.x)

    # ensure that the number of samples is the minimum for this window_length (relevant if window_length * samp.rate is not a whole number)
    window.x@left <- window.x@left[1:floor(as.numeric(args$frame)*window.x@samp.rate)]
    if (length(window.x@right)){
        window.x@right <- window.x@right[1:floor(as.numeric(args$frame)*window.x@samp.rate)]
    }
    list(wave=window.x, original_rate=original_rate)
}

waveToOneSpectrum <- function(clip, k=8, nw=4){
    wave_clip <- Waveform(clip)

    if (preemphasis_alpha>0){
        wave_clip <- PreEmphasize(wave_clip, preemphasis_alpha)
    }

    #Estimate the spectrum of one_window using the multitaper method. no preemphasis or zeropadding.
    wave_clip_spectrum <-
    wave_clip %>%
    #PreEmphasize(alpha = 0.5) %>% # optional
    #ZeroPad(lengthOut = sampleRate(one_window)) %>% # again, optional
    Multitaper(k = 8, nw = 4)
    # print(length(frequencies(wave_clip_spectrum)))
    wave_clip_spectrum
}

spectralSlope <- function(mts, minHz = -Inf, maxHz = Inf) {
    .indices <- (function(.f) {which(minHz < .f & .f < maxHz)})(frequencies(mts))
    .freqs <- frequencies(mts)[.indices] #%>% (function(.x) {(.x - mean(.x)) / sd(.x)})
    .values <- ((function(.v) {10 * log10(.v)})(values(mts)))[.indices] #%>% (function(.x) {(.x - mean(.x)) / sd(.x)})
    .spec <- data.frame(x = .freqs, y = .values)
    if (sum(!is.na(.spec))){
    # .coeffs <- coef(lm(data = .spec, formula = y ~ x))
        return(coef(lm(data = .spec, formula = y ~ x))[2])
    }else{
        return(NA)
    }
}

meanAmp <- function(x, minHz = min(freq(x)), maxHz = max(freq(x)), scale = 'dB', reference = NULL) {
    .vals <- values(x)
    if (scale == 'dB') {
      if (is.null(reference))
        .vals <- 10*log10(.vals/max(.vals))
      else if (reference == 'max')
        .vals <- 10*log10(.vals/max(.vals))
      else if (reference == 'min')
        .vals <- 10*log10(.vals/min(.vals))
      else if (is.numeric(reference))
        .vals <- 10*log10(.vals/reference)
      else
        message('Reference power must be argument when using dB scale.')
    }
    .vals <- .vals[which(minHz <= frequencies(x) & frequencies(x) <= maxHz)]
    return(mean(.vals))
}

F_M <- function(one_window_spectrum, sibilant, gender) {
  F_M_ranges <- data.frame(sblnt = c('s', 's', 'ʃ', 'ʃ'),
                           gndr = c('female', 'male', 'female', 'male'),
                           min = c(3000, 3000, 2000, 2000),
                           max = c(8000, 7000, 4000, 4000))

  F_M_range <- F_M_ranges %>%
    dplyr::filter(sblnt == sibilant, gndr == gender)

  F_M_min <- F_M_range$min
  F_M_max <- F_M_range$max

  return(peakHz(one_window_spectrum, minHz = F_M_min, maxHz = F_M_max))
}

measureAcoustics <- function(one_window_spectrum, corpus_data, row) {
  corpus_data[row, "spectral_peak_full"] <- peakHz(one_window_spectrum, minHz = 1000, maxHz = 11000)
  corpus_data[row, "spectral_cog"] <- centroid(one_window_spectrum, scale = "linear", minHz = 1000, maxHz = 11000)
  corpus_data[row, "F_M"] <- F_M(one_window_spectrum, corpus_data[row, "phone"], corpus_data[row, "gender"])

  #JM: store the multitaper values
  corpus_data[row, mts_colnames[1:length(one_window_spectrum@values)]] <- one_window_spectrum@values
  #JM: how to get frequencies and values out
  # frequencies <- seq(from = 0, to = one_window_spectrum@nyquist, by = one_window_spectrum@binWidth)
  # values <- one_window_spectrum@values
  corpus_data
}

parallelized <- TRUE
n_cores <- args$n_cores

## Get the corpus name from the input file
if (args$procedure=='sibilant'){
    # corpus_name <- str_match(args$input_file, "[\\w+\\/]*?([A-Za-z0-9_-]*)\\_sibilants\\.csv")[,2]
    corpus_name <- str_match(args$input_file, "[\\w+\\/]*?([A-Za-z0-9_-]*)\\_sibilants(_full)?.csv")[,2]
}else if (args$procedure=='mean_spectrum'){
    corpus_name <- str_match(args$input_file, "[\\w+\\/]*?([A-Za-z0-9_-]*)\\_utterances\\.csv")[,2]
}else{
    corpus_name <- 'unknown'
}

cat("Corpus name:", "\t", corpus_name, "\n")

message("Reading corpus data...")
corpus_data_original <- read.csv(args$input_file, colClasses = c(speaker = "character"))

# ML: Added for dynamic data (repeats each row n times, adds a measurement point column)
if (args$procedure == "sibilant" & length(args$measure_at) > 1) {
  message("Expanding corpus data for dynamic measures...")
  corpus_data <- corpus_data_original[rep(seq_len(nrow(corpus_data_original)), each = length(args$measure_at)), ]
  corpus_data$measurement <- args$measure_at
} else {
  corpus_data <- corpus_data_original

  if (args$procedure == "sibilant") {
    corpus_data$measurement <- args$measure_at
  }
}
# End of new code


if (args$numbers){
    corpus_data$discourse <- sprintf("%03d",corpus_data$discourse)
}

if(parallelized) {
    registerDoParallel(n_cores)
}else{
    n_cores = 1
}

##########################################################################
### LOOK AT ONE TOKEN PER DISCOURSE AND INFER DETAILS ABOUT THE CORPUS ###
##########################################################################

message('inspecting discourses...')
all_multitapers <- list()
n_values <- 0

for (sp in setdiff(unique(corpus_data$speaker),NA)){
    print(sp)
    all_multitapers[[sp]] <- list()
    subdata <- subset(corpus_data, speaker==sp)
    for (disc in unique(subdata$discourse)){
        subsubdata <- subset(subdata, discourse==disc)

        file_path <- get_file_path(subsubdata, 1, args$sound_dir, args$directories)

        if (args$procedure=='sibilant'){
            begin <- subsubdata[1, "phone_begin"]
            end <- subsubdata[1, "phone_end"]
        }else if(args$procedure=='mean_spectrum'){
            begin <- subsubdata[1, "utterance_begin"]
            end <- subsubdata[1, "utterance_end"]
        }else{
            print(paste0('UNKNOWN PROCEDURE: ***',args$procedure,'***'))
        }
        file_midpoint <- begin + (end-begin) / 2

        tryCatch(
            {
                wave_info <- getWaveForClip(file_path, file_midpoint - as.numeric(args$frame)/2, file_midpoint + as.numeric(args$frame)/2, as.numeric(args$rate))
                one_window <- wave_info$wave
                original_rate <- wave_info$original_rate
                samp.rate_default <- one_window@samp.rate
                one_window_spectrum<- waveToOneSpectrum(one_window)

                #save all the multitaper information except for the values
                all_multitapers[[sp]][[disc]] <- list(values = NULL,
                                                      frequencies = seq(from = 0, to = one_window_spectrum@nyquist, by = one_window_spectrum@binWidth),
                                                      binWidth = one_window_spectrum@binWidth,
                                                      nyquist = one_window_spectrum@nyquist,
                                                      k = one_window_spectrum@k,
                                                      nw = one_window_spectrum@nw)

                n_values <- max(n_values, length(one_window_spectrum@values))

            },
            error=function(cond){
                if (file.exists(file_path)){
                    message_text <- paste("[inspect discourses] could not load waveform data from file at specified time:", file_path, file_midpoint - as.numeric(args$frame)/2)
                }else{
                    message_text <- paste("[inspect discourses] file does not seem to exist:", file_path)
                }
                message(message_text)
                write(message_text,file="mts_logfile.txt",append=TRUE)
            }
        )

    }
}

mts_colnames <- paste0('S',1:n_values)
corpus_data$original_rate <- NA
corpus_data$downsampled_to <- NA
corpus_data[,mts_colnames] <- NA

####################################################################################################################################################
### MEAN SPECTRUM MEASUREMENT PROCEDURE                                                                                                          ###
####################################################################################################################################################

sample_from_utterances <- function(utterances, frame=0.35, clip_n=1000){

    utterances$left <- utterances$begin+as.numeric(frame)/2
    utterances$right <- utterances$end-as.numeric(frame)/2
    utterances$length <- utterances$right - utterances$left
    utterances <- subset(utterances, length>0)

    utterances$cumul_start <- cumsum(utterances$length) - utterances$length
    utterances$cumul_end <- cumsum(utterances$length)

    sample_times_cumul <- seq(0, utterances$cumul_end[nrow(utterances)], length.out=clip_n)
    sample_times_real <- c(utterances[1,'left'])

    for (row in 1:nrow(utterances)){
        sample_times_real <- c(sample_times_real,
                               sample_times_cumul[sample_times_cumul>utterances[row,'cumul_start'] & sample_times_cumul<=utterances[row,'cumul_end']] - utterances[row,'cumul_start'] + utterances[row,'left'])
    }
    sample_times_real
}



if (args$procedure=='mean_spectrum'){

    message('MEASURING MEAN SPECTRUM')

    clip_n <- 1000
    frame <- as.numeric(args$frame)

    amps_sampled <- list(speaker=c(), discourse=c(), freqs=c(),
                         meanvals=c(), maxvals=c(), minvals=c(), sdvals=c(),
                         meanamps=c(), maxamps=c(), minamps=c(), sdamps=c(),
                         meanamps2=c(), maxamps2=c(), minamps2=c(),
                         vals_10=c(), vals_20=c(), vals_30=c(),
                         vals_40=c(), vals_50=c(), vals_60=c(),
                         vals_70=c(), vals_80=c(), vals_90=c(),
                         amps_10=c(), amps_20=c(), amps_30=c(),
                         amps_40=c(), amps_50=c(), amps_60=c(),
                         amps_70=c(), amps_80=c(), amps_90=c(),
                         meannonvals=c(), maxnonvals=c(), minnonvals=c(), sdnonvals=c(),
                         meannonamps=c(), maxnonamps=c(), minnonamps=c(), sdnonamps=c(),
                         meannonamps2=c(), maxnonamps2=c(), minnonamps2=c(),
                         nonvals_10=c(), nonvals_20=c(), nonvals_30=c(),
                         nonvals_40=c(), nonvals_50=c(), nonvals_60=c(),
                         nonvals_70=c(), nonvals_80=c(), nonvals_90=c(),
                         nonamps_10=c(), nonamps_20=c(), nonamps_30=c(),
                         nonamps_40=c(), nonamps_50=c(), nonamps_60=c(),
                         nonamps_70=c(), nonamps_80=c(), nonamps_90=c()
                         )

    clip_n <- 1000

    # corpus_data <- read.csv('/projects/spade/datasets/datasets_utterances/spade-Scottish-Polish_utterances.csv')
    corpus_data <- corpus_data[order(corpus_data$utterance_begin),]
    corpus_data <- corpus_data[order(corpus_data$discourse),]
    corpus_data <- corpus_data[order(corpus_data$speaker),]

    for (sp in unique(corpus_data$speaker)){
    # for (sp in c('3164')){
        print(c(corpus_name,sp,'meanampsmean'))

        sp_data <- subset(corpus_data, speaker==sp)

        # all_discourses_sample_data <- c()

        for (disc in unique(sp_data$discourse)){
            print(disc)
            disc_data <- subset(sp_data, discourse==disc)
            # print(disc_data[1:40])
            # print(nrow(disc_data))
            # print('that was disc_data')
            file_path <- get_file_path(disc_data, row=1, args$sound_dir, args$directories)
            # file_path <- '/projects/spade/repo/git/spade-Scottish-Polish/audio_and_transcripts/Adam_and_Evelyn.wav'

            # find 1000 clips within the sound file

            # first make tables of all the utterances and non-utterances between them
            utterances <- data.frame(begin=disc_data$utterance_begin, end=disc_data$utterance_end)
            nonutterances <- data.frame(begin=utterances$end[-nrow(utterances)], end=utterances$begin[-1])
            # print(utterances)
            utterance_sample_times_real <- sample_from_utterances(utterances, frame=frame, clip_n=clip_n)

            # this is to catch cases where there is only one utterance in a discourse (so no following)
            if (nrow(nonutterances)){
                nonutterance_sample_times_real <- sample_from_utterances(nonutterances, frame=frame, clip_n=clip_n)
                sample_data <- rbind(data.frame(utterance=TRUE, clip_start=utterance_sample_times_real-frame/2, clip_end=utterance_sample_times_real+frame/2),
                                     data.frame(utterance=FALSE, clip_start=nonutterance_sample_times_real-frame/2, clip_end=nonutterance_sample_times_real+frame/2))
            }else{
                sample_data <- data.frame(utterance=TRUE, clip_start=utterance_sample_times_real-frame/2, clip_end=utterance_sample_times_real+frame/2)
            }
            disc_mts_colnames <- mts_colnames[1:length(all_multitapers[[sp]][[disc]]$frequencies)]
            # sample_data[,mts_colnames] <- NA
            sample_data[,disc_mts_colnames] <- NA

            # PARALLEL PROCESSING START
            batch_indices <- rep(0:(n_cores-1), each=(nrow(sample_data) %/% n_cores))
            batch_indices <- c(rep(0, nrow(sample_data)-length(batch_indices)), batch_indices)
            batches <- split(1:nrow(sample_data), batch_indices)

            sample_data <- foreach(batch=batches, .combine=rbind) %dopar% {
                sample_data <- sample_data[batch, ]
                for (row in 1:nrow(sample_data)){

                    tryCatch(
                        {
                            wave_info <- getWaveForClip(file_path, sample_data[row,'clip_start'], sample_data[row,'clip_end'], as.numeric(args$rate))
                            # wave_info <- getWaveForClip(file_path, sample_data[row,'clip_start'], sample_data[row,'clip_end'], as.numeric(44100))
                            one_window <- wave_info$wave
                            one_window_spectrum <- waveToOneSpectrum(one_window)
                            sample_data[row,disc_mts_colnames] <- one_window_spectrum@values
                        },
                        error=function(cond){
                            if (file.exists(file_path)){
                                message_text <- paste("[mean_spectrum] could not load waveform data from file at specified time:", file_path, sample_data[row,'clip_start'])
                            }else{
                                message_text <- paste("[mean_spectrum] file does not seem to exist:", file_path)
                            }
                            message(message_text)

                            write(message_text,file="mts_logfile.txt",append=TRUE)
                        }
                    )

                }
                sample_data
            }

            stopImplicitCluster()
            # PARALLEL PROCESSING END

            message(paste(sum(!is.na(sample_data[,disc_mts_colnames[1]])), 'of', clip_n*2, 'clips measured successfully'))

            # amps_sampled <- list(speaker=c(), discourse=c(), freqs=c(),
            #                      meanvals=c(), maxvals=c(), minvals=c(), sdvals=c(),
            #                      meanamps=c(), maxamps=c(), minamps=c(), sdamps=c(),
            #                      meanamps2=c(), maxamps2=c(), minamps2=c(),
            #                      vals_10=c(), vals_20=c(), vals_30=c(),
            #                      vals_40=c(), vals_50=c(), vals_60=c(),
            #                      vals_70=c(), vals_80=c(), vals_90=c(),
            #                      amps_10=c(), amps_20=c(), amps_30=c(),
            #                      amps_40=c(), amps_50=c(), amps_60=c(),
            #                      amps_70=c(), amps_80=c(), amps_90=c(),
            #                      meannonvals=c(), maxnonvals=c(), minnonvals=c(), sdnonvals=c(),
            #                      meannonamps=c(), maxnonamps=c(), minnonamps=c(), sdnonamps=c(),
            #                      meannonamps2=c(), maxnonamps2=c(), minnonamps2=c(),
            #                      nonvals_10=c(), nonvals_20=c(), nonvals_30=c(),
            #                      nonvals_40=c(), nonvals_50=c(), nonvals_60=c(),
            #                      nonvals_70=c(), nonvals_80=c(), nonvals_90=c(),
            #                      nonamps_10=c(), nonamps_20=c(), nonamps_30=c(),
            #                      nonamps_40=c(), nonamps_50=c(), nonamps_60=c(),
            #                      nonamps_70=c(), nonamps_80=c(), nonamps_90=c()
            #                      )

            all_utterance_values <- sample_data[sample_data$utterance,disc_mts_colnames]
            all_nonutterance_values <- sample_data[!sample_data$utterance,disc_mts_colnames]

            maxvalue <- max(all_utterance_values)
            # print (all_nonutterance_values)
            print (sp)
            print (nrow(all_nonutterance_values))

            if (sum(!is.na(all_utterance_values))){
                amps_sampled$speaker <- c(amps_sampled$speaker, sp)
                amps_sampled$discourse <- c(amps_sampled$discourse, disc)

                freqs <- all_multitapers[[sp]][[disc]]$frequencies
                meanvals <- colMeans(all_utterance_values)
                maxvals <- colMax(all_utterance_values)
                minvals <- colMin(all_utterance_values)
                sdvals <- colSD(all_utterance_values)

                if (!nrow(all_nonutterance_values)){
                    print('no rows 1')
                    meannonvals <- rep(NA, length(freqs))
                    maxnonvals <- rep(NA, length(freqs))
                    minnonvals <- rep(NA, length(freqs))
                    sdnonvals <- rep(NA, length(freqs))
                }else{
                    print('rows 1')
                    meannonvals <- colMeans(all_nonutterance_values)
                    maxnonvals <- colMax(all_nonutterance_values)
                    minnonvals <- colMin(all_nonutterance_values)
                    sdnonvals <- colSD(all_nonutterance_values)
                }
                amps_sampled$freqs <- rbind(amps_sampled$freqs, freqs)
                amps_sampled$meanvals <- rbind(amps_sampled$meanvals, meanvals)
                amps_sampled$maxvals <- rbind(amps_sampled$maxvals, maxvals)
                amps_sampled$minvals <- rbind(amps_sampled$minvals, minvals)
                amps_sampled$sdvals <- rbind(amps_sampled$sdvals, sdvals)

                amps_sampled$meannonvals <- rbind(amps_sampled$meannonvals, meannonvals)
                amps_sampled$maxnonvals <- rbind(amps_sampled$maxnonvals, maxnonvals)
                amps_sampled$minnonvals <- rbind(amps_sampled$minnonvals, minnonvals)
                amps_sampled$sdnonvals <- rbind(amps_sampled$sdnonvals, sdnonvals)

                disc_all_samples_amps <- t(apply(all_utterance_values, 1, function(x) 10*log10(x/maxvalue)))
                sdamps <- colSD(disc_all_samples_amps)
                amps_sampled$sdamps <- rbind(amps_sampled$sdamps, sdamps)
                # disc_all_samples_amps <- t(apply(all_utterance_values, 1, function(x) 10*log10(x/maxvalue)))

                if (!nrow(all_nonutterance_values)){
                    # print('no rows 2')
                    disc_all_samples_nonamps <- rep(NA, length(freqs))
                    sdnonamps <- rep(NA, length(freqs))
                    meannonamps <- rep(NA, length(freqs))
                    maxnonamps <- rep(NA, length(freqs))
                    minnonamps <- rep(NA, length(freqs))
                    meannonamps2 <- rep(NA, length(freqs))
                    maxnonamps2 <- rep(NA, length(freqs))
                    minnonamps2 <- rep(NA, length(freqs))
                }else{
                    # print('rows 2')
                    disc_all_samples_nonamps <- t(apply(all_nonutterance_values, 1, function(x) 10*log10(x/maxvalue)))
                    # disc_all_samples_nonamps <- t(apply(all_nonutterance_values, 1, function(x) 10*log10(x/maxvalue)))
                    sdnonamps <- colSD(disc_all_samples_nonamps)
                    meannonamps <- colMeans(disc_all_samples_nonamps)
                    maxnonamps <- colMax(disc_all_samples_nonamps)
                    minnonamps <- colMin(disc_all_samples_nonamps)
                    meannonamps2 <- 10*log10(meannonvals/maxvalue)
                    maxnonamps2 <- 10*log10(maxnonvals/maxvalue)
                    minnonamps2 <- 10*log10(minnonvals/maxvalue)
                }

                amps_sampled$sdnonamps <- rbind(amps_sampled$sdnonamps, sdnonamps)

                meanamps <- colMeans(disc_all_samples_amps)
                maxamps <- colMax(disc_all_samples_amps)
                minamps <- colMin(disc_all_samples_amps)

                meanamps2 <- 10*log10(meanvals/maxvalue)
                maxamps2 <- 10*log10(maxvals/maxvalue)
                minamps2 <- 10*log10(minvals/maxvalue)


                # if (sp=='exsmcrea'){
                #     print (freqs)
                #     write.csv(all_utterance_values, file='exsmcrea_allvalues.csv')
                # }

                # print (c(maxvalue, max(maxvals)))
                # print (summary(maxvals))
                # print (summary(maxamps))

                amps_sampled$meanamps <- rbind(amps_sampled$meanamps, meanamps)
                amps_sampled$maxamps <- rbind(amps_sampled$maxamps, maxamps)
                amps_sampled$minamps <- rbind(amps_sampled$minamps, minamps)
                amps_sampled$meanamps2 <- rbind(amps_sampled$meanamps2, meanamps2)
                amps_sampled$maxamps2 <- rbind(amps_sampled$maxamps2, maxamps2)
                amps_sampled$minamps2 <- rbind(amps_sampled$minamps2, minamps2)

                amps_sampled$meannonamps <- rbind(amps_sampled$meannonamps, meannonamps)
                amps_sampled$maxnonamps <- rbind(amps_sampled$maxnonamps, maxnonamps)
                amps_sampled$minnonamps <- rbind(amps_sampled$minnonamps, minnonamps)
                amps_sampled$meannonamps2 <- rbind(amps_sampled$meannonamps2, meannonamps2)
                amps_sampled$maxnonamps2 <- rbind(amps_sampled$maxnonamps2, maxnonamps2)
                amps_sampled$minnonamps2 <- rbind(amps_sampled$minnonamps2, minnonamps2)

                for (q in seq(0.1,0.9,0.1)){
                    vals_label <- paste('vals',q*100,sep='_')
                    amps_label <- paste('amps',q*100,sep='_')
                    nonvals_label <- paste('nonvals',q*100,sep='_')
                    nonamps_label <- paste('nonamps',q*100,sep='_')
                    amps_sampled[[vals_label]] <- rbind(amps_sampled[[vals_label]], colQuantile(all_utterance_values, q, na.rm=T))
                    amps_sampled[[amps_label]] <- rbind(amps_sampled[[amps_label]], colQuantile(disc_all_samples_amps, q, na.rm=T))

                    if (!nrow(all_nonutterance_values)){
                        # print('no rows 3')
                        amps_sampled[[nonvals_label]] <- rbind(amps_sampled[[nonvals_label]], rep(NA, length(freqs)))
                        amps_sampled[[nonamps_label]] <- rbind(amps_sampled[[nonamps_label]], rep(NA, length(freqs)))
                    }else{
                        # print('rows 3')
                        amps_sampled[[nonvals_label]] <- rbind(amps_sampled[[nonvals_label]], colQuantile(all_nonutterance_values, q, na.rm=T))
                        amps_sampled[[nonamps_label]] <- rbind(amps_sampled[[nonamps_label]], colQuantile(disc_all_samples_nonamps, q, na.rm=T))
                    }

                }
                print(length(amps_sampled$sp))
                print(nrow(amps_sampled$vals_10))
                print(nrow(amps_sampled$nonvals_10))
                # print(length(amps_sampled$nonvals_10))
                # print (amps_sampled$nonvals_10[1:5,])
                # print (summary(amps_sampled$nonvals_10))
            }
        }
        # print(c(length(amps_sampled$amps_10), length(amps_sampled$nonamps_10)))
    }
    save(amps_sampled, file=paste0(args$output_dir, corpus_name,"_mean_spectrum",".RData"))
    #######################################################
}

####################################################################################################################################################
### SIBILANT MEASUREMENT PROCEDURE                                                                                                               ###
####################################################################################################################################################

if (args$procedure=='sibilant'){

    message('MEASURING SIBILANTS')

    correct_slope_values <- function(freqs){
        freqs500 <- freqs
        freqs500[freqs500<500] <- 500
        slope_correct <- 6*(log2(500)-log2(freqs500))
        slope_correct_values <- (10^slope_correct)^0.1
        slope_correct_values
    }

    norm2b <- function(x, freqs=freqs, lowref, highref){
        xnorm2b <- (x-lowref) / (highref-lowref)
        xnorm2b <- xnorm2b*correct_slope_values(freqs)
        if (args$normalize){
        #     # xnorm2b <- xnorm2b*max(highref)/max(xnorm2b)
            xnorm2b <- xnorm2b*100000000
        }
        xnorm2b[xnorm2b<0.000001] <- 0.000001
        xnorm2b
    }


    ##########################
    ### MEASURE ALL TOKENS ###
    ##########################

    if(args$normalize){
        print('loading previously measured mean spectra')
        load(paste0(args$output_dir, corpus_name,"_mean_spectrum",".RData"))
    }

    message('measuring sibilant tokens...')
    #Split 0:nrows into (roughly) equal sized batches that are in order
    # ML: Modified to allow for dynamic data (don't break up tokens across batches)
    # Use original corpus to determine batches, then simply repeat indicies n times before splitting

    batch_indices <- rep(0:(n_cores-1), each=(nrow(corpus_data_original) %/% n_cores))
    batch_indices <- c(rep(0, nrow(corpus_data_original)-length(batch_indices)), batch_indices)
    batch_indices <- rep(batch_indices, each = length(args$measure_at))
    batches <- split(1:nrow(corpus_data), batch_indices)
    # End modifications

    corpus_data <- foreach(batch=batches, .combine=rbind) %dopar% {
        corpus_data <- corpus_data[batch, ]

        for (row in 1:nrow(corpus_data)){
            #cat(round(row/nrow(corpus_data),6), "\r")

            # ML: Added for dynamic data (only open the file once per token)
            if (length(args$measure_at) > 1) {
              if ((row - 1) %% length(args$measure_at) == 0) {
                file_path <- get_file_path(corpus_data, row, args$sound_dir, args$directories)
              }
            } else {
              file_path <- get_file_path(corpus_data, row, args$sound_dir, args$directories)
            }

            begin <- corpus_data[row, "phone_begin"]
            end <- corpus_data[row, "phone_end"]

            # Actually the measurement point
            file_midpoint <- begin + (end - begin) * corpus_data[row, "measurement"]
            # End

            tryCatch(
                {
                    wave_info <- getWaveForClip(file_path, file_midpoint - as.numeric(args$frame)/2, file_midpoint + as.numeric(args$frame)/2, as.numeric(args$rate))
                    # wave_info <- getWaveForClip(corpus_data, row=row, args$sound_dir, args$directories, as.numeric(args$rate))
                    one_window <- wave_info$wave
                    corpus_data[row,'original_rate'] <- wave_info$original_rate
                    corpus_data[row,'downsampled_to'] <- min(as.numeric(args$rate), wave_info$original_rate)
                    if (one_window@samp.rate != samp.rate_default){
                        message_text <- paste("corpus has inconsistent sample rate:", corpus_name, one_window@samp.rate, samp.rate_default)
                        # message(message_text)
                        write(message_text,file="mts_logfile.txt",append=TRUE)
                    }
                    one_window_spectrum <- waveToOneSpectrum(one_window)

                    if (args$normalize){
                        # print('normalizing')

                        one_window_spectrum_norm2b <- one_window_spectrum
                        disc_row <- which(amps_sampled$speaker==corpus_data[row,'speaker']&amps_sampled$discourse==corpus_data[row,'discourse'])
                        sp_rows <- which(amps_sampled$speaker==corpus_data[row,'speaker'])
                        v90 <- amps_sampled$vals_90[disc_row,]
                        # try using nonvals (from non-utterances) for this discourse
                        if (sum(!is.na(amps_sampled$nonvals_10[disc_row,]))){
                            # print('yes')
                            n10 <- amps_sampled$nonvals_10[disc_row,]
                        # then try using nonvals from other discourses for this speaker
                        }else if(length(sp_rows)>1){
                            if (sum(!is.na(colMeans(amps_sampled$nonvals_10[sp_rows,])))){
                                # print('maybe')
                                n10 <- colMeans(amps_sampled$nonvals_10[sp_rows,])
                                message_text <- paste("used nonamps from other discourses for:", file_path)
                                message(message_text)
                                write(message_text,file="mts_logfile.txt",append=TRUE)
                            }else{
                                # print ('no?')
                                n10 <- amps_sampled$vals_10[disc_row,]
                                message_text <- paste("used amps in place of nonamps for:", file_path)
                                message(message_text)
                                write(message_text,file="mts_logfile.txt",append=TRUE)
                            }
                        # then just use vals from the speech itself
                        }else{
                            # print('no')
                            n10 <- amps_sampled$vals_10[disc_row,]
                            message_text <- paste("used amps in place of nonamps for:", file_path)
                            message(message_text)
                            write(message_text,file="mts_logfile.txt",append=TRUE)
                        }
                        one_window_spectrum_norm2b@values <- norm2b(one_window_spectrum@values, frequencies(one_window_spectrum), n10, v90)


                        corpus_data <- measureAcoustics(one_window_spectrum_norm2b, corpus_data, row)
                    }else{
                        corpus_data <- measureAcoustics(one_window_spectrum, corpus_data, row)
                    }
                },
                error=function(cond){
                    if (file.exists(file_path)){
                        message_text <- paste("could not load waveform data from file at specified time:", file_path, begin)
                    # }else if(is.na(corpus_data[row, "spectral_lower_slope"])){
                    #     message_text <- paste("problem calculating spectral_slope", file_path, begin)
                    }else{
                        message_text <- paste("file does not seem to exist:", file_path)
                    }
                    message(message_text)
                    write(message_text,file="mts_logfile.txt",append=TRUE)
                }
            )
        }
        corpus_data
    }

    stopImplicitCluster()

    message(' preparing to write sibilant output...')
    # output the multitaper spectrum values
    for (sp in unique(corpus_data$speaker)){
        subdata <- subset(corpus_data, speaker==sp)
        for (disc in unique(subdata$discourse)){
            subsubdata <- subset(subdata, discourse==disc)
            disc_mts_colnames <- mts_colnames[1:length(all_multitapers[[sp]][[disc]]$frequencies)]
            all_multitapers[[sp]][[disc]]$values <- subsubdata[,disc_mts_colnames]
        }
    }
    # remove the multitaper spectrum values from corpus_data before writing the csv file
    corpus_data <- corpus_data[,setdiff(colnames(corpus_data),mts_colnames)]

    ########################
    ### WRITE THE OUTPUT ###
    ########################

    if(args$normalize){
        if (grepl('sibilants_full', args$input_file)){
        write.csv(corpus_data, paste0(args$output_dir, corpus_name,"_mts_sibilants_full_normalized",".csv"), quote = FALSE, row.names = FALSE)
        save(all_multitapers, file=paste0(args$output_dir, corpus_name,"_mts_sibilants_full_normalized",".RData"))
        }else{
        write.csv(corpus_data, paste0(args$output_dir, corpus_name,"_mts_sibilants_normalized",".csv"), quote = FALSE, row.names = FALSE)
        save(all_multitapers, file=paste0(args$output_dir, corpus_name,"_mts_sibilants_normalized",".RData"))
        }
    }else{
        if (grepl('sibilants_full', args$input_file)){
            write.csv(corpus_data, paste0(args$output_dir, corpus_name,"_mts_sibilants_full",".csv"), quote = FALSE, row.names = FALSE)
            save(all_multitapers, file=paste0(args$output_dir, corpus_name,"_mts_sibilants_full",".RData"))
        }else{
            write.csv(corpus_data, paste0(args$output_dir, corpus_name,"_mts_sibilants",".csv"), quote = FALSE, row.names = FALSE)
            save(all_multitapers, file=paste0(args$output_dir, corpus_name,"_mts_sibilants",".RData"))
        }
    }
    print (paste('successfully measured', sum(!is.na(corpus_data$spectral_cog)), 'out of',nrow(corpus_data),'tokens (',round(100*sum(!is.na(corpus_data$spectral_cog))/nrow(corpus_data),2),'% )'))
}

finished_at <- date()
print (paste('started', started_at))
print (paste('finished', finished_at))
