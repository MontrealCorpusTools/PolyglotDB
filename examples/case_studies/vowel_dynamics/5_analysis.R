library(tidyverse)
theme_set(theme_bw()) # Sets the ggplot2 theme

vowels <- read_csv('output/formants-refined.csv') # Change this path as needed

# Average each phone first within, then across speakers (because data is imbalanced)
phone_means <- vowels %>%
  filter(time >= 0.25 & time <= 0.75) %>%
  summarize(across(F1:F3,
                   ~ mean(.x, na.rm = TRUE)),
            .by = c(phone, speaker, gender, time)) %>%
  summarize(across(F1:F3,
                   ~ mean(.x, na.rm = TRUE)),
            .by = c(phone, time))

# Make the vowel space plot
vowel_space <- phone_means %>%
  ggplot(aes(x = F2, y = F1)) +
  geom_path(aes(colour = phone), linewidth = 0.5, arrow = arrow(length = unit(0.1, 'cm'), type = 'closed')) +
  geom_label(data = phone_means %>% slice_min(time, by = phone), aes(label = phone), size = 1.5) +
  scale_x_reverse() +
  scale_y_reverse() +
  labs(x = 'F2 (Hz)',
       y = 'F1 (Hz)') +
  theme(legend.position = 'none')

vowel_space

# Save the plot
vowel_space %>% ggsave('./vowel-space.png', ., width = 800, height = 600, unit = 'px')
