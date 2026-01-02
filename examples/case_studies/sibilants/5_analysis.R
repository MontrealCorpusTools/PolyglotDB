library(tidyverse)
theme_set(theme_bw())

# Colourblind-friendly colours from Okabe & Ito (https://jfly.uni-koeln.de/color/#pallet)
oi_colours <- c('#E69F00', '#56B4E9', '#009E73')

# Load the data
sibilants <- read_csv('./output/ParlBleu-subset_mts_sibilants_normalized.csv')

# Make the figure
sibilant_measures <- sibilants %>%
  pivot_longer(cols = c(spectral_peak_full:F_M),
               names_to = 'acoustics',
               values_to = 'value') %>%
  mutate(acoustics = acoustics %>% fct_relevel(c('spectral_peak_full', 'spectral_cog', 'F_M'))) %>%
  ggplot(aes(x = phone, y = value, colour = acoustics)) +
  geom_boxplot(position = position_dodge(width = 0.85)) +
  facet_wrap(~interaction(speaker, gender %>% str_to_title(), sep = ', '),
             scales = 'free_x') +
  labs(x = NULL,
       y = 'Frequency (Hz)',
       colour = 'Acoustic measure') +
  scale_colour_discrete(labels = c('Peak', 'COG', 'F_M'), type = oi_colours) +
  theme(legend.position = 'bottom')

sibilant_measures

sibilant_measures %>% ggsave('./sibilant_measures.png', ., width = 1600, height = 1200, unit = 'px')
