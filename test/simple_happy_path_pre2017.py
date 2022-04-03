import os

os.system(
    " ".join(
        [
            "poetry",
            "run",
            "python",
            "./src/scraper",
            "-start_date",
            "2022-03-22",
            "-end_date",
            "2022-03-22",
            "-county",
            "hays",
            "-judicial_officers",
            '"Updegrove, Robert"',
        ]
    )
)
