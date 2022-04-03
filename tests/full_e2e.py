from subprocess import check_output, STDOUT
from unittest import main, TestCase


def test_scraper(self, county: str, date: str, judicial_officer: str):
    output = check_output(
        [
            "poetry",
            "run",
            "python",
            "./src/scraper",
            "-start_date",
            date,
            "-end_date",
            date,
            "-county",
            county,
            "-judicial_officers",
            judicial_officer,
            "-test",
        ],
        stderr=STDOUT,
        shell=True,
    )
    self.assertIn(
        b"Testing, stopping after first case",
        output,
        "Assert that testing message is logged after first case is scraped successfully.",
    )


class TestScrapingSites(TestCase):
    def test_hays(self):
        test_scraper(
            self, county="hays", date="2022-03-22", judicial_officer="Updegrove, Robert"
        )

    def test_harris(self):
        test_scraper(
            self, county="harris", date="2022-03-02", judicial_officer="Adams, Wanda"
        )

    def test_dallas(self):
        test_scraper(
            self, county="dallas", date="2022-03-01", judicial_officer="BROWN, MARY"
        )


if __name__ == "__main__":
    main(verbosity=2)
