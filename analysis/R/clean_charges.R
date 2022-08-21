library(tidyverse)

# Constants

min_year <- 2000

# Excluded - Misdemeanor C, Misdemeanor Traffic (low severity)
#            Misdemeanor Unassigned, Misdemeanor Class Appeal, Felony Unassigned
allowed_levels <- c('Misdemeanor A', 'Misdemeanor B', 'State Jail Felony', 
                    'Third Degree Felony', 'Second Degree Felony',
                    'First Degree Felony', 'Capital Felony')

count_extraction_regex <- '(\\s|\\[|^)+(CT|COUNT)[ \\s.]+.*?(\\]|$)'


charges <- read_csv("~/Desktop/Projects/open-austin/data/charges.csv", col_select=-1, col_types = list(case_id = col_character())) %>%
  mutate(charge_date = lubridate::as_date(charge_date))

cases <- charges %>%
  group_by(case_id, case_number) %>%
  summarise(earliest_charge_date = min(charge_date),
            latest_charge_date = max(charge_date))

cases_different_dates <- charges %>%
  inner_join(filter(cases, earliest_charge_date != latest_charge_date)) %>%
  arrange(desc(case_id), charge_id)

charges_filtered <- charges %>%
  filter(lubridate::year(charge_date) >= min_year) %>%
  filter(level %in% allowed_levels) %>%
  mutate(charge_name = trimws(toupper(charge_name))) %>%
  mutate(charge_count = str_extract(charge_name, count_extraction_regex),
         # Kinda hacky, but don't remove the count if we have mistakenly captured the entire charge name
         charge_name_original = charge_name,
         charge_name = case_when(charge_name == charge_count ~ charge_name,
                                 is.na(charge_count) ~ charge_name,
                                 charge_name != charge_count ~ trimws(str_remove(charge_name, count_extraction_regex))))

distinct_charges <- charges_filtered %>%
  group_by(case_id, case_number, charge_name, charge_date, statute, level) %>%
  summarise(num_counts = n_distinct(charge_id),
            charge_id = min(charge_id)) %>%
  ungroup() %>%
  arrange(case_id, charge_id)
  