library(tidyverse)

min_probability <- 0.5
min_num_cases <- 10

uccs_schema <- read_csv('data/charges_2022-03-27_umich_2022-09-29/uccs_schema.csv')
umich_results <- read_csv('data/charges_2022-03-27_umich_2022-09-29/results.csv') %>%
  select(charge_name, uccs_code, probability) %>% 
  distinct()

charges_cleaned <- read_csv('data/output/charges_cleaned_unnormalized.csv')

charges_cleaned_uccs <- charges_cleaned %>%
  left_join(umich_results)

statute_uccs_mapping <- charges_cleaned_uccs %>%
  filter(!is.na(statute_chapter)) %>%
  group_by(statute_chapter, statute_section, statute_subsection, charge_name, uccs_code, probability) %>%
  summarise(num_cases_charge_name = n()) %>%
  ungroup() %>%
  group_by(statute_chapter, statute_section, statute_subsection, uccs_code) %>%
  mutate(num_cases_uccs = sum(num_cases_charge_name)) %>%
  ungroup() %>%
  group_by(statute_chapter, statute_section, statute_subsection) %>%
  filter(probability > min_probability) %>%
  arrange(desc(num_cases_uccs)) %>%
  summarise(statute_best_uccs_code = first(uccs_code),
            num_cases = first(num_cases_uccs)) %>%
  ungroup()

charges_cleaned_uccs_final <- charges_cleaned_uccs %>% 
  left_join(statute_uccs_mapping) %>%
  mutate(uccs_code = if_else(!is.na(statute_best_uccs_code) & (probability < min_probability) & (num_cases >= min_num_cases), statute_best_uccs_code, uccs_code)) %>%
  mutate(uccs_code = coalesce(uccs_code, statute_best_uccs_code)) %>%
  select(-statute_best_uccs_code, -num_cases) %>%
  left_join(uccs_schema)
         

write_csv(charges_cleaned_uccs_final, 'data/output/charges_cleaned_normalized.csv')
