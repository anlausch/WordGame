import gensim
import os

class Predictor:
    def __init__(self):
        print("Predictor initialized.")

    def load_embeddings(self, path="./embeddings/german.model"):
        if os.name != 'nt':
            self.embeddings = gensim.models.KeyedVectors.load_word2vec_format(path, binary=True)
        else:
            self.embeddings = gensim.models.Word2Vec.load_word2vec_format(path, binary=True)


    def predict(self, text=""):
        print("Predicting")
        return self.embeddings.most_similar(text)

def main():
    predictor = Predictor()
    predictor.load_embeddings()
    print(predictor.embeddings[0])

if __name__ == "__main__":
    main()