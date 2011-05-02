#!/usr/bin/env python2

import cherrypy
import urllib
import json

class AnalyzeBox:
  def __init__(self):
    #self.data = data
    self.path = 'http://localhost:8081'
    self.colors = {"neg":"FF0000", "pos":"00FF00", "unknown":"000000"}
    self.weights = {}

  def index(self, text=""):
    text.strip()
    weight_request = urllib.urlopen("{}/weights/?words={}".format(self.path, urllib.quote_plus(text)))
    self.weights = json.loads(weight_request.next())
    weight_request.close()
    classification = urllib.urlopen("{}/classify/?words={}".format(self.path, urllib.quote_plus(text)))
    self.classification = json.loads(classification.next())
    classification.close()
    print self.classification
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
{key}""".format(text=text, colored_text=self.color(text.split()), key="\n".join(["<font color='{}'>{}</font><br/>".format(value,key) for key, value in self.colors.items()]), classification=self.classification)

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
      label, weight = self.weights[word]
      #print "{}: weight {}, label {}".format(word, weight, label)
      color = "000000"
      if (weight > self.weights['largest weights'][label]/5):
        color = self.colors[label]
      output = output + " <font color='{}'>{}({:.2f})</font>".format(color, word, weight)
    return output

  def print_classifiers(self, classifiers):
    return "filler"


def word_feats(words):
  return dict([(word, True) for word in words])

cherrypy.quickstart(AnalyzeBox())

