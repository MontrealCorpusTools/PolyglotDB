library(tidyverse)
library(tuneR)

corpus_root <- '../ParlBleu-subset'

# Parameters for sampling
set.seed(76)
sample_size <- 5

# Parameters for Fast Track
fasttrack_dir <- './fasttrack'
split_sounds_by <- 'gender' # This can be the name of any column in the `vowels` dataframe
sound_file_padding <- 0.025


# Sampling ----------------------------------------------------------------

# Load the datasets
vowels <- read_csv('./output/vowels.csv')

# Get a sample for prototypes, balanced for phone and for gender
vowels_sample <- vowels %>%
  slice_sample(n = sample_size,
             by = c(phone, gender)) %>%
             arrange(phone, gender)

# Save the sample
vowels_sample %>%
  write_csv('./output/vowel_sample.csv')


# Creating directories and sound files for Fast Track ---------------------
resave_wav <- function (input_wav, output_wav, begin = 0, end = Inf, units = 'seconds') {
  wav <- readWave(input_wav, from = begin, to = end, units = units)
  writeWave(mono(wav), output_wav)
}

create_fasttrack_folder <- function (split_sounds = 'gender') {
  dir.create(fasttrack_dir)

  # Create subdirectories to run separate analyses on
  subdirectories <- vowels_sample %>%
    pull({{split_sounds}}) %>%
    unique() %>%
    paste(fasttrack_dir, ., 'sounds', sep = '/')

  subdirectories %>%
    lapply(dir.create, recursive = TRUE)

  # Create sound files containing just the vowel token (+ padding)
  vowels_sample <- vowels_sample %>%
    mutate(input_wav_path = paste(corpus_root,
                                  speaker,
                                  paste0(discourse, '.wav'),
                                  sep = '/'),
           output_wav_path = paste(fasttrack_dir,
                                   get(split_sounds),
                                   'sounds',
                                   # paste0(phone, '_', phone_id, '.wav'),
                                   paste0(phone_id, '.wav'),
                                   sep = '/'))

  for (row in 1:nrow(vowels_sample)) {
    curr_row <- vowels_sample[row,]

    resave_wav(curr_row$input_wav_path,
               curr_row$output_wav_path,
               begin = curr_row$phone_begin - sound_file_padding,
               end = curr_row$phone_end + sound_file_padding)
  }

}

create_fasttrack_folder(split_sounds_by)
