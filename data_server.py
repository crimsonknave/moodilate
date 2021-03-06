#!/usr/bin/python2

import cherrypy
import sys
from nltk.compat import defaultdict
import nltk.classify.util, nltk.metrics
from nltk.classify import NaiveBayesClassifier, apply_features
from nltk.corpus import movie_reviews
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder
import itertools
import random
import datetime
import json



class Data:
  def text_feats(self, text):
    document_words = set(text)
    features = {}
    for word in self.word_features:
      features['contains({})'.format(word)] = (word in document_words)
    return features

  def word_feats(self, words):
    return dict([(word, True) for word in self.pruned_filter(words)])

  def stopword_filtered_word_feats(self, words):
    return dict([(word, True) for word in words if word not in self.stopset])

  def bigram_word_feats(self, words, score_fn=nltk.metrics.BigramAssocMeasures.chi_sq, n=200):
    bigram_finder = BigramCollocationFinder.from_words(words)
    bigrams = bigram_finder.nbest(score_fn, n)
    return dict([(ngram, True) for ngram in self.pruned_filter(itertools.chain(words, bigrams))])

  def first_last_word_feats(self, words):
    return {"first": words[0], "last": words[-1]}

  def pruned_filter(self, words):
    if self.trained:
      important_features = set(self.feature_weights.keys())
      return [word for word in words if (word, True) in important_features]
    else:
      return words

  def parse_text(self, raw):
    tokens = [token.lower() for token in nltk.wordpunct_tokenize(raw)]
    print len(tokens)
    return tokens

  def __init__(self):
    self.feature_weights = defaultdict(lambda: ('default',0))
    self.trained = False
    self.largest = defaultdict(lambda: ('default name', 'default value',0))
    self.stopset = set(stopwords.words('english'))
    self.my_feats = self.bigram_word_feats
    self.train(self.my_feats)
    #self.book_train(self.my_feats)
    self.calculate_weights()
    self.train(self.my_feats)

  def book_train(self, feats):

    documents = [(list(movie_reviews.words(fileid)), category)
                  for category in movie_reviews.categories()
                  for fileid in movie_reviews.fileids(category)]

    random.shuffle(documents)

    self.all_words = nltk.FreqDist(w.lower() for w in movie_reviews.words() if w not in self.stopset)
    self.word_features = self.all_words.keys()[:1000]

    featuresets = [(self.text_feats(d), c) for (d,c) in documents]
    train_set, test_set = featuresets[200:], featuresets[:200]
    self.classifier = nltk.NaiveBayesClassifier.train(train_set)

    print nltk.classify.accuracy(self.classifier, test_set)

    self.classifier.show_most_informative_features(10)


  def train(self, feats):
    print "Starting to train the data"
    start = datetime.datetime.now()

    print "setting the ids", datetime.datetime.now()
    self.negids = movie_reviews.fileids('neg')
    self.posids = movie_reviews.fileids('pos')
    #random.shuffle(self.negids)
    #random.shuffle(self.posids)
    ##self.reviews = ([(movie_reviews.words(fileids=[f]), 'neg') for f in self.negids] +
        ##[(movie_reviews.words(fileids=[f]), 'pos') for f in self.posids])
    ##random.shuffle(self.reviews)

    ##self.train_set = apply_features(feats, self.reviews[len(self.reviews)*1/4:])
    ##self.test_set = apply_features(feats, self.reviews[:len(self.reviews)*1/4])

    print "setting the feats", datetime.datetime.now()
    self.negfeats = [(feats(movie_reviews.words(fileids=[f])), 'neg') for f in self.negids]
    self.posfeats = [(feats(movie_reviews.words(fileids=[f])), 'pos') for f in self.posids]

    self.negcutoff = len(self.negfeats)*3/4
    self.poscutoff = len(self.posfeats)*3/4

    print "setting the train/test", datetime.datetime.now()
    self.trainfeats = self.negfeats[:self.negcutoff] + self.posfeats[:self.poscutoff]
    self.testfeats = self.negfeats[self.negcutoff:] + self.posfeats[self.poscutoff:]

    print "training", datetime.datetime.now()
    self.classifier = NaiveBayesClassifier.train(self.trainfeats)
    ##self.classifier = NaiveBayesClassifier.train(self.train_set)
    self.refsets = defaultdict(set)
    self.testsets = defaultdict(set)

    print "accuracy stuff", datetime.datetime.now()
    for i, (feats, label) in enumerate(self.testfeats):
    ##for i, (feats, label) in enumerate(self.test_set):
      self.refsets[label].add(i)
      observed = self.classifier.classify(feats)
      self.testsets[observed].add(i)

    end = datetime.datetime.now()
    print "Training lasted for ", end-start


    print 'accuracy:', nltk.classify.util.accuracy(self.classifier, self.testfeats)
    ##print 'accuracy:', nltk.classify.util.accuracy(self.classifier, self.test_set)
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
    feature_dict = self.my_feats(self.parse_text(words))
    print "Class_dict is:", feature_dict
    return self.classifier.classify(feature_dict)
  classify.exposed = True

  def calculate_weights(self):
    print "Calculating weights"
    start = datetime.datetime.now()
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
        self.largest[l1] = (fname, fval, weight)
      else:
        weight = (cpdist[l1, fname].prob(fval))/(cpdist[l0, fname].prob(fval))
      if self.feature_weights[(fname, fval)][1] < weight:
        self.feature_weights[(fname, fval)] = (l1, weight)
      if self.largest[l1][2] < weight and self.largest[l1][2] != "INF":
        #print "{}: {}, {} is larger than {}".format(l1, fname, weight, self.largest[l1])
        self.largest[l1] = (fname, fval, weight)

    end = datetime.datetime.now()
    print "Weighing lasted for ", end-start

    print "Pruning the weights"
    start = datetime.datetime.now()
    total = len(self.feature_weights)
    useful_feature_weights = {}
    for feature, (label, weight) in self.feature_weights.items():
      if weight > self.largest[label][2]/10 and label in self.classifier._labels:
        useful_feature_weights[feature] = (label, weight)
    self.feature_weights = useful_feature_weights
    print "feature_weights had {} entires it now has {}".format(total, len(self.feature_weights))
    end = datetime.datetime.now()
    print "Pruning lasted for ", end-start

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
    feature_dict = self.my_feats(self.parse_text(words))
    weights = {}

    for feature, value in feature_dict.items():
      # We encode the tuple as json because json hashes require strings as keys
      label, weight = self.weight((feature, value))
      print label, weight
      weights[json.dumps((feature, value))] = (label, weight)
    print weights
    return weights
  weights.exposed = True

  def weight(self, feature):
    print "Looking for the weight of ", feature
    try:
      weight = self.feature_weights[feature]
    except KeyError:
      weight = ('neutral', 1)
    print "Found the weight for {} to be {}".format(feature, weight)
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
        #  return (1, 'neutral')
      except KeyError:
        print "Key Error: {}".format(word)
        return ('neutral', 1)

    labels = sorted(labels)
    return (labels[-1][1], labels[-1][0]/labels[0][0])

if __name__ == "__main__":
  data = Data()
  #data.train()
  #app = cherrypy.tree.mount(data, script_name='/')
  conf = {'tools.json_out.on':True, 'server.socket_port':1234}
  cherrypy.config.update(conf)
  cherrypy.quickstart(data)
