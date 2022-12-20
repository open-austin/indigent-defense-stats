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
  group_by(case_number) %>%
  # Remove cases with more than one case_id per case_number - it is rare and we are not reconciling these at this time
  filter(n_distinct(case_id) == 1) %>%
  ungroup() %>%
  filter(attorney_type %in% c('Retained', 'Court Appointed')) %>%
  arrange(case_number)

charges_dm <- charges %>%
  filter(case_number %in% cases$case_number) %>%
  select(case_number, case_id, charge_id, charge_desc, offense_type_desc,
         num_counts, charge_date, is_primary_charge, level, offense_type_desc) %>%
  rename(charge_category = offense_type_desc)

charges_by_case <- charges_dm %>%
  group_by(case_number, case_id) %>%
  arrange(charge_id) %>%
  summarise(charge_desc=list(charge_desc),
            charge_category = list(charge_category),
            charge_level = list(level))

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
  group_by(charge_desc, charge_category, level) %>%
  mutate(num_cases_charge = n()) %>%
  ungroup() %>%
  filter(num_cases_charge >= 50) %>%
  group_by(charge_desc, charge_category, attorney_type, has_evidence_of_representation) %>%
  summarise(count = n())

combined_nested <- cases_dm %>%
  left_join(charges_by_case) %>%
  left_join(events_by_case) %>%
  mutate(motions = map_if(motions, is.null, ~list()))

combined_json <- jsonlite::toJSON(combined_nested)
combined_json_sample <- jsonlite::toJSON(combined_nested %>% sample_n(2000))

jsonlite::prettify(combined_json_sample)
write(combined_json, "data/output/nested_cases.json")
write(combined_json_sample, 'data/output/nested_cases_sample.json')


