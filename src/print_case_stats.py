import os
import json

N_LONGEST = 5

case_data_list = []

for JO_dir in os.scandir("data_by_JO"):
    for case_file in os.scandir(os.path.join(JO_dir.path, "case_data")):
        with open(case_file.path, "r") as file_handle:
            case_data_list.append(json.loads(file_handle.read()))


def print_top_cases_by_lambda(sort_function, description):
    print("\n", N_LONGEST, "longest cases by", description + ".")
    cases_by_lambda = sorted(case_data_list, key=sort_function)[-N_LONGEST:]
    print(
        "\n".join(
            f"{i}. {sort_function(case)} - {case['filename']}"
            for i, case in enumerate(cases_by_lambda[::-1], 1)
        )
    )


print_top_cases_by_lambda(lambda case: len(str(case)), "string length")
print(
    "Average string length of cases:",
    int(sum(len(str(case)) for case in case_data_list) / len(case_data_list)),
)
events_len = lambda case: len(case["other events and hearings"])
print_top_cases_by_lambda(
    events_len,
    "'other events and hearings' length",
)
print(
    "Average 'other events and hearings' length of cases:",
    int(sum(events_len(case) for case in case_data_list) / len(case_data_list)),
)
disposition_len = lambda case: len(case["dispositions"])
print_top_cases_by_lambda(
    disposition_len,
    "'dispositions' length",
)
print(
    "Average 'dispositions' length of cases:",
    int(sum(disposition_len(case) for case in case_data_list) / len(case_data_list)),
)
print("\nNumber of cases:", len(case_data_list))
