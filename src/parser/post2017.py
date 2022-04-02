import json, traceback, os, argparse

from bs4 import BeautifulSoup


def parse(case_json_path: str, case_html_path: str, args: argparse.Namespace) -> None:
    print(case_json_path, case_html_path, args)
