library(tidyverse)

# Constants

min_year <- 2005

allowed_levels <- c('Misdemeanor A', 'Misdemeanor B', 'State Jail Felony', 
                    'First Degree Felony', 'Second Degree Felony', 'Third Degree Felony', 
                    'Capital Felony')

# Filter out minor offenses and outlying levels that we aren't concerned with
disallowed_levels_minor <- c('Misdemeanor C', 'Misdemeanor Traffic')
disallowed_levels_misc <- c('Felony Unassigned', 'Misdemeanor Unassigned', 'Misdemeanor Class Appeal')

valid_roman_numeral <- '(M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))'
count_base <- '(CN*TS*|COUNTS*)'
opening_marker_first_pass <- '(\\[|\\()(.*\\s)?'
opening_marker_second_pass <- '((\\s|\\-|\\.|\\:)*\\b)'
closing_marker_first_pass <- '(\\]|\\))'
closing_marker_second_pass <- '(\\s|\\.|\\-|\\:|$)+'
post_count_spacing_first_pass <- '(\\s|\\.|\\-|\\:|$)*'
post_count_spacing_second_pass <- '(\\s|\\.|\\-|\\:|$)+'
count_remainder_first_pass <- '.*?'
count_remainder_second_pass <- glue::glue('([0-9]+|{valid_roman_numeral})((\\s*)(\\-|\\&|\\,)(\\s*)([0-9]+|{valid_roman_numeral}))*')

count_extraction_regex_first_pass <- as.character(glue::glue('{opening_marker_first_pass}{count_base}{post_count_spacing_first_pass}{count_remainder_first_pass}{closing_marker_first_pass}'))
count_extraction_regex_second_pass <- as.character(glue::glue('{opening_marker_second_pass}{count_base}{post_count_spacing_second_pass}{count_remainder_second_pass}{closing_marker_second_pass}'))
statute_split_regex <- '[\\.\\(\\-\\)\\ ]'

charge_abbrev_lookup <- c(POM = 'POSSESSION OF MARIJUANA', POCS = 'POSSESSION OF A CONTROLLED SUBSTANCE', 
                          MTAG = 'MOTION TO ADJUDICATE GUILT', MTRP = 'MOTION TO REVOKE PROBATION',
                          EOCA = 'ENGAGING IN ORGANIZED CRIMINAL ACTIVITY', AADW = 'AGGRAVATED ASSAULT WITH A DEADLY WEAPON',
                          BOH = 'BURGLARY OF HABITATION', AAPO = 'AGGRAVATED ASSAULT ON A PEACE OFFICER',
                          UUMV = 'UNAUTHORIZED USE OF A MOTOR VEHICLE', FTA = 'FAILURE TO APPEAR')
charge_abbrev_lookup_regex <- charge_abbrev_lookup
names(charge_abbrev_lookup_regex) <- paste0('\\b', names(charge_abbrev_lookup), '\\b')

# Keep FTA, delete rest
post_charge_events_regex <- c('MOTION TO ADJUDICATE|MOTION (TO )*REVOKE|FAIL(URE)* TO APPEAR')
failure_to_appear_regex <- c('FAIL(URE)* TO APPEAR')

# Read in Odyssey charge data
charges <- read_csv("data/charges_2022-03-27.csv", col_select=-1, col_types = list(case_id = col_character())) %>%
  mutate(charge_date = lubridate::as_date(charge_date),
         level_group = case_when(str_detect(level, 'Felony') ~ 'Felony',
                                 str_detect(level, 'Misdemeanor') ~ 'Misdemeanor'))

cases <- charges %>%
  group_by(case_number, case_id) %>%
  summarise(num_distinct_charges = n_distinct(charge_id),
            earliest_charge_date = min(charge_date),
            latest_charge_date = max(charge_date),
            has_allowed_level = any(level %in% allowed_levels)) %>%
  ungroup()

# Filter cases based on eligibility (year and charge level)
cases_filtered <- cases %>%
  filter(lubridate::year(earliest_charge_date) >= min_year) %>%
  filter(has_allowed_level)

select_case_charges <- charges %>%
  filter(case_number %in% cases_filtered$case_number) %>%
  filter(level %in% allowed_levels) %>%
  mutate(level = factor(level, levels = allowed_levels),
         charge_name = trimws(toupper(charge_name)),
         is_post_charge_event = str_detect(charge_name, post_charge_events_regex),
         is_failure_to_appear = str_detect(charge_name, failure_to_appear_regex)) %>%
  arrange(case_number, charge_id)

# Extract count data from charge name using regular expressions. This will allow us to normalize the charge names with better accuracy.
charges_count_extracted <- select_case_charges %>%
  mutate(charge_count_extracted_first_pass = str_extract(charge_name, count_extraction_regex_first_pass),
         charge_count_extracted_second_pass = ifelse(is.na(charge_count_extracted_first_pass), str_extract(charge_name, count_extraction_regex_second_pass), NA),
         charge_count_extracted = coalesce(charge_count_extracted_first_pass, charge_count_extracted_second_pass),
         charge_name_original = charge_name,
         charge_name =  if_else(is.na(charge_count_extracted), charge_name, trimws(str_remove(charge_name, fixed(charge_count_extracted)))))

# Roll up charges so there is only one charge within each case and charge type with annotated count information
charges_rolled_up <- charges_count_extracted %>%
  filter(!is_post_charge_event) %>%
  group_by(case_number, case_id, charge_name, statute, level) %>%
  summarise(num_counts = n(),
            charge_id = min(charge_id),
            earliest_charge_date = min(charge_date, na.rm=TRUE),
            latest_charge_date = max(charge_date, na.rm=TRUE)) %>%
  ungroup() %>%
  mutate(charge_date = earliest_charge_date) %>%
  group_by(case_number, case_id) %>%
  arrange(desc(level), charge_id) %>%
  mutate(charge_id = row_number()) %>%
  ungroup() %>%
  mutate(is_primary_charge = (charge_id == 1))
  #filter(case_id %in% cases_filtered$case_id)

# Extract count data from charge name using regular expressions. This will allow us to normalize the charge names with better accuracy.
charges_count_extracted <- select_case_charges %>%
  mutate(charge_name = trimws(toupper(charge_name))) %>%
  mutate(is_motion_charge = charge_name %in% motion_charges) %>%
  mutate(charge_count_extracted_first_pass = str_extract(charge_name, count_extraction_regex_first_pass),
         charge_count_extracted_second_pass = ifelse(is.na(charge_count_extracted_first_pass), str_extract(charge_name, count_extraction_regex_second_pass), NA),
         charge_count_extracted = coalesce(charge_count_extracted_first_pass, charge_count_extracted_second_pass),
         charge_name_original = charge_name,
         charge_name =  if_else(is.na(charge_count_extracted), charge_name, trimws(str_remove(charge_name, fixed(charge_count_extracted))))) %>%
  group_by(case_id, charge_name, statute, level) %>%
  arrange(charge_id) %>%
  mutate(charge_count_freq = row_number()) %>%
  ungroup()

# Roll up charges so there is only one charge within each case and charge type with annotated count information
charges_rolled_up <- charges_count_extracted %>%
  group_by(case_id, charge_name, statute, level, charge_date, is_motion_charge) %>%
  summarise(num_counts = max(charge_count_freq)) %>%
  ungroup() %>%
  group_by(case_id) %>%
  arrange(charge_date, is_motion_charge) %>%
  mutate(charge_id = row_number()) %>%
  ungroup()

# Use regular expressions to break statute field apart into its components - chapter, section, and subsection(s). This allows us to normalize charge
# names using metadata associated with the charge statute.
statute_expanded <- charges_rolled_up %>%
  select(statute) %>%
  filter(str_detect(toupper(statute), 'UNKNOWN|DEFAULT', negate = TRUE)) %>%
  distinct() %>%
  mutate(statute_component = str_split(statute, statute_split_regex)) %>%
  unnest(statute_component) %>%
  filter(statute_component != "") %>%
  group_by(statute) %>%
  mutate(num = row_number()) %>%
  ungroup() %>%
  mutate(classification = case_when((num == 1) & !is.na(statute_component) ~ 'statute_chapter',
                                    (num == 2) & !is.na(statute_component) ~ 'statute_section',
                                    (num > 2) & ((tolower(statute_component) %in% letters) | (statute_component %in% 0:9)) ~ 'statute_subsection')) %>%
  filter(!is.na(classification)) %>%
  group_by(statute, classification) %>%
  arrange(num) %>%
  mutate(statute_component = ifelse(classification == 'statute_subsection', paste(tolower(statute_component), collapse = ' - '), statute_component)) %>%
  select(-num) %>%
  distinct() %>%
  ungroup() %>%
  pivot_wider(id_cols = statute, names_from = classification, values_from = statute_component)

charges_expanded <- charges_rolled_up %>% 
  left_join(statute_expanded)

# Get distinct charge names for Umich classifier
charge_names_umich <- charges_expanded %>% 
  select(charge_name)

write_csv(charge_names_umich, 'data/output/charge_names_umich.csv')