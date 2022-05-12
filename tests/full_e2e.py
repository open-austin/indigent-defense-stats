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
        output[0],
        output,
        "Assert that testing message is logged after first case is scraped successfully.",
    )

class TestScrapingSites(TestCase):
    def test_anderson(self):
        test_scraper(
            self, county="anderson", date="2022-03-28", judicial_officer="Calhoon, Mark"
        )

    def test_angelina(self):
        test_scraper(
            self, county="angelina", date="2022-02-23", judicial_officer="Cheshire, Rodney"
        )

    def test_austin(self):
        test_scraper(
            self, county="austin", date="2022-04-27", judicial_officer="Burger, Bernice"
        )

    def test_bastrop(self):
        test_scraper(
            self, county="bastrop", date="2022-04-21", judicial_officer="Allen, Cindy"
        )

    def test_bell(self):
        test_scraper(
            self, county="bell", date="2022-05-10", judicial_officer="Coleman, Clifford"
        )

    def test_bexar(self):
        test_scraper(
            self, county="bexar", date="2022-03-07", judicial_officer="ALVARADO, ROSIE"
        )

    def test_bowie(self):
        test_scraper(
            self, county="bowie", date="2022-02-10", judicial_officer="Hankins, Mary"
        )

    def test_brazoria(self):
        test_scraper(
            self, county="brazoria", date="2022-04-14", judicial_officer="Bulanek, Patrick"
        )

    def test_calhoun(self):
        test_scraper(
            self, county="calhoun", date="2022-01-12", judicial_officer="Williams, Stephen"
        )

    def test_cameron(self):
        test_scraper(
            self, county="cameron", date="2022-03-24", judicial_officer="Alejandro, Leonel"
        )

    def test_collin(self):
        test_scraper(
            self, county="collin", date="2022-04-14", judicial_officer="Baxter, Lance"
        )

    def test_dallas(self):
        test_scraper(
            self, county="dallas", date="2022-02-03", judicial_officer="BROWN, MARY"
        )

    def test_denton(self):
        test_scraper(
            self, county="denton", date="2022-05-06", judicial_officer="Shanklin, Brody"
        )

    def test_ector(self):
        test_scraper(
            self, county="ector", date="2022-02-28", judicial_officer="Wilson, Kathy"
        )

    def test_fannin(self):
        test_scraper(
            self, county="fannin", date="2022-01-12", judicial_officer="Blake, Laurine"
        )

    def test_fortbend(self):
        test_scraper(
            self, county="fort bend", date="2022-05-03", judicial_officer="Glover, Tamecia"
        )

    def test_galveston(self):
        test_scraper(
            self, county="galveston", date="2022-01-13", judicial_officer="Ellisor, John"
        )

    def test_gillespie(self):
        test_scraper(
            self, county="gillespie", date="2022-01-25", judicial_officer="Mabray, Cheryll"
        )

    def test_grayson(self):
        test_scraper(
            self, county="grayson", date="2022-03-31", judicial_officer="Fallon, Jim"
        )

    def test_gregg(self):
        test_scraper(
            self, county="gregg", date="2022-01-11", judicial_officer="Womack, Tim"
        )

    def test_guadalupe(self):
        test_scraper(
            self, county="guadalupe", date="2022-01-20", judicial_officer="Crawford, Jessica"
        )

    def test_hale(self):
        test_scraper(
            self, county="hale", date="2022-04-21", judicial_officer="Collins, Sheron"
        )

    def test_harris(self):
        test_scraper(
            self, county="harris", date="2022-01-19", judicial_officer="Adams, Wanda"
        )

    def test_harrison(self):
        test_scraper(
            self, county="harrison", date="2022-03-29", judicial_officer="Black, Joe"
        )

    def test_hays(self):
        test_scraper(
            self, county="hays", date="2022-05-10", judicial_officer="Updegrove, Robert"
        )
    
    def test_henderson(self):
        test_scraper(
            self, county="henderson", date="2022-01-27", judicial_officer="Perryman, Nancy"
        )

    def test_hidalgo(self):
        test_scraper(
            self, county="hidalgo", date="2022-04-13", judicial_officer="Garcia, JoAnne"
        )

    def test_howard(self):
        test_scraper(
            self, county="howard", date="2022-03-24", judicial_officer="Yeats, Timothy D"
        )

    def test_johnson(self):
        test_scraper(
            self, county="johnson", date="2022-02-28", judicial_officer="Monk, Jeff"
        )

    def test_lamar(self):
        test_scraper(
            self, county="lamar", date="2022-01-25", judicial_officer="Bell, Brandon"
        )

    def test_liberty(self):
        test_scraper(
            self, county="liberty", date="2022-01-11", judicial_officer="Chambers, Thomas"
        )

    def test_lubbock(self):
        test_scraper(
            self, county="lubbock", date="2022-03-03", judicial_officer="Darnell, Kara"
        )

    def test_medina(self):
        test_scraper(
            self, county="medina", date="2022-01-27", judicial_officer="Cashion, Mark"
        )

    def test_montgomery(self):
        test_scraper(
            self, county="montgomery", date="2022-02-16", judicial_officer="Grant, Phil"
        )

    def test_morris(self):
        test_scraper(
            self, county="morris", date="2022-01-26", judicial_officer="Fridia, Nikita"
        )

    def test_navarro(self):
        test_scraper(
            self, county="navarro", date="2022-02-28", judicial_officer="Putman, Amanda"
        )

    def test_nueces(self):
        test_scraper(
            self, county="nueces", date="2022-03-30", judicial_officer="Barclay, Susan"
        )

    def test_panola(self):
        test_scraper(
            self, county="panola", date="2022-04-11", judicial_officer="Bailey, Terry D"
        )

    def test_parker(self):
        test_scraper(
            self, county="parker", date="2022-02-23", judicial_officer="Deen, Pat"
        )

    def test_potter(self):
        test_scraper(
            self, county="potter", date="2022-04-07", judicial_officer="Baker, Carry"
        )

    def test_randall(self):
        test_scraper(
            self, county="randall", date="2022-04-12", judicial_officer="Christy, Dyer"
        )

    def test_rockwall(self):
        test_scraper(
            self, county="rockwall", date="2022-01-20", judicial_officer="Hall, Brett"
        )
        
    def test_sanjacinto(self):
        test_scraper(
            self, county="san jacinto", date="2022-05-10", judicial_officer="Faulkner, Fritz"
        )

    def test_smith(self):
        test_scraper(
            self, county="smith", date="2022-03-24", judicial_officer="Heaton, Taylor"
        )

    def test_tarrant(self):
        test_scraper(
            self, county="tarrant", date="2022-01-26", judicial_officer="Kelly, Lynn"
        )

    def test_taylor(self):
        test_scraper(
            self, county="taylor", date="2022-04-07", judicial_officer="Harper, Robert"
        )

    def test_tomgreen(self):
        test_scraper(
            self, county="tom green", date="2022-04-11", judicial_officer="Nolen, Ben"
        )

    def test_travis(self):
        test_scraper(
            self, county="travis", date="2022-04-29", judicial_officer="Holmes, Sylvia"
        )

    def test_victoria(self):
        test_scraper(
            self, county="victoria", date="2022-04-28", judicial_officer="Ernst, Travis H."
        )

    def test_walker(self):
        test_scraper(
            self, county="walker", date="2022-02-17", judicial_officer="Cole, Stephen"
        )

    def test_waller(self):
        test_scraper(
            self, county="waller", date="2022-02-08", judicial_officer="Chaney, Carol"
        )

    def test_webb(self):
        test_scraper(
            self, county="webb", date="2022-05-02", judicial_officer="Villarreal, Victor"
        )

    def test_wichita(self):
        test_scraper(
            self, county="wichita", date="2022-01-20", judicial_officer="Barnard, Charles"
        )

    def test_williamson(self):
        test_scraper(
            self, county="williamson", date="2022-02-28", judicial_officer="McLean, Evelyn"
        )

    def test_wise(self):
        test_scraper(
            self, county="wise", date="2022-03-15", judicial_officer="Garrett, Willie"
        )

    def test_wood(self):
        test_scraper(
            self, county="wood", date="2022-02-17", judicial_officer="Gilbreath, Tony"
        )

if __name__ == "__main__":
    main(verbosity=2)
