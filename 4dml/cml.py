#!/usr/bin/env python2

#    4DML Transformation Utility
#
#    (C) 2006 Silas S. Brown (University of Cambridge Computer Laboratory,
#        Cambridge, UK, http://www.cus.cam.ac.uk/~ssb22 )
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program; see the file COPYING.  If not, write to
#     the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#     Boston, MA 02111-1307, USA.

#!/usr/bin/env python2
# Note: This uses PLY and may create a parsetab.py
# (and requires python 2)

try:
    import jythonHack # first
except ImportError: pass
import xml_in # needed in case running this as main
# (to avoid circular import problems in xmlutil)
import re,lex,yacc,xmlutil
from xmlutil import documentName
from error import TransformError

def cml2xml(str): return xmlutil.tuple2text(cml2tuple(str))
def cml2fs(str):
    return xmlutil.tuple2fourspace(cml2tuple(str))
def cml2xml_embedded(file):
    return cml2xml(cdata_start + file.read() + cdata_end)
def cml2fs_embedded(file):
    return cml2fs(cdata_start + file.read() + cdata_end)

def cml2tuple(str):
    return yacc.parse(documentName+" "+documentParams+\
                      "/("+str+")")

cdata_start = "]]"
cdata_end = "[[cml"
documentParams = "nomarkup no-input"
# (no-input so still works even if top-level element is not
# "document"; this shouldn't break MML because the
# "document" will just be ignored.  Could also use
# allow-empty and include-rest.)
# (**** Not sure what effect this has on the speed.  Could
# have no-input iff not using MML, but that doesn't seem
# right because somebody might use output from mml2xml and
# we don't want two different behaviours)

tokens = ( 'word', 'quoted', 'comma', 'slash', 'equals',
           'lParen', 'rParen','data')
t_ignore = " \t\n"

t_word   = r'[a-zA-Z0-9_-]+'
t_quoted = r'"[\s\S]*?"'
# Using \s\S to represent any char including newlines
t_comma  = r','
t_slash  = r'/'
t_equals = r'='
t_lParen = r'\('
t_rParen = r'\)'

def t_data(t):
    t.value = t.value[len(cdata_start):-len(cdata_end)]
    return t
t_data.__doc__ = re.escape(cdata_start) + \
                 r'[\s\S]*?' + re.escape(cdata_end)
# the ? after the * sets non-greedy (minimal) matching

def t_error(t):
    raise TransformError("CML: Illegal character '%s'" % t.value[0])

lex.lex()

def p_statement(t):
    'statement : list'
    if not len(t[1])==1: raise TransformError("CML: Not exactly 1 top-level element")
    t[0] = t[1][0] # a top-level (name,attribs,children)
def p_list(t):
    'list : listItem listRest'
    t[0] = t[1] + t[2] # a list (don't need to turn first item into a list, because it might be a parenthesised list - see below)
def p_listRest(t):
    'listRest : comma list'
    t[0] = t[2]
def p_listRest_epsilon(t):
    'listRest : '
    t[0] = []
def p_listRest_data(t):
    'listRest : data list'
    t[0] = [t[1]] + t[2] # cdata (xmlify done later) (here making first item into a list *** might better to use "insert" if the second is guaranteed to not be re-used)
def p_list_listrest(t):
    'list : listRest'
    t[0] = t[1]
def p_listItem(t): # an element (name,attrs,children)
    # but listItem is always a LIST (in case using
    # parentheses)
    'listItem : word attribs itemRest'
    t[0] = [(t[1],t[2],t[3])]
def p_listItem_quoted(t):
    'listItem : quoted'
    t[0] = [unquote(t[1])] # cdata (turning into a list)
def p_itemRest(t): # itemRest is always a list
    'itemRest : slash listItem'
    t[0] = t[2] # since listItem is always a list
def p_itemRest_epsilon(t):
    'itemRest : '
    t[0] = []
def unquote(str):
    if str[0]=='"' and str[-1]=='"': return str[1:-1]
    else: return str
def p_attribs(t):
    'attribs : word value attribs'
    dict = t[3] # .copy()
    dict[t[1]] = unquote(t[2])
    t[0] = dict
def p_value(t):
    'value : equals wordOrData'
    t[0] = t[2]
def p_wordOrData_word(t):
    'wordOrData : word'
    t[0] = t[1]
def p_wordOrData_quoted(t):
    'wordOrData : quoted'
    t[0] = t[1]
def p_wordOrData_data(t):
    'wordOrData : data'
    t[0] = t[1] # value of an attrib (xmlify done later)
def p_value_epsilon(t):
    'value : '
    t[0] = "1"
def p_attrib_epsilon(t):
    'attribs : '
    t[0] = {}
def p_list_group(t):
    'listItem : lParen list rParen'
    t[0] = t[2]

def p_error(t):
    if t: raise TransformError("CML: Syntax error at '%s'" % t.value)
    else: raise TransformError("CML: Parse error (EOF?)")

yacc.yacc(debug=0)
import parsetab # jythonc hack

# import version
if __name__ == "__main__":
    import sys
    print cml2xml_embedded(sys.stdin)
