library(tidyverse)

charges <- read_csv('data/output/charges_cleaned_normalized.csv')

events <- read_csv('data/events_2022-03-27.csv', col_select=-1) %>%
  mutate(event_date = lubridate::as_date(event_date),
         first_event_date = lubridate::as_date(first_event_date))

select_events <- charges %>%
  select(case_number, earliest_charge_date) %>%
  left_join(events) %>%
  group_by(case_number) %>%
  filter(all(event_date >= earliest_charge_date)) %>%
  ungroup()

good_motions <- c('Motion To Suppress', 'Motion to Reduce Bond', 
                  'Motion for Production', 'Motion For Speedy Trial', 
                  'Motion for Discovery', 'Motion In Limine')

events_cleaned <- select_events %>%
  mutate(event_name_formatted = str_to_title(tolower(event_name)),
         is_evidence_of_representation = event_name_formatted %in% good_motions) %>%
  rename(attorney_type = attorney) %>%
  mutate(attorney_type = if_else(is.na(attorney_type), 'None / Other', str_to_title(attorney_type))) %>%
  select(case_number, case_id, event_name, event_name_formatted, is_evidence_of_representation,
         event_date, attorney_type, defense_attorney) 

write_csv(events_cleaned, 'data/output/events_cleaned.csv')



