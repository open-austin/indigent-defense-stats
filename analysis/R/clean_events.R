library(tidyverse)

charges <- read_csv('data/output/charges_cleaned_normalized.csv')


events <- read_csv('data/events_2022-03-27.csv', col_select=-1) %>%
  mutate(event_date = lubridate::as_date(event_date),
         first_event_date = lubridate::as_date(first_event_date))

select_events <- charges %>%
  select(case_number, earliest_charge_date) %>%
  left_join(events) %>%
  filter(event_date >= earliest_charge_date)

good_motion_dismiss <- c("Motion and Order To Dismiss", "Motion To Dismiss")
good_motion_itemized_payment <- c("Motion/Order for Payment of Itemized Time/Services",
                                  "Motion For Payment of Itemized Time and Services",
                                  "Motion for Payment of Itemized Time & Services")
other_good_motions <- c("Motion To Suppress", "Motion to Reduce Bond", 
                        "Motion for Production", "Motion For Speedy Trial", 
                        "Motion for Discovery", "Motion In Limine")

all_good_motions <- c(good_motion_dismiss, good_motion_itemized_payment, 
                      other_good_motions)

events_cleaned <- select_events %>%
  mutate(event_name_lower = tolower(event_name),
         event_name = case_when((event_name_lower %in% tolower(good_motion_dismiss)) ~ 
                                  good_motion_dismiss[1],
                                (event_name_lower %in% tolower(good_motion_itemized_payment)) ~ 
                                  good_motion_itemized_payment[1],
                                TRUE ~ event_name),
         event_name_formatted = str_to_title(event_name)) %>%
  select(case_number, event_name_formatted, event_date, first_event_date, attorney) 

write_csv(events_cleaned, 'data/output/events_cleaned.csv')



