import csv
import os
import glob

class Processor:
    def __init__(self, directory_path):
        self.directory_path = directory_path

    def process(self):
        sentences = []

        for file_path in glob.glob(os.path.join(self.directory_path, '*.csv')):
            with open(file_path, mode='r') as file:
                csv_reader = csv.reader(file)
                headers = next(csv_reader)
                sentences.append(headers)
                columns = {header: [] for header in headers}
                
                for row in csv_reader:
                    for header, value in zip(headers, row):
                        columns[header].append(value)
                for column in columns.values():
                    sentences.append(column)
        return sentences