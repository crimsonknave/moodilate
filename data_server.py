#!/usr/bin/python2

import cherrypy
import sys
from nltk.compat import defaultdict
import nltk.classify.util, nltk.metrics
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import movie_reviews
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder
import itertools
import random



class Data:
  def word_feats(self, words):
    return dict([(word, True) for word in words])

  def stopword_filtered_word_feats(self, words):
    return dict([(word, True) for word in words if word not in self.stopset])

  def bigram_word_feats(self, words, score_fn=nltk.metrics.BigramAssocMeasures.chi_sq, n=200):
    bigram_finder = BigramCollocationFinder.from_words(words)
    bigrams = bigram_finder.nbest(score_fn, n)
    return dict([(ngram, True) for ngram in itertools.chain(words, bigrams)])

  def __init__(self):
    self.feature_weights = defaultdict(lambda: ('default',0))
    self.largest = defaultdict(lambda: ('default',0))
    self.stopset = set(stopwords.words('english'))
    #self.train(self.word_feats)
    #self.train(self.stopword_filtered_word_feats)
    self.my_feats = self.bigram_word_feats
    self.train(self.my_feats)
    self.calculate_weights()
  def train(self, feats):
    print "Starting to train the data"

    self.negids = movie_reviews.fileids('neg')
    self.posids = movie_reviews.fileids('pos')
    #random.shuffle(self.negids)
    #random.shuffle(self.posids)

    self.negfeats = [(feats(movie_reviews.words(fileids=[f])), 'neg') for f in self.negids]
    self.posfeats = [(feats(movie_reviews.words(fileids=[f])), 'pos') for f in self.posids]

    self.negcutoff = len(self.negfeats)*3/4
    self.poscutoff = len(self.posfeats)*3/4

    self.trainfeats = self.negfeats[:self.negcutoff] + self.posfeats[:self.poscutoff]
    self.testfeats = self.negfeats[self.negcutoff:] + self.posfeats[self.poscutoff:]

    self.classifier = NaiveBayesClassifier.train(self.trainfeats)
    self.refsets = defaultdict(set)
    self.testsets = defaultdict(set)

    for i, (feats, label) in enumerate(self.testfeats):
      self.refsets[label].add(i)
      observed = self.classifier.classify(feats)
      self.testsets[observed].add(i)

    print 'accuracy:', nltk.classify.util.accuracy(self.classifier, self.testfeats)
    print 'pos precision:', nltk.metrics.precision(self.refsets['pos'], self.testsets['pos'])
    print 'pos recall:', nltk.metrics.recall(self.refsets['pos'], self.testsets['pos'])
    print 'neg precision:', nltk.metrics.precision(self.refsets['neg'], self.testsets['neg'])
    print 'neg recall:', nltk.metrics.recall(self.refsets['neg'], self.testsets['neg'])
    self.classifier.show_most_informative_features()
    self.trained = True
  
  #def classify_word(self, word):
  #  return self.classifier.classify({word:True})
  #classify_word.exposed = True
  def classify(self, words):
    #words = words.split()
    #words_dict = dict([(word, True) for word in words])
    class_dict = self.my_feats(words.split())
    print "Class_dict is:", class_dict
    return self.classifier.classify(class_dict)
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
        #print "{}: {}, {} is larger than {}".format(l1, fname, weight, self.largest[l1])
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
      weight = self.feature_weights[word.lower()]
    except KeyError:
      weight = ('minor', 1)
    #print "Found the weight for {} to be {}".format(word, weight)
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
        #  return (1, 'minor')
      except KeyError:
        print "Key Error: {}".format(word)
        return ('minor', 1)

    labels = sorted(labels)
    return (labels[-1][1], labels[-1][0]/labels[0][0])

if __name__ == "__main__":
  data = Data()
  #data.train()
  #app = cherrypy.tree.mount(data, script_name='/')
  conf = {'tools.json_out.on':True, 'server.socket_port':8081}
  cherrypy.config.update(conf)
  cherrypy.quickstart(data)
