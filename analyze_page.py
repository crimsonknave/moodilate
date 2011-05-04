#!/usr/bin/env python2

import cherrypy
import urllib
import json
from collections import defaultdict
from operator import itemgetter

def tuplify(tup):
  """ Taken from http://stackoverflow.com/questions/1014352/how-do-i-convert-a-nested-tuple-of-tuples-and-lists-to-lists-of-lists-in-python with only a name change"""
  if isinstance(tup, (list, tuple)):
    return tuple([tuplify(i) for i in tup])
  return tup

def label_columns(d):
  html = "<table>\n<tr>\n"
  for label in d.keys():
    html += "  <th>{}</th>\n".format(label)
  for row in map(none_to_string, *d.values()):
    print "row", row
    html += "  <tr>\n"
    for column in row:
      html += "    <td>{}</td>\n".format(column)
    html += "  </tr>\n"
  html += "</table>\n"

  print html
  return html

def none_to_string(*args):
  "   used with map to emulate the builtin zip, but replaces emptyness with ''"
  return ["" if x == None else x for x in args]

def decode_keys(encoded_dict):
  print "encoded_dict", encoded_dict
  new_dict = {}
  for key, value in encoded_dict.items():
    new_key = json.loads(key)
    print new_key
    new_dict[tuplify(new_key)] = value
  return new_dict

class AnalyzeBox:
  def __init__(self):
    #self.data = data
    self.path = 'http://localhost:1234'
    self.colors = {"neg":"FF0000", "pos":"00FF00", "neutral":"000000"}

  def index(self, text=""):
    text.strip()
    populated = True if len(text)>0 else False
    if populated:
      weight_request = urllib.urlopen("{}/weights/?words={}".format(self.path, urllib.quote_plus(text)))
      weights = decode_keys(json.loads(weight_request.next()))
      weight_request.close()
      print "weights", weights
      largest_weights_request = urllib.urlopen(self.path+"/largest_weights")
      largest_weights = json.loads(largest_weights_request.next())
      largest_weights_request.close()
      classification_request = urllib.urlopen("{}/classify/?words={}".format(self.path, urllib.quote_plus(text)))
      classification = json.loads(classification_request.next())
      classification_request.close()
      influencers = label_columns(self.influencers(weights))
    else:
      influencers = ""
      classification = ""
    formatters={
        'text':text,
        #'key':'\n'.join(["<font color='{}'>{}</font><br/>".format(value,key) for key, value in self.colors.items()]),
        'influencers':influencers,
        'classification':classification
        }
    return """
<form name="input" action="index" method="get">
Text: <textarea id="source" name="text" rows="10" cols="50">
{text}</textarea>
<input type="submit" value="Analyze"/>
</form>
Your text was {classification}<br/>
The most significant parts were:
<br/>
{influencers}
<br/>""".format(**formatters)

  index.exposed = True

  def polarize(self, word): 
    try:
      kind = self.data.classifier._feature_probdist[word]
    except KeyError:
      kind = "unknown"
    return kind

  def influencers(self, weights, n=5):
    labels = defaultdict(list)
    for feature in weights.keys():
      label, weight = weights[feature]
      labels[label].append((feature, weight))

    for key, value in labels.items():
      labels[key] = sorted(value,key=itemgetter(1), reverse=True)[:n]
    print "labels", labels
    return labels


  def color(self,  weights, largest):
    """ attempts to color the inputs based on weight and label."""
    output = ""
    for feature in weights.keys():
      label, weight = weights[feature]
      print feature, label, weight
      #print "{}: weight {}, label {}".format(word, weight, label)
      color = "000000"
      try:
        if (weight > largest[label][1]/10):
          color = self.colors[label]
      except KeyError:
        pass
      output = output + " <font color='{}'>{}({:.2f})</font>".format(color, feature, weight)
    return output

  def print_classifiers(self, classifiers):
    return "filler"


def word_feats(words):
  return dict([(word, True) for word in words])

conf = {'server.socket_port':4321}
cherrypy.config.update(conf)
cherrypy.quickstart(AnalyzeBox())

