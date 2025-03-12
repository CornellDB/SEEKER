import csv
import os
import glob
from concurrent.futures import ThreadPoolExecutor

class Processor:
    def __init__(self, directory_path):
        self.directory_path = directory_path

    def process_file(self, file_path):
        sentences = []
        with open(file_path, mode='r') as file:
            csv_reader = csv.reader(file, quoting=csv.QUOTE_NONE)
            headers = next(csv_reader)
            sentences.append(headers)
            columns = {header: [] for header in headers}
            
            for row in csv_reader:
                try:
                    for header, value in zip(headers, row):
                        columns[header].append(value)
                except:
                    # handling field larger than field limit
                    pass
                
            for column in columns.values():
                sentences.append(column)
        return sentences

    def process(self, max_workers=4):
        sentences = []
        file_paths = glob.glob(os.path.join(self.directory_path, '*.csv'))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(self.process_file, file_paths)
        
        for result in results:
            sentences.extend(result)
        
        return sentences