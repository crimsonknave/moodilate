#!/usr/bin/python2

def word_feats(words):
  return dict([(word, True) for word in words])

class Data:
  def train(self):
    import nltk.classify.util
    from nltk.classify import NaiveBayesClassifier
    from nltk.corpus import movie_reviews
    import random

    self.negids = movie_reviews.fileids('neg')
    self.posids = movie_reviews.fileids('pos')
    random.shuffle(self.negids)
    random.shuffle(self.posids)

    self.negfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'neg') for f in self.negids]
    self.posfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'pos') for f in self.posids]

    self.negcutoff = len(self.negfeats)*3/4
    self.poscutoff = len(self.posfeats)*3/4

    self.trainfeats = self.negfeats[:self.negcutoff] + self.posfeats[:self.poscutoff]
    self.testfeats = self.negfeats[self.negcutoff:] + self.posfeats[self.poscutoff:]

    self.classifier = NaiveBayesClassifier.train(self.trainfeats)
    print 'accuracy:', nltk.classify.util.accuracy(self.classifier, self.testfeats)
    self.classifier.show_most_informative_features()
  
  def classify_word(self, word):
    return self.classifier.classify({word:True})
  def classify(self, words_dict):
    return self.classifier.classify(words_dict)

