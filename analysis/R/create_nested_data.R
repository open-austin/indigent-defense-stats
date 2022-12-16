library(tidyverse)
library(rjson)

charges <- read_csv('data/output/charges_cleaned_normalized.csv', 
                    col_types = list(case_id = col_character(), 
                    statute_chapter = col_character(), charge_date = col_character(), 
                    earliest_charge_date = col_character()))
events <- read_csv('data/output/events_cleaned.csv', col_types = list(case_id = col_character(), event_date = col_character()))

cases <- events %>% 
  select(case_id, case_number, defense_attorney, attorney_type) %>% 
  left_join(select(charges, case_number, earliest_charge_date)) %>%
  distinct() %>%
  group_by(case_number) %>%
  # Remove cases with more than one case_id per case_number - it is rare and we are not reconciling these at this time
  filter(n_distinct(case_id) == 1) %>%
  ungroup() %>%
  filter(attorney_type %in% c('Retained', 'Court Appointed')) %>%
  arrange(case_number)

charges_dm <- charges %>%
  filter(case_number %in% cases_dm$case_number) %>%
  select(case_number, case_id, charge_id, charge_name, num_counts, 
         charge_date, is_primary_charge, level, statute, statute_chapter, 
         statute_section, statute_subsection, charge_desc, offense_category_desc,
         offense_type_desc)

events_dm <- events %>%
  filter(case_number %in% cases_dm$case_number) %>%
  select(case_number, case_id, event_date, event_name_formatted, is_evidence_of_representation) %>%
  filter(is_evidence_of_representation) %>%
  rename(event_name = event_name_formatted)
 
cases_events <- events_dm %>%
  left_join(cases_dm) %>%
  group_by(case_number) %>%
  summarise(has_evidence_of_representation = any(is_evidence_of_representation)) %>%
  ungroup()

cases_dm <- cases %>%
  left_join(cases_events)

events_nested <- events_dm %>% group_by(case_number, case_id) %>% nest() %>% rename(events = data)
charges_nested <- charges_dm %>% group_by(case_number, case_id) %>% nest() %>% rename(charges = data)

combined_nested <- cases_dm %>%
  left_join(charges_nested) %>%
  left_join(events_nested) %>%
  mutate(has_evidence_of_representation = coalesce(has_evidence_of_representation, FALSE))

combined_json <- jsonlite::toJSON(combined_nested)
combined_json_sample <- jsonlite::toJSON(combined_nested %>% sample_n(2000))

jsonlite::prettify(combined_json_sample)
write(combined_json, "data/output/nested_cases.json")
write(combined_json_sample, 'data/output/nested_cases_sample.json')


