import csv
import os
import glob
from pathos.multiprocessing import ProcessingPool as Pool
# from multiprocessing.pool import ThreadPool as Pool
from tqdm import tqdm

class Processor:
    def __init__(self, directory_path):
        self.directory_path = directory_path

    def process_file(self, file_path):
        sentences = []
        with open(file_path, mode='r') as file:
            try:
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

            except:
                pass

        return sentences
    
    # single-threaded version
    def process_single(self, maxlen=1000):
        sentences = []
        file_paths = glob.glob(os.path.join(self.directory_path, '*.csv'))
        for i in tqdm(range(min(maxlen, len(file_paths)))):
            sentences.extend(self.process_file(file_paths[i]))
        return sentences

    def process(self, max_workers=2):
        sentences = []
        file_paths = glob.glob(os.path.join(self.directory_path, '*.csv'))
        
        with Pool(processes=max_workers) as pool:
            results = tqdm(pool.imap(self.process_file, file_paths), total=len(file_paths))
        
        for result in results:
            sentences.extend(result)
        
        return sentences