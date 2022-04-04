- [texas_county_data.csv](texas_county_data.csv) - details for the scraper are stored here

  - some of the note fields include a password for guest login. The format is: `PUBLICLOGIN#{user}/{pass}# do not edit - used as data in scraper` replacing the values in {}s.

  - The version number is usually the copyright year, it is for Odyssey sites. Some sites have an actual version number, this might make more sense. Year works well for the sites which show an old copyright year, meaning that is when the software was released.

  - I've tried to represent unscrapable sites with reasoning through the `search_disabled, site_down, captcha,must_pay, and must_register` fields

  - Any additional notes for using the site which are unique to that site go in notes. Also, info for non-odyssey sites or anything else that seems notable.

- [texas_census_data.csv](texas_census_data.csv) - Included for research purposes. Some fields are coded according to these [Data dictionary reference names.](https://www2.census.gov/programs-surveys/decennial/2020/technical-documentation/complete-tech-docs/summary-file/2020Census_PL94_171Redistricting_NationalTechDoc.pdf)
