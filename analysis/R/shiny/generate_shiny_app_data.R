library(tidyverse)
library(rjson)

min_num_cases <- 50

charges <- read_csv('data/output/charges_cleaned_normalized.csv')
events <- read_csv('data/output/events_cleaned.csv')

data <- events %>%
  filter(attorney %in% c("Retained", "Court Appointed")) %>%
  group_by(case_number) %>%
  mutate(num_attorney_types = n_distinct(attorney)) %>%
  ungroup() %>%
  filter(num_attorney_types == 1) %>%
  select(-num_attorney_types) %>%
  left_join(charges)

charges_levels <- data %>%
  filter(!is.na(uccs_code)) %>%
  select(case_number, charge_id, charge_desc, offense_type_desc, level) %>%
  distinct() %>%
  group_by(charge_desc, offense_type_desc, level) %>%
  summarise(n=n()) %>%
  ungroup() %>%
  filter(n >= min_num_cases) %>%
  select(-n)

write_csv(data, 'data/clean_charge_event_data.csv')
save(toJSON(data, 'data/clean_charge_event_data.json'))
saveRDS(data, 'analysis/hays-county-defense/app_data.rds')
saveRDS(charges_levels, 'analysis/hays-county-defense/charges_levels_app.rds')
