#!/usr/bin/env python2

import cherrypy
import urllib
import json

class AnalyzeBox:
  def __init__(self):
    #self.data = data
    self.path = 'http://localhost:8081'
    self.colors = {"neg":"FF0000", "pos":"00FF00", "minor":"000000"}

  def index(self, text=""):
    text.strip()
    weight_request = urllib.urlopen("{}/weights/?words={}".format(self.path, urllib.quote_plus(text)))
    weights = json.loads(weight_request.next())
    weight_request.close()
    largest_weights_request = urllib.urlopen(self.path+"/largest_weights")
    largest_weights = json.loads(largest_weights_request.next())
    largest_weights_request.close()
    classification_request = urllib.urlopen("{}/classify/?words={}".format(self.path, urllib.quote_plus(text)))
    classification = json.loads(classification_request.next())
    classification_request.close()
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
{key}""".format(text=text, colored_text=self.color(text.split(),weights, largest_weights), key="\n".join(["<font color='{}'>{}</font><br/>".format(value,key) for key, value in self.colors.items()]), classification=classification)

  index.exposed = True

  def polarize(self, word): 
    try:
      kind = self.data.classifier._feature_probdist[word]
    except KeyError:
      kind = "unknown"
    return kind

  def color(self, words, weights, largest):
    output = ""
    for word in words:
      label, weight = weights[word.lower()]
      #print "{}: weight {}, label {}".format(word, weight, label)
      color = "000000"
      try:
        if (weight > largest[label][1]/10):
          color = self.colors[label]
      except KeyError:
        pass
      output = output + " <font color='{}'>{}({:.2f})</font>".format(color, word, weight)
    return output

  def print_classifiers(self, classifiers):
    return "filler"


def word_feats(words):
  return dict([(word, True) for word in words])

cherrypy.quickstart(AnalyzeBox())

