library(tidyverse)

tokens <- read_csv('./output/vowel_sample.csv')
sound_file_padding <- 0.025

# Create a single dataframe for all the acoustics
acoustics <- data.frame()
winners <- data.frame()

sound_dirs <- list.dirs('./fasttrack', recursive = FALSE)

for (d in sound_dirs) {
  winners_temp <- read_csv(paste(d, 'winners.csv', sep = '/'), na = '')

  winners <- winners %>%
    rbind(winners_temp)

  d <- d %>%
    paste0('/csvs')

  sounds_list <- list.files(d)

  for (sound in sounds_list) {
    sound_csv <- read_csv(paste(d, sound, sep = '/')) %>%
      # mutate(phone_id = str_split_i(sound, '_', 2) %>% str_split_i('\\.', 1),
      mutate(phone_id = sound %>% str_split_i('\\.', 1),
             .before = everything())

    sound_csv <- sound_csv %>%
      mutate(time = time - sound_file_padding)

    acoustics <- acoustics %>%
      rbind(sound_csv)
  }
}

tokens_with_acoustics <- tokens %>%
  right_join(acoustics,
            by = 'phone_id') %>%
  rename_with(~ str_to_upper(.x), .cols = f1:b3) # Make the column names uppercase for consistency with other scripts

tokens_with_acoustics %>% write_csv('./output/vowel_sample_fasttrack.csv')
