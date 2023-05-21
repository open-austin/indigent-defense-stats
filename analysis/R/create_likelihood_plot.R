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
