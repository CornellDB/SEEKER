import time
import json
import sys
import uuid
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

class QgramIndexer:
    """
    QgramIndexer class for SEEKER system, providing both full dataset (Di, Mi) 
    and summary-based (Si, Mi) indexing using Q-grams.
    """
    def __init__(self, use_summaries=False, q=2):
        """
        Initialize the QgramIndexer class.
        
        Args:
            use_summaries (bool): Whether to use summaries instead of full datasets
            q (int): Size of the q-grams (default is 2)
        """
        self.use_summaries = use_summaries
        self.q = q
        self.dataset_index = {}  # Main index mapping q-grams to datasets
        self.dataset_info = {}   # Store dataset information
        
    def _generate_qgrams(self, text, q=None):
        """
        Generate q-grams from text.
        
        Args:
            text (str): The text to generate q-grams from
            q (int): Size of the q-grams, defaults to self.q
            
        Returns:
            set: Set of unique q-grams
        """
        if q is None:
            q = self.q
            
        # Normalize text
        text = text.lower()
        
        # Generate q-grams
        qgrams = set()
        for i in range(len(text) - q + 1):
            qgram = text[i:i+q]
            qgrams.add(qgram)
            
        return qgrams
    
    def _generate_summary(self, dataset_content, top_n=50):
        """
        Generate a summary of the dataset using TF-IDF to extract the most important terms.
        
        Args:
            dataset_content (str): The content of the dataset
            top_n (int): Number of top terms to include in the summary
            
        Returns:
            str: A summary of the dataset
        """
        # Simple tokenization without NLTK dependencies
        words = dataset_content.lower().split()
        filtered_words = [w for w in words if len(w) > 2 and w.isalnum()]
        
        # If dataset is too small, return as is
        if len(filtered_words) < top_n:
            return " ".join(filtered_words)
        
        # Use TF-IDF to find important terms
        try:
            vectorizer = TfidfVectorizer(max_features=top_n)
            tfidf_matrix = vectorizer.fit_transform([dataset_content])
            
            # Get feature names (terms)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top terms based on TF-IDF scores
            tfidf_scores = tfidf_matrix.toarray()[0]
            top_indices = np.argsort(tfidf_scores)[-top_n:]
            top_terms = [feature_names[i] for i in top_indices]
            
            # Return summary as a space-separated string of top terms
            return " ".join(top_terms)
        except:
            # If TF-IDF fails, return a subset of filtered tokens
            return " ".join(filtered_words[:top_n])
    
    def ingest(self, dataset_model):
        """
        Ingest a dataset and its metadata into the index.
        
        Args:
            dataset_model: SEEKER DatasetModel object
            
        Returns:
            bool: True if ingestion was successful, False otherwise
        """
        try:
            # Convert DataFrame to string for indexing
            dataset_content = dataset_model.dataset.astype(str).to_json()
            metadata_content = json.dumps(dataset_model.metadata) if dataset_model.metadata else "{}"
            
            # Generate a document ID if not present
            doc_id = str(dataset_model.id) if hasattr(dataset_model, 'id') else str(uuid.uuid4())
            dataset_name = dataset_model.name if hasattr(dataset_model, 'name') else dataset_model.dataset_name
            
            # Store dataset info
            self.dataset_info[doc_id] = {
                "dataset_id": doc_id,
                "dataset_name": dataset_name,
                "metadata": metadata_content
            }
            
            # Process content based on indexing strategy
            if self.use_summaries:
                # Generate and index the summary
                summary = self._generate_summary(dataset_content)
                content_to_index = summary
            else:
                # Index the full dataset
                content_to_index = dataset_content
            
            # Generate q-grams
            qgrams = self._generate_qgrams(content_to_index)
            
            # Add to index
            for qgram in qgrams:
                if qgram not in self.dataset_index:
                    self.dataset_index[qgram] = set()
                self.dataset_index[qgram].add(doc_id)
            
            return True
        except Exception as e:
            print(f"Error ingesting dataset {dataset_name}: {e}")
            return False
    
    def ingest_multiple(self, dataset_models):
        """
        Ingest multiple datasets into the index.
        
        Args:
            dataset_models: Dictionary of SEEKER DatasetModel objects
            
        Returns:
            dict: Dictionary with dataset names as keys and ingestion success as values
        """
        results = {}
        for name, model in dataset_models.items():
            results[name] = self.ingest(model)
        return results
    
    def query(self, keyword):
        """
        Query the index using q-grams.
        
        Args:
            keyword (str): The keyword to search for
            
        Returns:
            list: List of matching dataset results with scores
            float: Time taken for the query in seconds
        """
        start_time = time.time()
        
        # Generate q-grams from the keyword
        keyword_qgrams = self._generate_qgrams(keyword)
        
        # Find matching datasets
        matching_datasets = {}
        
        for qgram in keyword_qgrams:
            if qgram in self.dataset_index:
                for doc_id in self.dataset_index[qgram]:
                    if doc_id not in matching_datasets:
                        matching_datasets[doc_id] = 0
                    matching_datasets[doc_id] += 1
        
        # Calculate scores based on matching q-gram count
        results = []
        max_score = max(matching_datasets.values()) if matching_datasets else 1
        
        for doc_id, count in matching_datasets.items():
            # Normalize score
            score = count / max_score * 10  # Scale to similar range as Elasticsearch
            
            # Get dataset info
            info = self.dataset_info.get(doc_id, {})
            
            results.append({
                "dataset_id": doc_id,
                "dataset_name": info.get("dataset_name", "Unknown"),
                "score": score
            })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        return results, query_time
    
    def get_index_size(self):
        """
        Get the size of the index in bytes.
        
        Returns:
            int: Size of the index in bytes
        """
        # Calculate the size of the index in memory
        index_size = sys.getsizeof(self.dataset_index)
        info_size = sys.getsizeof(self.dataset_info)
        
        # Add sizes of all keys and values
        for qgram, doc_ids in self.dataset_index.items():
            index_size += sys.getsizeof(qgram)
            index_size += sys.getsizeof(doc_ids)
            for doc_id in doc_ids:
                index_size += sys.getsizeof(doc_id)
        
        for doc_id, info in self.dataset_info.items():
            info_size += sys.getsizeof(doc_id)
            info_size += sys.getsizeof(info)
            for key, value in info.items():
                info_size += sys.getsizeof(key)
                info_size += sys.getsizeof(value)
        
        return index_size + info_size
    
    def clear_indices(self):
        """Clear the index."""
        self.dataset_index = {}
        self.dataset_info = {}
        return True
