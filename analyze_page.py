#!/usr/bin/env python2

import cherrypy

class AnalyzeBox:
  def __init__(self, data):
    self.data = data
    self.colors = {"neg":"FF0000", "pos":"00FF00", "unknown":"000000"}

  def index(self, text=""):
    text.strip()
    return """
<form name="input" action="index" method="get">
Text: <textarea id="source" name="text" rows="10" cols="50">
{text}</textarea>
<input type="submit" value="Analyze"/>
</form>
Your text was {classification}<br/>
This is what you submitted:
{colored_text}
<br/>
Key:
<br/>
{key}""".format(text=text, colored_text=self.color(text.split()), key="\n".join(["<font color='{}'>{}</font><br/>".format(value,key) for key, value in self.colors.items()]), classification=self.data.classify(word_feats(text.split())))

  index.exposed = True

  def polarize(self, word): 
    try:
      kind = self.data.classifier._feature_probdist[word]
    except KeyError:
      kind = "unknown"
    return kind

  def color(self, words):
    output = ""
    for word in words:
      label, weight = self.data.weight(word)
      #print "{}: weight {}, label {}".format(word, weight, label)
      output = output + " <font color='{}'>{}({:.2f})</font>".format(self.colors[label], word, weight)
    return output

  def print_classifiers(self, classifiers):
    return "filler"


def word_feats(words):
  return dict([(word, True) for word in words])

import data_server

stuff = data_server.Data()
stuff.train()
cherrypy.quickstart(AnalyzeBox(stuff))

