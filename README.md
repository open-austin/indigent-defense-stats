# Tyler Technologies Odyssey scraper and parser

This is a scraper to collect and process public case records from the Tyler Technologies Odyssey court records system. If you are a dev or want to file an Issue, please read [CONTRIBUTING](CONTRIBUTING.md).

## Local setup

### Install toolchain

1. Clone this repo and navigate to it.
   - `git clone https://github.com/open-austin/indigent-defense-stats`
   - `cd indigent-defense-stats`
2. Install Pyenv if not already installed ([linux, mac](https://github.com/pyenv/pyenv), or [windows](https://github.com/pyenv-win/pyenv-win))
3. Run `pyenv install` to get the right Python version

### Setup `venv`

First, you'll need to create a virtual environment, this differs depending on your OS.

On linux/mac

```bash
python -m venv .venv --prompt ids # (you can substitute `ids` for any name you want)
```

On Windows

```powershell
c:\>Python35\python -m venv c:\path\to\repo\ids # (you can substitute `ids` for any name you want)
```

Next, you'll need to "activate" the venv. You'll need to run this command every time you work in the codebase and tell your IDE which Python environment to use. It will likely default to wherever `python` resolves to in your system path. The specific command you run will depend on both your OS and shell.

On linux/mac

| platform | shell      | Command to activate virtual environment |
| :------- | :--------- | :-------------------------------------- |
| POSIX    | bash/zsh   | $ source <venv>/bin/activate            |
|          | fish       | $ source <venv>/bin/activate.fish       |
|          | csh/tcsh   | $ source <venv>/bin/activate.csh        |
|          | PowerShell | $ <venv>/bin/Activate.ps1               |
| Windows  | cmd.exe    | C:\> <venv>\Scripts\activate.bat        |
|          | PowerShell | PS C:\> <venv>\Scripts\Activate.ps1     |

Source: https://docs.python.org/3/library/venv.html#how-venvs-work

Note: Again, you'll need to activate venv _every time you want to work in the codebase_.

### Install python dependencies

Using `pip`, install the project dependencies.

```shell
pip install -r requirements.txt
```

### Running CLI

@TODO - this section needs to be updated.

7. Set parameters to the main command:
   - counties = The counties that are listed in the count CSV. Update column "scraper" in the CSV to "yes" to include the county.
   - start_date = The first date you want to scrape for case data. Update in scraper.
   - end_date = The last date you want to scrape for case data. Update in scraper.
8. Run the handler.
   - `python run python .src/orchestrator`

## Structure of Code

- County Database: A CSV table contains the necessary Odyssey links and version for each county in Texas. One column ("scrape") indicates whether that county should be scraped. Currently, Hays is the default.
- Handler (src/handler): This reads the CSV for the counties to be scraped and runs the following processes for each county. You can also set the start and end date of the parser here.

  - **Scraper** (`src/scraper`): This scrapes all of the judicial officers for each day within the period set in the handler and saves all of the HTML to data/[county name]/case_html.
  - **Parser** (`src/parser`): This parses all of the HTML in the county-specific HTML folder to accompanying JSON files in data/[county name]/case_json.
  - **Cleaner** (`src/cleaner`): This cleans and redacts information in in the county-specific json folder to a new folder of JSON files in data/[county name]/case_json_cleaned.
  - **Updater** (`src/updater`): This pushed the cleaned and redacted JSON in the county-specific cleaned json folder to a container in CosmosDB where it can then be use for visualization.

## Flowchart: Relationships Between Functions and Directories

```mermaid
flowchart TD
    orchestrator{"src/orchestrator (class): <br> orchestrate (function)"} --> county_db[resources/texas_county_data.csv]
    county_db  --> |return counties where 'scrape' = 'yes'| orchestrator
    orchestrator -->|loop through these counties <br> and run these four functions| scraper(1. src/scraper: scrape)
    scraper --> parser(2. src/parser: parse)
    scraper --> |create 1 HTML per case| data_html[data/county/case_html/case_id.html]
    parser--> pre2017(src/parser/pre2017)
    parser--> post2017(src/parser/post2017)
    pre2017 --> cleaner[3. src/cleaner: clean]
    post2017 --> cleaner
    parser --> |create 1 JSON per case| data_json[data/county/case_json/case_id.json]
    cleaner --> |look for charge in db<br>and normalize it to uccs| charge_db[resouces/umich-uccs-database.json]
    charge_db --> cleaner
    cleaner --> updater(4. src/updater: update)
    cleaner --> |create 1 JSON per case| data_json_cleaned[data/county/case_json_cleaned/case_id.json]
    updater --> |send final cleaned JSON to CosmosDB container| CosmosDB_container[CosmosDB container]
    CosmosDB_container --> visualization{live visualization}
```
