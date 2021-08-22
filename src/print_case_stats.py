import os
import json
import statistics

from time import time

N_LONGEST = 5
START_TIME = time()

case_data_list = []

for JO_dir in os.scandir("data_by_JO"):
    for case_file in os.scandir(os.path.join(JO_dir.path, "case_data")):
        with open(case_file.path, "r") as file_handle:
            case_data_list.append(json.loads(file_handle.read()))


def print_top_cases_by_lambda(sort_function, description):
    print("\n", description)
    cases_by_lambda = sorted(case_data_list, key=sort_function)[-N_LONGEST:]
    print(
        "\n".join(
            f"{i}. {sort_function(case)}".ljust(20) + case["filename"]
            for i, case in enumerate(cases_by_lambda[::-1], 1)
        )
    )
    print(
        "Mean:",
        round(statistics.mean(sort_function(case) for case in case_data_list), 2),
        " Median:",
        round(statistics.median(sort_function(case) for case in case_data_list), 2),
        " Mode:",
        round(statistics.mode(sort_function(case) for case in case_data_list), 2),
    )


events_len = lambda case: len(case["other events and hearings"])
print_top_cases_by_lambda(
    events_len,
    "other events and hearings length",
)
disposition_len = lambda case: len(case["dispositions"])
print_top_cases_by_lambda(
    disposition_len,
    "dispositions length",
)
case_cost = (
    lambda case: float(
        case["financial information"]["total financial assessment"].replace(",", "")
    )
    if "financial information" in case
    else 0.0
)
print_top_cases_by_lambda(
    case_cost,
    "highest cost",
)
charges_len = lambda case: len(case["charge information"])
print_top_cases_by_lambda(
    charges_len,
    "number of charges",
)
print("\nNumber of cases:", len(case_data_list))
print("Stats parsing runtime:", round(time() - START_TIME, 2), "seconds")
