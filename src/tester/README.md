
# Unit Testing
This module provides unit testing using the unittest module for each module in the program.
## Setup
  
Once you've loaded the repository in Visual Studio, you can load the test by using the testing module in the VS interface. But you should make sure to update your settings.json file in the .vscode folder created in the root folder in order to direct VS to the subdirectory location of the test files within /src/tester.
```

{
"python.testing.unittestEnabled": true,
"python.testing.unittestArgs": [
"-v"
]
}
```
## Tests

### A. Scraper Tests

#### Test #1: Did the scraper create a file called 12947592.html in the right location?

This will look to see if there is an HTML file of the expected name in the expected destination.

It will also check if the file has been updated since the test began (ie. was updated rather than simply exists).

#### Test #2: Test #2: Is the resulting HTML file longer than 1000 characters?

This will check if the length of a string of the HTML file is longer than 1000 characters to ensure it was a full page scrape.
  
#### Test #3: Does the resulting HTML file container the cause number in the expected header location?

This will check a specific location in the HTML file for where a cause number is expected to be. If the cause number is present within the HTML at that location, this is a good indication that the scrape was successful.
  
### B. Parser Tests

#### Test #1: Check to see if there is a JSON called 51652356.json created in the correct location and that it was updated since this test started running

This will look to see if there is an JSON file of the expected name in the expected destination.

It will also check if the file has been updated since the test began (ie. was updated rather than simply exists).

####  Test #2: Check to see that JSON parsed all of the necessary fields and did so properly.

This unit test uses a JSON database of expected fields and features of those fields (called "field_validation_list.json") where each entry in the JSON file is a field with the following fields for each that are used in validation (for example):
```
{
    "name": "location",
    "logical_level": "top",
    "type": "string",
    "estimated_min_length": 3,
    "importance": "necessary"
},
{
    "name": "party information",
    "logical_level": "top",
    "type": "array",
    "estimated_min_length": 1,
    "importance": "necessary"
},
{
    "name": "charge information",
    "logical_level": "top",
    "type": "array",
    "estimated_min_length": 1,
    "importance": "necessary"
},
{
    "name": "defendant",
    "logical_level": "party",
    "type": "string",
    "estimated_min_length": 1,
    "importance": "necessary"
}
```
The order of fields it addresses goes in this order:
- necessary: fields that are consider required for a successful parsing
- high: are important for data visualization and analysis
- medium: have potential for use
- low: have little or no use or importance

It does so by opening a json dictionary filled with expected fields and expected features of those fields:
- whether field exists in the jason (is in): check_exists
- expected type (str or array):
- expected length (strings and arrays): check_length

### C. Cleaner Tests

In progress.
  
### D. Updater Tests

In progress.
  
### E. Orchestrator Tests

In progress.
