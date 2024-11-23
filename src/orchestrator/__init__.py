import os, csv

# Import all of the programs modules within the parent_dir
from .. import scraper
from .. import parser
from .. import cleaner
from .. import updater

class Orchestrator:
    def __init__(self):
        #Sets our base parameters
        self.counties = []
        self.start_date = '2024-07-01'       #Update start date here
        self.end_date = '2024-07-01'         #Update start date here
    def orchestrate(self, test: bool = False):

        #This open the county data CSV to see which counties should be scraped, parsed, cleaned, and updated.
        with open(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "resources", "texas_county_data.csv"
            ),
            mode="r",
        ) as file_handle:
            csv_file = csv.DictReader(file_handle)
            for row in csv_file:
                #This only selects the counties from the csv that should be parsed.
                if row["scrape"].lower() == "yes":
                    self.counties.append(row["county"])

        #This runs the different modules in order
        for c in self.counties:
            print(f"Starting to scrape, parse, clean, and update this county: {c}")
            scraper(test = test, county = c).scrape() #src/scraper
            parser(c).parse() #src/parser
            cleaner(c).clean() #src/cleaner
            updater(c).update() #src/updater
            print(f"Completed with scraping, parsing, cleaning, and updating of this county: {c}")

if __name__ == '__main__':
    Orchestrator().orchestrate()
