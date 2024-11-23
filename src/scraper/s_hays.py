import logging
from helpers import *

class ScraperHays():

    def __init__(self):
        pass

    def scraper_hays(self, base_url, results_soup, case_html_path, logger, session, ms_wait):
        case_urls = [
            base_url + anchor["href"]
            for anchor in results_soup.select('a[href^="CaseDetail"]')
        ]
        logger.info(f"{len(case_urls)} cases found")
        for case_url in case_urls:
            case_id = case_url.split("=")[1]
            logger.info(f"{case_id} - scraping case")
            # make request for the case
            try:
                case_html = request_page_with_retry(
                    session=session,
                    url=case_url,
                    verification_text="Date Filed",
                    logger=logger,
                    ms_wait=ms_wait,
                )
            except:
                logger.info(f"Issue with scraping this case: {case_id}. Moving to next one.")
            # write html case data
            logger.info(f"{len(case_html)} response string length")

            with open(
                os.path.join(case_html_path, f"{case_id}.html"), "w"
            ) as file_handle:
                file_handle.write(case_html)
