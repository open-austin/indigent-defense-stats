library(tidyverse)
library(rjson)

charges <- read_csv('data/output/charges_cleaned_normalized.csv', 
                    col_types = list(statute_chapter = col_character(), charge_date = col_character(), earliest_charge_date = col_character()))
events <- read_csv('data/output/events_cleaned.csv', col_types = list(event_date = col_character()))

cases <- events %>% 
  select(case_number, attorney_type) %>% 
  left_join(select(charges, case_number, earliest_charge_date)) %>%
  distinct() %>%
  arrange(case_number)

charges_dm <- charges %>%
  filter(case_number %in% cases$case_number) %>%
  select(case_number, charge_id, charge_desc, offense_type_desc,
         num_counts, charge_date, is_primary_charge, level, offense_type_desc) %>%
  rename(charge_category = offense_type_desc,
         charge_name = charge_desc,
         charge_level = level) %>% 
  filter(is_primary_charge) 

events_dm <- events %>%
  filter(case_number %in% cases$case_number) %>%
  select(case_number, event_date, event_name_formatted, is_evidence_of_representation) %>%
  filter(is_evidence_of_representation) %>%
  rename(event_name = event_name_formatted)

events_by_case <- events_dm %>%
  group_by(case_number) %>%
  summarise(motions=list(unique(event_name)))
 
cases_events <- events_dm %>%
  left_join(cases) %>%
  group_by(case_number) %>%
  summarise(has_evidence_of_representation = any(is_evidence_of_representation)) %>%
  ungroup()

cases_dm <- cases %>%
  left_join(cases_events) %>%
  mutate(has_evidence_of_representation = coalesce(has_evidence_of_representation, FALSE))

vis_data <- cases_dm %>%
  left_join(charges_dm) %>%
  select(case_number, attorney_type, charge_date, charge_name, charge_category, charge_level, has_evidence_of_representation) %>%
  left_join(events_by_case) %>%
  mutate(motions = map_if(motions, is.null, ~list()))

vis_json <- jsonlite::toJSON(vis_data)
vis_json_sample <- jsonlite::toJSON(vis_data %>% sample_n(2000))

jsonlite::prettify(vis_json_sample)
write(vis_json, "data/output/clean_cases_vis.json")




