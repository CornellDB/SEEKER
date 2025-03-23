from gensim.models import Word2Vec

class EmbeddingTrainer:
    def __init__(self, sentences=[], vector_size=100, window=5, min_count=1, workers=4):
        self.sentences = sentences
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.workers = workers
        self.model = None

    def train(self, epochs=10):
        self.model = Word2Vec(
            sentences=self.sentences,
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            workers=self.workers,
            epochs=epochs
        )
        self.model.train(self.sentences, total_examples=self.model.corpus_count, epochs=epochs)

    def save_model(self, file_path):
        if self.model is not None:
            self.model.save(file_path)
    
    def load_model(self, file_path):
        self.model = Word2Vec.load(file_path)
        return self.model
    
    def get_similar_words(self, word,  topn=10):
        if self.model is not None:
            return self.model.wv.most_similar(word, topn=topn)
        return []