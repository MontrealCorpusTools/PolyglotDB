library(tidyverse)

measurement_point <- 0.33
proto_parameters <- c('F1', 'F2', 'F3', 'B1', 'B2', 'B3')
formants_path <- './output/vowel_sample_fasttrack.csv'
prototypes_path <- './output/generated_prototypes.csv'

# Load the formant data (from Fast Track)
formant_data <- read_csv(formants_path)

formant_data <- formant_data %>%
  mutate(time.rel = time / (phone_end - phone_begin),
         .after = time)

formant_data <- formant_data %>%
  summarize(across(c(F1:B3),
                ~ approx(x = time.rel,
                         y = .x,
                         xout = measurement_point)$y),
            .by = c(phone_id, phone)) %>%
  mutate(time.rel = measurement_point)

formant_data <- formant_data %>%
  mutate(across(c(B1, B2, B3),
                 ~ log10(.x)))

formant_data <- formant_data[, c('phone', proto_parameters)]

# Calculate the means and covariance matrices
corpus_means_for_phones <- formant_data %>%
  group_by(phone) %>%
  summarize(across(where(is.numeric), mean))

corpus_covmats_list <- list()

for (p in unique(formant_data$phone)) {
  corpus_covmats_list[[p]] <- formant_data %>%
    filter(phone == p) %>%
    select(F1:B3) %>%
    cov()
}

# Format the covariance matrices for the output and combine them with the means
corpus_covmats <- c()

for(p in names(corpus_covmats_list)){
  phone_matrix <- corpus_covmats_list[[p]]

  corpus_covmats <- rbind(corpus_covmats, data.frame(phone = p, phone_matrix))
}

phones_for_polyglot <- rbind(data.frame(type = 'means', corpus_means_for_phones), data.frame(type = 'matrix', corpus_covmats))

names(phones_for_polyglot)[names(phones_for_polyglot) %in% proto_parameters] <-
  paste(names(phones_for_polyglot)[names(phones_for_polyglot) %in% proto_parameters], measurement_point, sep='_')

# Make the prototype files
phones_for_polyglot %>%
  write_csv(prototypes_path)
