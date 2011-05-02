#!/usr/bin/python2

import cherrypy
from nltk.compat import defaultdict

def word_feats(words):
  return dict([(word, True) for word in words])

class Data:
  def __init__(self):
    self.feature_weights = defaultdict(lambda: ('default',0))
    self.largest = defaultdict(lambda: ('default',0))
    self.train()
    self.calculate_weights()
  def train(self):
    print "Starting to train the data"
    import nltk.classify.util
    from nltk.classify import NaiveBayesClassifier
    from nltk.corpus import movie_reviews
    import random

    self.negids = movie_reviews.fileids('neg')
    self.posids = movie_reviews.fileids('pos')
    #random.shuffle(self.negids)
    #random.shuffle(self.posids)

    self.negfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'neg') for f in self.negids]
    self.posfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'pos') for f in self.posids]

    self.negcutoff = len(self.negfeats)*3/4
    self.poscutoff = len(self.posfeats)*3/4

    self.trainfeats = self.negfeats[:self.negcutoff] + self.posfeats[:self.poscutoff]
    self.testfeats = self.negfeats[self.negcutoff:] + self.posfeats[self.poscutoff:]

    self.classifier = NaiveBayesClassifier.train(self.trainfeats)
    print 'accuracy:', nltk.classify.util.accuracy(self.classifier, self.testfeats)
    self.classifier.show_most_informative_features()
  
  #def classify_word(self, word):
  #  return self.classifier.classify({word:True})
  #classify_word.exposed = True
  def classify(self, words):
    words_dict = dict([(word, True) for word in words])
    return self.classifier.classify(words_dict)
  classify.exposed = True

  def calculate_weights(self):
    print "Calculating weights"
    cpdist = self.classifier._feature_probdist
    for (fname, fval) in self.list_all_features():
      def label_prob(l):
        return cpdist[l,fname].prob(fval)
      labels = sorted([l for l in self.classifier._labels
        if fval in cpdist[l, fname].samples()], key=label_prob)
      if len(labels) == 1: continue
      l0 = labels[0]
      l1 = labels[-1]
      if cpdist[l0, fname].prob(fval) == 0:
        weight = "INF"
        print "inf!"
        self.largest[l1] = (fname, weight)
      else:
        weight = (cpdist[l1, fname].prob(fval))/(cpdist[l0, fname].prob(fval))
      if self.feature_weights[fname][1] < weight:
        self.feature_weights[fname] = (l1, weight)
      if self.largest[l1][1] < weight and self.largest[l1][1] != "INF":
        print "{}: {}, {} is larger than {}".format(l1, fname, weight, self.largest[l1])
        self.largest[l1] = (fname, weight)

  def list_all_features(self):
    features = set()
    for (label, fname), probdist in self.classifier._feature_probdist.items():
      for fval in probdist.samples():
        features.add((fname, fval))
    return features

  def largest_weights(self):
    return self.largest
  largest_weights.exposed = True



  def weights(self, words):
    words = words.split()
    weights = {}

    for word in words:
      weights[word] = self.weight(word)
    return weights
  weights.exposed = True

  def weight(self, word):
    try:
      weight = self.feature_weights[word]
    except KeyError:
      weight = ('unknown', 1)
    return weight
  weight.exposed = True

  def old_weight(self, word):
    print "Weighing: {}".format(word)
    cpdist = self.classifier._feature_probdist
    def label_prob(label, name, value):
      return cpdist[label, name].prob(value)

    labels = []
    for label in self.classifier._labels:
      try:
        #if word in cpdist[label, word.encode('ascii')].samples():
        labels.append([label_prob(label, word, True), label])
        #else:
        #  return (1, 'unknown')
      except KeyError:
        print "Key Error: {}".format(word)
        return ('unknown', 1)

    labels = sorted(labels)
    return (labels[-1][1], labels[-1][0]/labels[0][0])

if __name__ == "__main__":
  data = Data()
  #data.train()
  #app = cherrypy.tree.mount(data, script_name='/')
  conf = {'tools.json_out.on':True, 'server.socket_port':8081}
  cherrypy.config.update(conf)
  cherrypy.quickstart(data)
