from subprocess import check_output, STDOUT
from unittest import main, TestCase


class TestScrapingSites(TestCase):
    def test_hays(self):
        output = check_output(
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
                "Updegrove, Robert",
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


if __name__ == "__main__":
    main(verbosity=2)
