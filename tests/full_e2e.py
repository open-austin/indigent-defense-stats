from subprocess import check_output, STDOUT
from unittest import main, TestCase


def test_scraper(self, county: str, date: str, judicial_officer: str):
    key = b'Testing, stopping after first case'
    message = "Assert that testing message is logged after first case is scraped successfully."
    container = check_output(
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
        key,
        container,
        message
    )

class TestScrapingSites(TestCase):
    # pass
    def test_anderson(self):
        test_scraper(
            self, county="anderson", date="2022-03-28", judicial_officer="Calhoon, Mark"
        )

    #error - captcha?
    def test_angelina(self):
        test_scraper(
            self, county="angelina", date="2022-01-19", judicial_officer="GRUBBS, PATRICIA"
        )

    # pass
    def test_austin(self):
        test_scraper(
            self, county="austin", date="2022-04-27", judicial_officer="Burger, Bernice"
        )

    # pass
    def test_bastrop(self):
        test_scraper(
            self, county="bastrop", date="2022-04-21", judicial_officer="Allen, Cindy"
        )

    # fail ?
    def test_bell(self):
        test_scraper(
            self, county="bell", date="2022-04-29", judicial_officer="Coleman, Clifford"
        )

    # fail ?
    def test_bexar(self):
        test_scraper(
            self, county="bexar", date="2022-03-07", judicial_officer="ALVARADO, ROSIE"
        )

    # pass
    def test_bowie(self):
        test_scraper(
            self, county="bowie", date="2022-03-07", judicial_officer="Miller, Bill"
        )

    # pass
    def test_brazoria(self):
        test_scraper(
            self, county="brazoria", date="2022-01-10", judicial_officer="Holder, Terri"
        )
    
    # error - unable to search easily?
    def test_burnet(self):
        test_scraper(
            self, county="burnet", date="2019-04-05", judicial_officer="Baardsen, Dawn"
        )

    # fail ?
    def test_calhoun(self):
        test_scraper(
            self, county="calhoun", date="2022-01-12", judicial_officer="Williams, Stephen"
        )

    # error - captcha?
    def test_cameron(self):
        test_scraper(
            self, county="cameron", date="2022-02-23", judicial_officer="Alejandro, Leonel"
        )

     # error - unable to search easily?
    def test_chambers(self):
        test_scraper(
            self, county="chambers", date="2022-03-25", judicial_officer="Baker, Jennifer"
        )

    # pass
    def test_collin(self):
        test_scraper(
            self, county="collin", date="2022-03-04", judicial_officer="Mason, Corinne A."
        )

    # error - unable to search court calendar? 
    def test_comal(self):
        test_scraper(
            self, county="comal", date="2021-01-05", judicial_officer="Wigington, Deborah"
        )

    # fail ?
    def test_dallas(self):
        test_scraper(
            self, county="dallas", date="2022-02-03", judicial_officer="BROWN, MARY"
        )

    # fail ?
    def test_denton(self):
        test_scraper(
            self, county="denton", date="2022-05-18", judicial_officer="Hughey, Harris"
        )

    # fail ?
    def test_ector(self):
        test_scraper(
            self, county="ector", date="2022-02-28", judicial_officer="Wilson, Kathy"
        )

    # El Paso - Unable to search by judical officer.

    # fail ?
    def test_fannin(self):
        test_scraper(
            self, county="fannin", date="2022-01-12", judicial_officer="Blake, Laurine"
        )

    # pass
    def test_fortbend(self):
        test_scraper(
            self, county="fort bend", date="2022-05-19", judicial_officer="Wallace, Toni"
        )

    # error - captcha?
    def test_galveston(self):
        test_scraper(
            self, county="galveston", date="2022-01-13", judicial_officer="Ellisor, John"
        )

    # pass
    def test_gillespie(self):
        test_scraper(
            self, county="gillespie", date="2022-02-17", judicial_officer="McCann, Linda Meier"
        )

    # pass
    def test_grayson(self):
        test_scraper(
            self, county="grayson", date="2022-03-31", judicial_officer="Fallon, Jim"
        )

    # pass
    def test_gregg(self):
        test_scraper(
            self, county="gregg", date="2022-03-03", judicial_officer="Phillips, R. Kent"
        )

    # fail ?
    def test_guadalupe(self):
        test_scraper(
            self, county="guadalupe", date="2022-02-04", judicial_officer="Crawford, Jessica"
        )

    # pass
    def test_hale(self):
        test_scraper(
            self, county="hale", date="2022-01-05", judicial_officer="Davis, Karen"
        )

    # fail ?
    def test_harris(self):
        test_scraper(
            self, county="harris", date="2022-01-19", judicial_officer="Adams, Wanda"
        )

    # pass
    def test_harrison(self):
        test_scraper(
            self, county="harrison", date="2022-03-29", judicial_officer="Black, Joe"
        )

    # pass
    def test_hays(self):
        test_scraper(
            self, county="hays", date="2022-05-10", judicial_officer="Updegrove, Robert"
        )

    # pass
    def test_henderson(self):
        test_scraper(
            self, county="henderson", date="2022-02-15", judicial_officer="Perryman, Nancy"
        )

    # pass
    def test_hidalgo(self):
        test_scraper(
            self, county="hidalgo", date="2022-03-21", judicial_officer="Gonzalez, Noe"
        )

    # pass
    def test_howard(self):
        test_scraper(
            self, county="howard", date="2022-03-24", judicial_officer="Yeats, Timothy D"
        )

    # error ?
    def test_hunt(self):
        test_scraper(
            self, county="hunt", date="2022-04-18", judicial_officer="Aiken, Keli M."
        )

    # Hutchison - Requires login, unsure how to obtain.

    # error ?
    def test_johnson(self):
        test_scraper(
            self, county="johnson", date="2022-02-28", judicial_officer="Monk, Jeff"
        )

    # Kaufman - Unable to search by judical officer.

    # Kerr - Unable to search by judical officer.

    # fail - not finding judicial officers
    def test_lamar(self):
        test_scraper(
            self, county="lamar", date="2022-01-25", judicial_officer="Bell, Brandon"
        )

    # fail ?
    def test_liberty(self):
        test_scraper(
            self, county="liberty", date="2022-01-11", judicial_officer="Chambers, Thomas"
        )

    # fail ?
    def test_lubbock(self):
        test_scraper(
            self, county="lubbock", date="2022-03-03", judicial_officer="Darnell, Kara"
        )

    # pass
    def test_matagorda(self):
        test_scraper(
            self, county="matagorda", date="2022-03-08", judicial_officer="Sanders, Jason K."
        )

    # pass
    def test_medina(self):
        test_scraper(
            self, county="medina", date="2022-01-06", judicial_officer="Cashion, Mark"
        )

    # pass
    def test_montgomery(self):
        test_scraper(
            self, county="montgomery", date="2022-02-16", judicial_officer="Grant, Phil"
        )

    # pass
    def test_morris(self):
        test_scraper(
            self, county="morris", date="2022-01-26", judicial_officer="Fridia, Nikita"
        )

    # pass
    def test_navarro(self):
        test_scraper(
            self, county="navarro", date="2022-03-23", judicial_officer="LAGOMARSINO, JAMES"
        )

    # pass
    def test_nueces(self):
        test_scraper(
            self, county="nueces", date="2022-01-13", judicial_officer="Galvan, Bobby"
        )

    # pass
    def test_panola(self):
        test_scraper(
            self, county="panola", date="2022-04-11", judicial_officer="Bailey, Terry D"
        )

    # fail ?
    def test_parker(self):
        test_scraper(
            self, county="parker", date="2022-02-23", judicial_officer="Deen, Pat"
        )

    # fail ?
    def test_potter(self):
        test_scraper(
            self, county="potter", date="2022-04-07", judicial_officer="Baker, Carry"
        )

    # pass
    def test_randall(self):
        test_scraper(
            self, county="randall", date="2022-01-25", judicial_officer="Anderson, James"
        )

    # fail ?
    def test_rockwall(self):
        test_scraper(
            self, county="rockwall", date="2022-01-20", judicial_officer="Hall, Brett"
        )

    # pass     
    def test_sanjacinto(self):
        test_scraper(
            self, county="san jacinto", date="2022-05-10", judicial_officer="Faulkner, Fritz"
        )

    # pass
    def test_smith(self):
        test_scraper(
            self, county="smith", date="2022-02-02", judicial_officer="Ellis, Jason"
        )

    # fail ?
    def test_tarrant(self):
        test_scraper(
            self, county="tarrant", date="2022-03-02", judicial_officer="McGown, Quentin"
        )

    # pass
    def test_taylor(self):
        test_scraper(
            self, county="taylor", date="2022-04-07", judicial_officer="Harper, Robert"
        )

    # error ?
    def test_tomgreen(self):
        test_scraper(
            self, county="tom green", date="2022-04-11", judicial_officer="Nolen, Ben"
        )

    # pass
    def test_travis(self):
        test_scraper(
            self, county="travis", date="2022-04-29", judicial_officer="Holmes, Sylvia"
        )

    # pass
    def test_victoria(self):
        test_scraper(
            self, county="victoria", date="2022-01-31", judicial_officer="Ernst, Travis H."
        )

    # pass
    def test_walker(self):
        test_scraper(
            self, county="walker", date="2022-04-12", judicial_officer="Holt, Mark"
        )

    # pass
    def test_waller(self):
        test_scraper(
            self, county="waller", date="2022-03-23", judicial_officer="Jackson, Marian E."
        )

    # pass
    def test_webb(self):
        test_scraper(
            self, county="webb", date="2022-05-02", judicial_officer="Villarreal, Victor"
        )

    # fail ?
    def test_wichita(self):
        test_scraper(
            self, county="wichita", date="2022-01-05", judicial_officer="Barnard, Charles"
        )

    # pass
    def test_williamson(self):
        test_scraper(
            self, county="williamson", date="2022-03-22", judicial_officer="McLean, Evelyn"
        )

    # pass
    def test_wise(self):
        test_scraper(
            self, county="wise", date="2022-03-15", judicial_officer="Garrett, Willie"
        )

    # pass
    def test_wood(self):
        test_scraper(
            self, county="wood", date="2022-03-10", judicial_officer="McCampbell, J Brad"
        )


if __name__ == "__main__":
    main(verbosity=2)

