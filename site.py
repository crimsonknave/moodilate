#!/usr/bin/env python2

import cherrypy

class AnalyzeBox:
  def __init__(self, data):
    self.data = data
    self.colors = {"neg":"FF0000", "pos":"00FF00"}

  def index(self, text=""):
    text.strip()
    return """
<form name="input" action="index" method="get">
Text: <textarea id="source" name="text" rows="10" cols="50">
{}</textarea>
<input type="submit" value="Analyze"/>
</form>
This is what you submitted:
{}
<br/>
Key:
<br/>
{}""".format(text, self.color(text.split()), "\n".join(["<font color='{}'>{}</font><br/>".format(value,key) for key, value in self.colors.items()]))

  index.exposed = True

  def polarize(self, word): 
    return self.data.classify(word)

  def color(self, words, style_method=polarize):
    output = ""
    for word in words:
      output = output + " <font color='{}'>{}</font>".format(self.colors[style_method(self,word)], word)
    return output


      

  def print_classifiers(self, classifiers):
    return "filler"

class Data:
  def train(self):
    import nltk.classify.util
    from nltk.classify import NaiveBayesClassifier
    from nltk.corpus import movie_reviews
    import random

    def word_feats(words):
      return dict([(word, True) for word in words])

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
  
  def classify(self, word):
    return self.classifier.classify({word:True})



stuff = Data()
stuff.train()
cherrypy.quickstart(AnalyzeBox(stuff))

