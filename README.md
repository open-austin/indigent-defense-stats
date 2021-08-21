## Hays County Criminal Records Scraper

This is (currently) a simple proof-of-concept that uses `requests`, `datetime`
and `beautifulsoup` to collect case records over the past five years.

### Installation

This project was instantiated with `venv`.

- create the venv, `python3 -m venv .`
- active the project, e.g. `source bin/activate` (bash) or `. .venv/bin/activate.fish` (fish)
- install libraries, `pip install -r requirements.txt`

## Technical Plan

#### Scraping pages of search results

The smallest set of stable values for court records for this project
are the Judicial Officers. They preside over a court for sometimes years
and are associated with every court case (imporantly, the electronic record)
for that span of time.

```
Given:
  - A judicial officer
  - A date range (e.g. 07/01/2015 - 09/01/2015)

Do:
  - Request records for the given range
  IF
    - Rate limiting, or some error occurs
    THEN
      - Try to get a new session
  IF
    - Record count exceeds 200
    THEN
      - Store the records (probably in-memory)
      - Check the date of the 200th record
      - Update the BEGIN and END date strings
  ELSE
    - Request the next set of results
```

## Edge cases

- Leap years
- A day with more than 200 records (seems uncommon?)
