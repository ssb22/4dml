#!/usr/bin/env python2

#    4DML Transformation Utility
#
#    (C) 2002-2006 Silas S. Brown (University of Cambridge Computer Laboratory,
#        Cambridge, UK, http://ssb22.user.srcf.net )
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Miscellaneous XML utilities

# imports have been moved to end of file (avoid circular
# imports problem with mml2xml)

def setup_events_to_text():
    global start_element,end_element,char_data
    global start_xml,end_xml
    start_element=h_start_element;end_element=h_end_element
    char_data=h_char_data
    start_xml=h_start_xml;end_xml=h_end_xml
def setup_events_to_text_raw():
    global start_xml
    setup_events_to_text()
    start_xml=h_start_xml_raw # no "<?xml ..." tag

def setup_events_to_fourspace(linkName=None):
    global start_element,end_element,char_data
    global start_xml,end_xml
    global hacky_global_link_name
    start_element = xml_in.start_element
    end_element = xml_in.end_element
    char_data = xml_in.char_data
    start_xml = alt_start_xml
    end_xml = alt_end_xml
    hacky_global_link_name = linkName

# Convert a tuple-like list into XML events:
def tuple2events(tuple):
    start_xml()
    inner_tuple2events(tuple)
    return end_xml()

def inner_tuple2events(tuple):
    (name, attribs, children) = tuple
    start_element(name,attribs)
    for i in children:
        if type(i)==types.StringType or type(i)==types.UnicodeType: char_data(i)
        else: inner_tuple2events(i)
    end_element(name)

def tuple2text(tuple):
    setup_events_to_text()
    return tuple2events(tuple)
def tuple2text_raw(tuple):
    setup_events_to_text_raw()
    return tuple2events(tuple)

def tuple2fourspace(tuple):
    # Go via Expat if available, otherwise go direct
    if hasattr(xml_in,'xml'): return xml_in.xmlStringToFourspace(tuple2text(tuple))
    else:
        setup_events_to_fourspace()
        return tuple2events(tuple)

# Convert XML events into textual XML:
class Holder:
    pass
holder = Holder()
hadContents = 1
def h_start_element(name,attr):
    if not name: return
    global hadContents
    if not hadContents: holder.out.write(">")
    holder.out.write("<"+name)
    for (k,v) in attr.items():
        holder.out.write(" "+k+"=\""+limited_xmlify(v)+"\"")
        # NOT xmlify(v) - assume the user knows about XML and can write "&#10;" etc in attributes (**** is this the best place to put that idea?  It is documented in cml, and matrix.py doesn't use it, so should be ok)
    hadContents = 0
def h_end_element(name):
    if not name: return
    global hadContents
    if not hadContents:
        holder.out.write("/>")
        hadContents = 1 # for the parent element
    else: holder.out.write("</"+name+">")
def h_char_data(data):
    global hadContents
    if not hadContents:
        hadContents = 1
        holder.out.write(">")
    holder.out.write(xmlify(data))
# A couple of extras:
def h_start_xml():
    h_start_xml_raw()
    holder.out.write("<?xml version=\"1.0\"?>\n")
def h_start_xml_raw():
    from cStringIO import StringIO # here so the embedded
    # version can run anyway if StringIO not available
    holder.out = StringIO()
def h_end_xml():
    holder.out.write("\n")
    r = holder.out.getvalue()
    holder.out.close()
    return r

# Pass XML events to xml_in
def alt_start_xml():
    xml_in.state=xml_in.ParserState(1,0,hacky_global_link_name) # *** (only 1 (recognise special attributes) if doing mml and not if doing cml - fix this sometime)
def alt_end_xml():
    xml_in.state.cleanup()
    return xml_in.state.result

documentName = "document"

def xmlify(str):
    str = string.replace(str,"&","&amp;")
    return limited_xmlify(str)

def limited_xmlify(str):
    # xmlify everything except & (assume user knows how to
    # use &) (**** could be better documented)
    str = string.replace(str,"<","&lt;")
    str = string.replace(str,">","&gt;")
    str = string.replace(str,"\"","&quot;")
    return str

import xml_in
import string,types
