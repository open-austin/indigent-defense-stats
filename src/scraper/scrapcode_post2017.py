# Not currently in use. Should be moved to a county-specific module, class, and method when a post2017 county is included
"""def scrape_case_data_post2017(self, base_url, case_html_path, session, logger, ms_wait):
    # Need to POST this page to get a JSON of the search results after the initial POST
    case_list_json = request_page_with_retry(
        session=session,
        url=urllib.parse.urljoin(base_url, "Hearing/HearingResults/Read"),
        verification_text="AggregateResults",
        logger=logger,
    )
    case_list_json = json.loads(case_list_json)
    logger.info(f"{case_list_json['Total']} cases found")
    for case_json in case_list_json["Data"]:
        case_id = str(case_json["CaseId"])
        logger.info(f"{case_id} scraping case")
        # make request for the case
        case_html = request_page_with_retry(
            session=session,
            url=urllib.parse.urljoin(base_url, "Case/CaseDetail"),
            verification_text="Case Information",
            logger=logger,
            ms_wait=ms_wait,
            params={
                "eid": case_json["EncryptedCaseId"],
                "CaseNumber": case_json["CaseNumber"],
            },
        )
        # make request for financial info
        case_html += request_page_with_retry(
            session=session,
            url=urllib.parse.urljoin(
                base_url, "Case/CaseDetail/LoadFinancialInformation"
            ),
            verification_text="Financial",
            logger=logger,
            ms_wait=ms_wait,
            params={
                "caseId": case_json["CaseId"],
            },
        )
        # write case html data
        logger.info(f"{len(case_html)} response string length")
        with open(
            os.path.join(case_html_path, f"{case_id}.html"), "w"
        ) as file_handle:
            file_handle.write(case_html)"""