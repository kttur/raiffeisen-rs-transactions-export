import csv


def write_dict_to_csv(file_path, data):
    with open(file_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=data.keys())
        writer.writeheader()
        writer.writerows(data)
