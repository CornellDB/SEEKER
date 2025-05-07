import time
import json
import matplotlib.pyplot as plt
import numpy as np
from elasticsearch import Elasticsearch
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pandas as pd
import uuid

class ElasticIndexer:
    """
    ElasticIndexer class for SEEKER system, providing both full dataset (Di, Mi) 
    and summary-based (Si, Mi) indexing using Elasticsearch.
    """
    def __init__(self, use_summaries=False, host='localhost', port=9200):
        """
        Initialize the ElasticIndexer class.
        
        Args:
            use_summaries (bool): Whether to use summaries instead of full datasets
            host (str): Elasticsearch host
            port (int): Elasticsearch port
        """
        self.es = Elasticsearch([{'host': host, 'port': port, 'scheme': 'http'}])
        self.use_summaries = use_summaries
        
        # Define index names for both approaches
        self.full_index = "seeker_datasets_full"
        self.summary_index = "seeker_datasets_summary"
        
        # Create indices if they don't exist
        self._create_indices()
        
        # Download NLTK resources if needed
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
    
    def _create_indices(self):
        """Create Elasticsearch indices if they don't exist."""
        # Mapping for full dataset index
        full_mapping = {
            "mappings": {
                "properties": {
                    "dataset_id": {"type": "keyword"},
                    "dataset_name": {"type": "keyword"},
                    "dataset_content": {"type": "text"},
                    "metadata": {"type": "text"}
                }
            }
        }
        
        # Mapping for summary index
        summary_mapping = {
            "mappings": {
                "properties": {
                    "dataset_id": {"type": "keyword"},
                    "dataset_name": {"type": "keyword"},
                    "summary": {"type": "text"},
                    "metadata": {"type": "text"}
                }
            }
        }
        
        # Create indices if they don't exist
        if not self.es.indices.exists(index=self.full_index):
            self.es.indices.create(index=self.full_index, body=full_mapping)
        
        if not self.es.indices.exists(index=self.summary_index):
            self.es.indices.create(index=self.summary_index, body=summary_mapping)
    
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
        Ingest a dataset and its metadata into both indices.
        
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
            
            # Index the full dataset
            self.es.index(
                index=self.full_index,
                id=doc_id,
                body={
                    "dataset_id": doc_id,
                    "dataset_name": dataset_name,
                    "dataset_content": dataset_content,
                    "metadata": metadata_content
                }
            )
            
            # Generate and index the summary
            summary = self._generate_summary(dataset_content)
            self.es.index(
                index=self.summary_index,
                id=doc_id,
                body={
                    "dataset_id": doc_id,
                    "dataset_name": dataset_name,
                    "summary": summary,
                    "metadata": metadata_content
                }
            )
            
            # Refresh indices to make the documents available for search
            self.es.indices.refresh(index=self.full_index)
            self.es.indices.refresh(index=self.summary_index)
            
            return True
        except Exception as e:
            print(f"Error ingesting dataset {dataset_name}: {e}")
            return False
    
    def ingest_multiple(self, dataset_models):
        """
        Ingest multiple datasets into both indices.
        
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
        Query the appropriate index based on configuration.
        
        Args:
            keyword (str): The keyword to search for
            
        Returns:
            list: List of matching dataset results with scores
            float: Time taken for the query in seconds
        """
        start_time = time.time()
        
        if self.use_summaries:
            # Search in the summary index
            response = self.es.search(
                index=self.summary_index,
                body={
                    "query": {
                        "multi_match": {
                            "query": keyword,
                            "fields": ["summary", "metadata"]
                        }
                    }
                }
            )
        else:
            # Search in the full dataset index
            response = self.es.search(
                index=self.full_index,
                body={
                    "query": {
                        "multi_match": {
                            "query": keyword,
                            "fields": ["dataset_content", "metadata"]
                        }
                    }
                }
            )
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Extract dataset info and scores
        hits = response.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits:
            source = hit.get("_source", {})
            results.append({
                "dataset_id": source.get("dataset_id"),
                "dataset_name": source.get("dataset_name"),
                "score": hit.get("_score", 0)
            })
        
        return results, query_time
    
    def get_index_size(self):
        """
        Get the size of the index being used.
        
        Returns:
            int: Size of the index in bytes
        """
        if self.use_summaries:
            stats = self.es.indices.stats(index=self.summary_index)
        else:
            stats = self.es.indices.stats(index=self.full_index)
        
        # Get the size in bytes
        return stats["_all"]["total"]["store"]["size_in_bytes"]
    
    def clear_indices(self):
        """Clear both indices."""
        try:
            self.es.indices.delete(index=self.full_index, ignore=[404])
            self.es.indices.delete(index=self.summary_index, ignore=[404])
            self._create_indices()
            return True
        except Exception as e:
            print(f"Error clearing indices: {e}")
            return False
