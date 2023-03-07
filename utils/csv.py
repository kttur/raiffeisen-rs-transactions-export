import csv


def write_dict_to_csv(file_path, data):
    if not data:
        return

    with open(file_path, 'w', newline='', encoding="utf-8") as csv_file:
        header = data[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)
