import re
import pandas as pd

class TextProcessor:
    def preprocess_text(self, text):
        # Simple text preprocessing to remove non-alphanumeric characters and convert to lowercase
        text = re.sub(r'\W+', ' ', text)
        return text.lower()

    def get_word_counts(self, df):
        # Convert all data in the DataFrame to lowercase string
        all_text = df.astype(str).apply(lambda x: ' '.join(x), axis=1).str.cat(sep=' ').lower()
        # Preprocess the text
        all_text = self.preprocess_text(all_text)
        # Convert the text to a pandas Series
        words = pd.Series(all_text.split())
        #Delete nan values and empty strings
        words = words[words != 'nan']
        words = words[words != '']
        # Delete words with length less than 3
        words = words[words.str.len() > 2]
        # Delete words with numbers
        words = words[~words.str.contains(r'\d')]
        # Get word counts
        return words.value_counts()
