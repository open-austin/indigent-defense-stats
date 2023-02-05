library(tidyverse)
library(rjson)

charges <- read_csv('data/output/charges_cleaned_normalized.csv', 
                    col_types = list(case_id = col_character(), 
                    statute_chapter = col_character(), charge_date = col_character(), 
                    earliest_charge_date = col_character()))
events <- read_csv('data/output/events_cleaned.csv', col_types = list(case_id = col_character(), event_date = col_character()))

cases <- events %>% 
  select(case_id, case_number, attorney_type) %>% 
  left_join(select(charges, case_number, earliest_charge_date)) %>%
  distinct() %>%
  arrange(case_number)

charges_dm <- charges %>%
  filter(case_number %in% cases$case_number) %>%
  select(case_number, case_id, charge_id, charge_desc, offense_type_desc,
         num_counts, charge_date, is_primary_charge, level, offense_type_desc) %>%
  rename(charge_category = offense_type_desc,
         charge_name = charge_desc,
         charge_level = level)

charges_nested <- charges_dm %>%
  nest(charges=c('charge_id', 'charge_name', 'charge_category', 'charge_date', 'charge_level', 'is_primary_charge', 'num_counts'))

events_dm <- events %>%
  filter(case_number %in% cases$case_number) %>%
  select(case_number, case_id, event_date, event_name_formatted, is_evidence_of_representation) %>%
  filter(is_evidence_of_representation) %>%
  rename(event_name = event_name_formatted)

events_by_case <- events_dm %>%
  group_by(case_number, case_id) %>%
  summarise(motions=list(unique(event_name)))
 
cases_events <- events_dm %>%
  left_join(cases) %>%
  group_by(case_number) %>%
  summarise(has_evidence_of_representation = any(is_evidence_of_representation)) %>%
  ungroup()

cases_dm <- cases %>%
  left_join(cases_events) %>%
  mutate(has_evidence_of_representation = coalesce(has_evidence_of_representation, FALSE))

combined <- cases_dm %>%
  left_join(charges_dm)

combined_by_charge <- combined %>%
  filter(attorney_type %in% c('Retained', 'Court Appointed')) %>%
  mutate(charge_level = case_when(str_detect(charge_level, 'Felony') ~ 'Felony',
                                  str_detect(charge_level, 'Misdemeanor') ~ 'Misdemeanor')) %>%
  group_by(charge_name, charge_level, attorney_type, has_evidence_of_representation) %>%
  summarise(count = n()) %>%
  ungroup() %>%
  group_by(charge_name, charge_level) %>%
  filter(min(count) >= 30) %>%
  summarise(lr_num = max(count[has_evidence_of_representation & (attorney_type == 'Retained')]) / max(count[(attorney_type == 'Retained')]),
            lr_denom = max(count[has_evidence_of_representation & (attorney_type == 'Court Appointed')]) / max(count[(attorney_type == 'Court Appointed')]),
            likelihood_ratio = lr_num / lr_denom) %>%
  ungroup()

plot_data <- combined_by_charge %>%
  mutate(charge = paste(charge_name, '-', charge_level)) %>%
  select(charge, likelihood_ratio) %>%
  arrange(desc(likelihood_ratio)) %>%
  mutate(charge = fct_inorder(charge))

ggplot(data=plot_data, aes(x=charge, y=likelihood_ratio)) +
  geom_bar(stat = 'identity', fill = 'dodgerblue3') +
  scale_x_discrete(labels = function(x) str_wrap(x, width = 14)) +
  geom_hline(yintercept = 1) +
  labs(x = '\nCharge', y='Likelihood Ratio\n', title='') +
  theme(axis.text.x = element_text(angle=90))

combined_nested <- cases_dm %>%
  left_join(charges_nested) %>%
  left_join(events_by_case) %>%
  mutate(motions = map_if(motions, is.null, ~list()))

combined_json <- jsonlite::toJSON(combined_nested)
combined_json_sample <- jsonlite::toJSON(combined_nested %>% sample_n(2000))

jsonlite::prettify(combined_json_sample)
write(combined_json, "data/output/clean_cases_vis.json")
write(combined_json_sample, 'data/output/clean_cases_vis_sample.json')




