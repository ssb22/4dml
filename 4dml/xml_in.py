#!/usr/bin/env python2

#    4DML Transformation Utility
#
#    (C) 2002-2006 Silas S. Brown (University of Cambridge Computer Laboratory,
#        Cambridge, UK, http://ssb22.user.srcf.net )
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

# Search **** for things that need doing

import os
try:
    if os.environ.has_key("no_expat"): raise ImportError
    import xml.parsers.expat
# except ImportError:
except: # jython hack
    # manage as best as we can
    import sys, version
    sys.stderr.write("Warning: Expat parser not loaded\n")

import types
from nspace import N_Space
import fourspace
# don't use "from fourspace import FourSpace" because we
# might be in a cycle (in which case that 'fourspace' will
# refer to an empty module under initialisation and it won't
# yet have the class 'FourSpace')
from dimens import scopeDimension
from sys import stdin
from string import whitespace,lower
from error import TransformError
from str_unique import globalUniquifier
# (uniquifier: won't re-assign to thread-safe just yet, so
# doesn't really matter that ref is copied by that line)

# Special XML attributes for overlapping elements
# (these are only processed if asked for)
incAttrib = "_IncrementPos" # increment position # of an
# element further up the tree (element name is THIS
# element's elem name; this element is ignored)
resetAttrib = "_SetPos" # similar, but reset the position #
# to the given value (e.g. 1)
renameAttrib = "_Rename" # change elem name (NB use new name
# next time, & rename back before close (hacky, sorry))
notFinishedAttrib="_Unfinished" # This position-setting is
# not the whole re-positioning; don't write a blank element
initPosAttrib="_InitPos" # Initial posn # of THIS element
# (not one further up the tree)
# **** Don't like this use of reserved words

class ParserState:
    def __init__(self, recogniseSpecialAttributes = 0,
                 recogniseRowspan = 0,
                 linkName = None):
        self.recogniseSpecialAttributes = recogniseSpecialAttributes
        self.recogniseRowspan = recogniseRowspan
        self.positions = [1] # Positions of tags among peers
        self.spanSkips = [] # for rowspan/colspan etc
        self.spanSkips.append([]) ; self.spanSkips.append([]) # 2 in case someone writes COLSPAN etc at top level
        self.cursor = N_Space(3) # for writing to 'result'
        self.result = fourspace.FourSpace()
        self.cdata = ""
        self.had_cdata = 0 # see below (don't call it
        # hadCData - Python gets confused) (update: problem
        # is that it wasn't in a 'context' - seems global
        # vars need to be updated in-place, not reassigned
        # <??? this comment seems to have been mangled>
        self.maybe_remove = None # see below
        self.maybe_remove_points = N_Space(4)
        self.justHadIncrement = 0
        # self.removeList = []
        self.inAttributes = 0
        self.expect_endelement = 0 # for special attributes
        if linkName:
            self.linker=StringLinker()
            self.linker.linkName = linkName
            self.linker.linkDepth = 2 # **** hard-coded !?
            # (2 because 1 would give more than one root)
        else: self.linker = None
        self.lastElementWasUnfinished = 0
    def do_maybe_remove(self):
        if self.maybe_remove:
            # self.removeList.append(self.maybe_remove)
            # if len(self.removeList)>10: self.cleanup()
            # (batched up for cleanup(), so less complexity
            # with large input files - don't have to call
            # subSection() so often)
            self.result.removePoints(self.maybe_remove_points.getPoints())
            self.maybe_remove_points.thePoints.clear() # naughty
            self.maybe_remove = None
    def cleanup(self):
        # self.result.removePoints(self.result.subSection(scopeDimension,self.removeList).getPoints())
        # self.removeList = []
        pass

# I don't like globals, but expat needs call-back functions
global state
# state = ParserState() # NO! because fourspace might not yet be initialised - we'll construct it later
state = None

def init_state(recogniseSpecialAttributes = 0,
               recogniseRowspan = 0,
               linkName = None):
    global state
    state=ParserState(recogniseSpecialAttributes,recogniseRowspan,linkName)
    p = xml.parsers.expat.ParserCreate("UTF-8")
    # (supports: UTF-8, UTF-16, ISO-8859-1, ASCII.
    # NB o/p might be Unicode or UTF-8, depending on version
    # (can override if necessary))
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    try:
        p.buffer_text = True # might speed things up in Python 2.3+
    except: pass
    # **** Need DefaultHandler() + entities etc
    return p

def start_element(name, attributes):
    # Start a new element
    something_written = state.cdata # may be an increment coming up which means we need to record a null element that otherwise wouldn't be recorded
    flush_cdata(state.cdata)
    assert not state.expect_endelement, "Special attributes should only be applied to empty elements" # **** also check on cdata
    thisPos=None # position of new element undecided
    if state.recogniseSpecialAttributes:
        if attributes.has_key(incAttrib) or \
           attributes.has_key(resetAttrib) or \
           attributes.has_key(renameAttrib):
            # NB this element's "end" will not be processed.  The next
            # processing will be at the start of the NEXT element.
            state.justHadIncrement = not state.justHadIncrement and not state.lastElementWasUnfinished # in case the empty data hasn't been recorded
            if not something_written and state.justHadIncrement: flush_cdata(state.cdata)
            state.lastElementWasUnfinished = attributes.has_key(notFinishedAttrib)
            state.justHadIncrement = not state.lastElementWasUnfinished
            # Change the value of "name" further up the tree
            # Need to find it first
            section = state.cursor.crossSection(0,name)
            depths = section.axisProjection(1)
            depths.sort()
            depth = depths[-1]
            position = state.positions[depth-1]
            # Now got (name,position,depth) - change it
            state.cursor.removePoint((name,position,depth))
            if attributes.has_key(incAttrib):
                position = position + 1
            elif attributes.has_key(resetAttrib):
                position = int(attributes[resetAttrib])
            if attributes.has_key(renameAttrib):
                name = attributes[renameAttrib]
            state.cursor.addPoint((name,position,depth))
            state.positions[depth-1] = position
            state.expect_endelement = 1 # so this element's end is not processed, and checks it's empty
            return
        else:
            state.lastElementWasUnfinished = 0
            if attributes.has_key(initPosAttrib):
                thisPos=int(attributes[initPosAttrib])
                del attributes[initPosAttrib]
        # Done with recognising special attributes
    if state.recogniseRowspan:
        thisPos=setupRowspan(name,attributes,thisPos)
    state.do_maybe_remove()
    state.justHadIncrement = 0
    # The last item on "positions" is the position to use.
    # Append a "1" for child elements.
    if thisPos==None: thisPos = state.positions[-1]
    else: state.positions[-1]=thisPos # (in case next is not numbered)
    thisDepth = len(state.positions)
    state.positions.append(1) ; state.spanSkips.append([])
    # Now ready to add the point to the cursor
    state.cursor.addPoint((name,thisPos,thisDepth))
    # had_cdata: See below
    state.had_cdata = 0
    # Here's one way of handling attributes:
    # (but need to reserve the word or something)
    if len(attributes) > 0:
        start_element("!attributes",{})
        state.inAttributes = 1
        for i in attributes.items():
            start_element(i[0],{})
            char_data(i[1])
            end_element(i[0])
        state.inAttributes = 0
        end_element("!attributes")
        # and backtrack, so first child element has same
        # position number (horrible hack for tables
        # demonstration)
        state.positions[-1] = state.positions[-1] - 1
def end_element(name):
    # End an element
    if state.expect_endelement:
        state.expect_endelement = 0
        return
    flush_cdata(state.cdata)
    # If the element has been completely empty, then it's
    # representing something (rather than marking something
    # up) and doesn't really fit this paradigm (perhaps
    # the XML should itself be treated as the thing to
    # mark up, or something).  For now, we'll add a null
    # item of cdata just to make sure it gets written in.
    if not state.had_cdata:
        char_data("") # the empty string
        # (this should also set had_cdata to 1, so the
        # parent element doesn't have to do anything)
    state.maybe_remove = None # anyway
    state.maybe_remove_points.thePoints.clear() # naughty
    state.justHadIncrement = 0
    # Drop one from 'positions' to read off the position
    # that we had.  Then increment it for the next element
    # at this level.
    state.positions.pop() ; state.spanSkips.pop()
    if state.spanSkips[-1]: del state.spanSkips[-1][0] # so all the 'n rows later' is now 'n-1 rows later'
    thisDepth = len(state.positions)
    thisPos = state.positions[-1]
    state.positions[-1] = thisPos + 1
    # Now ready to remove the point from the cursor
    state.cursor.removePoint((name,thisPos,thisDepth))

def addSpanSkip(rowsLater,posBefore,skipAmount):
    # (for colspan/rowspan stuff)
    spanList = state.spanSkips[-2] # (not the one that will
    # disappear at the end of the row, but the one that will
    # disappear at the end of the table)
    while len(spanList) <= rowsLater: spanList.append({})
    spanDict = spanList[rowsLater] # dict of pos -> skip
    if spanDict.has_key(posBefore):
        skipAmount = skipAmount + spanDict[posBefore]
    spanDict[posBefore] = skipAmount

def setupRowspan(name,attributes,thisPos):
    if thisPos==None: thisPos = state.positions[-1]
    # Change thisPos according to already-added skips:
    if state.spanSkips[-2]:
        if state.spanSkips[-2][0].has_key(thisPos):
            thisPos += state.spanSkips[-2][0][thisPos]
    # Plan future skips:
    colspan = rowspan = 1
    for k,v in attributes.items():
        try:
            if lower(k)=="rowspan": rowspan=int(v)
            elif lower(k)=="colspan": colspan=int(v)
        except ValueError: pass
    for i in range(1,rowspan): addSpanSkip(i,thisPos,colspan)
    if colspan>1: addSpanSkip(0,thisPos+1,colspan-1)
    return thisPos

def char_data(data):
    state.cdata = state.cdata + data
def flush_cdata(data):
    # Handle character data
    state.cdata = ""
    # First, do we really want this data?  If it's
    # ignorable whitespace then probably not (set the empty
    # string), unless we're in an attribute.  And if so
    # (or if it's the empty string anyway), we only want
    # it if it's the first thing (i.e. don't create surplus
    # "cdata" elements)
    if not state.inAttributes:
        found = 0
        for i in data:
            if i not in whitespace:
                found = 1
                break
        if found == 0: data = ""
    if data == "" and not (state.positions[-1] == 1 or state.justHadIncrement):
        return # Don't want it

    # Get a unique version of the data
    uniqueData = globalUniquifier.makeUnique(data)
    # NB the data may still be "" when there's *going*
    # to be child elements.  So keep track of it and
    # remove it if necessary.
    state.do_maybe_remove()
    if data == "" and not state.justHadIncrement:
        # (in first position can be assumed, because of
        # the code above)
        state.maybe_remove = uniqueData
    # cdata is assumed to come first, so if there has been
    # something before it, then we need a position marker
    # (2001-09-29: Now ALWAYS having a posn marker)
    # need_to_end = 0
    # if not state.positions[-1] == 1:
    #     need_to_end=1
    #     start_element("",{}) # cdata
    if not data == "": start_element("",{}) # cdata
    # (not data="" because don't want to mark up the epsilons)
    # Now can copy it across
    cursor = state.cursor
    if state.linker:
        # This is a bug workaround (2002-10-07) - if using
        # links then don't make them the same depth as other
        # elements.  (**** Probably no longer necessary)
        cursor = N_Space(3)
        for name,posn,depth in state.cursor.getPoints():
            if depth>=state.linker.linkDepth: depth=depth+1
            cursor.addPoint((name,posn,depth))
        # if data=="": cursor.addPoint((state.linker.linkName,state.linker.getStringNo(uniqueData),state.linker.linkDepth))
        # (uniqueData rather than "" so doesn't chase down links to other empty strings)
        # (and now commented out altogether - plft2 example got really confused about surplus 'autolinks' over "")
        # End of bug workaround
    state.result.addCursorPoints(cursor,scopeDimension,uniqueData)
    if state.maybe_remove: state.maybe_remove_points.addCursorPoints(cursor,scopeDimension,uniqueData) # cache them so don't have to call scopeOfElement() later
    # Also, do we want linking?
    if state.linker and not data=="":
        state.result.addPoint((state.linker.linkName,state.linker.getStringNo(data),state.linker.linkDepth,uniqueData))
    state.had_cdata = 1
    state.justHadIncrement = 0
    # following did say if need_to_end:
    if not data == "": end_element("")

def xmlStringToFourspace(xml_string,
                         recogniseSpecialAttributes=0,
                         recogniseRowspan=0,
                         linkName=None):
    p = init_state(recogniseSpecialAttributes,recogniseRowspan,linkName)
    try:
        p.Parse(xml_string)
    except xml.parsers.expat.ExpatError:
        import sys
        (type,value) = sys.exc_info()[:2]
        if not os.environ.has_key("fdml_ignore_expat_error"): raise TransformError("Parse error in: %s\n%s: %s\n" % (xml_string,type,value))
    # state.cleanup()
    return state.result
def xmlFileToFourspace(file,recogniseSpecialAttributes=0,
                       recogniseRowspan=0,
                       linkName=None):
    p = init_state(recogniseSpecialAttributes,recogniseRowspan,linkName)
    try:
        p.ParseFile(file)
    except xml.parsers.expat.ExpatError:
        import sys
        (type,value) = sys.exc_info()[:2]
        if not os.environ.has_key("fdml_ignore_expat_error"): raise TransformError("Parse error in file %s\n%s: %s\n" % (file,type,value))
    # state.cleanup()
    return state.result

def makePrintable(name):
    if hasattr(name,'encode') and \
       type(name) == types.UnicodeType:
        return name.encode('UTF-8')
    else: return name
#     import string
#     retVal = ""
#     for i in name:
#         if i in string.printable: retVal += i
#         else: retVal += "?"
#     return retVal

class StringLinker:
    def __init__(self):
        self.stringNos = {}
        self.counter = 1
    def getStringNo(self,string):
        if not self.stringNos.has_key(string):
            self.stringNos[string] = self.counter
            self.counter = self.counter + 1
        return self.stringNos[string]
