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

  def weight(self, word):
    cpdist = self.classifier._feature_probdist
    def label_prob(label, name, value):
      return cpdist[label, name].prob(value)

    labels = []
    for label in self.classifier._labels:
      print label
      try:
        #if word in cpdist[label, word.encode('ascii')].samples():
        labels.append([label_prob(label, word, True), label])
        #else:
        #  return (1, 'unknown')
      except KeyError:
        print "Key Error"
        return ('unknown', 1)

    labels = sorted(labels)
    print labels
    return (labels[-1][1], labels[-1][0]/labels[0][0])



    try:
      asdf
    except KeyError:
      return 


