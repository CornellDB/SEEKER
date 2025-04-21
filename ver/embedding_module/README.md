# VER - Embedding Module

The embedding module is used to create word embeddings for column attributes and examples. It iterates through all data ingested by the index and outputs embeddings to find similar words throughout tables.

## Processor

The processor sifts through all csv files specified by a data folder and combines column headers and data rows as "sentences". These are used to provide contextual relevance in the embedding trainer.

## Embedding Trainer

The trainer takes in a list of "sentences" and trains a model for obtaining similar words given a specific input. 

## Usage

```
dir = "./dir/to/csvs"
processor = Processor(dir)
sentences = processor.process()

trainer = EmbeddingTrainer(sentences)
trainer.train()

related_words = trainer.get_similar_words("word")
```

The model can also be saved and loaded to train more datasets using the `load_model()` and `save_model()`.
