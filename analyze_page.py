#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import cherrypy
import urllib, urllib2
import json
from collections import defaultdict
from operator import itemgetter
import datetime

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
    #print "row", row
    html += "  <tr>\n"
    for column in row:
      if column:
        html += "    <td>{} = {} : {:.2f}</td>\n".format(column[0][0], column[0][1], column[1])
      else:
        html += "    <td></td>\n"
    html += "  </tr>\n"
  html += "</table>\n"

  #print html
  return html

def none_to_string(*args):
  "   used with map to emulate the builtin zip, but replaces emptyness with ''"
  return ["" if x == None else x for x in args]

def decode_keys(encoded_dict):
  #print "encoded_dict", encoded_dict
  new_dict = {}
  for key, value in encoded_dict.items():
    new_key = json.loads(key)
    #print new_key
    new_dict[tuplify(new_key)] = value
  return new_dict

class AnalyzeBox:
  def __init__(self):
    #self.data = data
    self.path = 'http://localhost:1234'
    self.colors = {"neg":"FF0000", "pos":"00FF00", "neutral":"000000"}

  def index(self, text=""):
    start = datetime.datetime.now()
    word_count = len(text.split())
    text.strip()
    text = text.encode('utf-8')
    print "text begins like", text[0:50]
    populated = True if len(text)>0 else False
    if populated:
      values = {'words':text}
      data = urllib.urlencode(values)
      w_start = datetime.datetime.now()
      weight_request = urllib2.Request("{}/weights".format(self.path), data)
      weight_resp = urllib2.urlopen(weight_request)
      weights = decode_keys(json.loads(weight_resp.read()))
      #print "weights", weights
      w_end = datetime.datetime.now()
      #largest_weights_request = urllib.urlopen(self.path+"/largest_weights")
      #largest_weights = json.loads(largest_weights_request.next())
      #largest_weights_request.close()
      c_start = datetime.datetime.now()
      class_req = urllib2.Request("{}/classify".format(self.path), data)
      class_resp = urllib2.urlopen(class_req)
      classification = json.loads(class_resp.read())
      c_end = datetime.datetime.now()
      influencers = label_columns(self.influencers(weights))
    else:
      print "unpopulated"
      w_start = datetime.datetime.now()
      w_end = datetime.datetime.now()
      influencers = ""
      classification = ""
      c_start = datetime.datetime.now()
      c_end = datetime.datetime.now()
    formatters={
        'text':text,
        #'key':'\n'.join(["<font color='{}'>{}</font><br/>".format(value,key) for key, value in self.colors.items()]),
        'influencers':influencers,
        'classification':classification
        }

    end = datetime.datetime.now()
    total = end-start
    w_total = w_end-w_start
    c_total = c_end-c_start
    print "Processing {} words lasted {} ({} wps), weights took {} ({} wps), classification took {} ({} wps)".format(word_count, total, word_count/total.total_seconds(), w_total, word_count/w_total.total_seconds(), c_total, word_count/c_total.total_seconds())
    return """
<form name="input" action="moodilate" method="post">
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

  def influencers(self, weights, n=10):
    labels = defaultdict(list)
    for feature in weights.keys():
      label, weight = weights[feature]
      labels[label].append((feature, weight))

    for key, value in labels.items():
      labels[key] = sorted(value,key=itemgetter(1), reverse=True)[:n]
    #print "labels", labels
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

