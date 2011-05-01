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
    return self.data.classify_word(word)

  def color(self, words, style_method=polarize):
    output = ""
    for word in words:
      output = output + " <font color='{}'>{}</font>".format(self.colors[style_method(self,word)], word)
    return output

  def print_classifiers(self, classifiers):
    return "filler"


def word_feats(words):
  return dict([(word, True) for word in words])

import data_server

stuff = data_server.Data()
stuff.train()
cherrypy.quickstart(AnalyzeBox(stuff))

