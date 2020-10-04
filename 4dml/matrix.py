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

#!/usr/bin/env python2

# simple generalised markup language for coding matrix-like
# data (music, translation notes, etc)

# Important: matrix.directTo4dml knows nothing about
# Unicode; everything is in raw binary.  If you mix this
# with a model that's taken through an XML parser like
# Expat, then errors might result later when Python tries to
# mix the two.  Either do everything with Expat or do
# nothing with it.

# Main thing to call is mmlToFourspace, which does one thing
# or another depending on whether xml_in can successfully
# import 'xml'

import xmlutil,xml_in
from xmlutil import documentName
from xml_in import incAttrib, resetAttrib, renameAttrib, notFinishedAttrib, initPosAttrib
from error import TransformError

import string,sre,sys
re=sre # hack for jythonc

def setup_text():
    global start_element,end_element,char_data
    global start_xml,end_xml
    xmlutil.setup_events_to_text()
    from xmlutil import start_element,end_element,char_data,start_xml,end_xml

# The following is in case Expat isn't available:
def setup_alternatives(linkName=None):
    global start_element,end_element,char_data
    global start_xml,end_xml,parseAll
    xmlutil.setup_events_to_fourspace(linkName)
    from xmlutil import start_element,end_element,char_data,start_xml,end_xml
    parseAll = alt_parseAll

# And some for handling the overlaps:
def inc_element(name,finished=1,newName=None,nameDic=None):
    dic = {} ; dic[incAttrib]="1" ; name=chkRenAttrib(dic,name,newName,nameDic)
    if not finished: dic[notFinishedAttrib]="1"
    start_element(name,dic) ; end_element(name)
def reset_element(name,finished=1,newName=None,nameDic=None):
    dic = {} ; dic[resetAttrib]="1"; name=chkRenAttrib(dic,name,newName,nameDic)
    if not finished: dic[notFinishedAttrib]="1"
    start_element(name,dic) ; end_element(name)
def chkRenAttrib(dic,name,newName,nameDic):
    if not newName: newName=name
    if nameDic and not nameDic[name]==newName:
    	    dic[renameAttrib]=newName
    	    oldName=nameDic[name]
    	    nameDic[name]=newName
    	    name=oldName
    return name
# (+ **** mml blocks with "also" may go wrong if names not uniq) (prob doc'd this limitatn, but not in the context of renaming elems)
# also **** should ensure renamed back b4 closing elements (otherwise cld get "remove nonexist point" assert, or data errors) (at least doc this)
# Actually it needs re-designing properly!

def flipUnix(text):
    # Change Mac and DOS line endings to Unix
    # (since some code here assumes Unix-style newlines)
    return string.join(re.split(r"\r\n?",text),"\n")

ParagraphRegexp = r"\n(?:[ \t]*\n)+" # paragraph separator
# **** the above might not always be right
# (the ?: is to avoid grouping - re.split does something
# different with it otherwise)

def headerBody(text):
    # Separates a header from the body, at first blank line
    # Returns a (header, body) tuple
    # (Don't really need this blank line if using reserved
    # words etc, but it can help with error checking)
    retVal = re.split(ParagraphRegexp, text, 1)
    if not retVal: return ("","")
    elif len(retVal) == 1: return (retVal[0], "")
    elif len(retVal) == 2: return (retVal[0], retVal[1])
    else: assert 0, "re.split bug detected - please use a version of Python greater than 1.5"

# also a split2 to use string.split (rather than re.split)
# and guarantee to return a pair of values
def split2(text,separator=None):
    retVal = string.split(text,separator,1)
    if not retVal: return ("","")
    elif len(retVal) == 1: return (retVal[0], "")
    elif len(retVal) == 2: return (retVal[0], retVal[1])
    else: assert 0, "re.split bug detected - please use a version of Python greater than 1.5"

reservedWordHave = "have"
reservedWordAs   = "as"
reservedWordAlso = "also" # begin new alternative hierarchy
reservedWordSpecial = "special:"
reservedWordMax = "maximum" ; reservedWordPer = "per"
# (only reserved in the header; NB must be lower case here,
# although the parser is not case-sensitive)
reservedWordLabel="label";reservedWordAs2="as"
reservedWordOp1="switches.";reservedWordOp2="switches"

def parseHeader(text,specials):
    # Parses the header; returns list of (splitList, renameList) alternatives for the alternative hierarchies
    # also returns 'encloseIn' - returns ([(split,rename)],enclose)
    # **** This parser ignores some errors; may need fixing
    # **** This is getting hacky - need proper grammar
    words = string.split(text)
    alternatives = []
    splitList = [] ; renameList = []
    addingTo = splitList
    specialState = 0 ; firstWord = 1 ; encloseIn = None
    for i in words:
        loweri = string.lower(i)
        if specialState==0:
            if loweri==reservedWordHave:
                addingTo = splitList
                checkLen(splitList,renameList)
            elif loweri==reservedWordAs:
                addingTo = renameList
            elif loweri==reservedWordAlso:
                # "also" - new alternative
                checkLen(splitList,renameList)
                alternatives.append((splitList,renameList))
                splitList = [] ; renameList = []
                addingTo = splitList
            elif loweri==reservedWordSpecial:
                # "special:" command (see below)
                specialState = 1
            elif firstWord: encloseIn = i
            else: addingTo.append(i)
        elif specialState==1: # element
            specialElemName = i
            specialState = 2
        elif specialState==2: # action
            specialAction = loweri
            if specialAction==reservedWordOp1:
                specialState = 0
                specials.stateCmds.append((specialElemName,None))
                # ("elemName" is actually the operator)
            else: specialState = 3
        elif specialState==3: # argument
            specialArgument = loweri
            if specialAction==reservedWordMax or specialAction==reservedWordLabel:
                specialState = 4
            elif specialAction==reservedWordOp2:
                specialState = 0
                specials.stateCmds.append((specialElemName,i))
            else: raise TransformError("MML: Unknown special action '%s'" % (specialAction,))
        elif specialState==4: # additional stuff
            if specialAction==reservedWordMax:
                if not loweri==reservedWordPer: raise TransformError("MML: Expecting '%s' after '%s'" % (reservedWordPer, reservedWordMax))
                specialState = 5
            elif specialAction==reservedWordLabel:
                if not loweri==reservedWordAs2: raise TransformError("MML: Expecting '%s' after '%s'" % (reservedWordAs2, specialAction))
                specialState = 5
            else: assert 0, "Shouldn't get here"
        elif specialState==5:
            if specialAction==reservedWordMax:
                maxval = int(specialArgument)
                if not maxval>0: raise TransformError("MML: Expecting integer >0 after '%s'" % (reservedWordMax,))
                specials.addMax(specialElemName,maxval,i)
                specialState = 0
            elif specialAction==reservedWordLabel:
                maxval = int(specialArgument)
                if not maxval>0: raise TransformError("MML: Expecting integer >0 after '%s'" % (reservedWordLabel,))
                specials.addRelabel(specialElemName,maxval-1,i)
            else: assert 0, "Shouldn't get here"
        firstWord = 0
    checkLen(splitList,renameList)
    alternatives.append((splitList,renameList))
    return (alternatives,encloseIn)

def checkLen(splitList,renameList):
    if not len(renameList) == len(splitList):
        raise TransformError("MML: Error in input: %s/%s not balanced (%s, %s)" % (reservedWordHave,reservedWordAs,splitList,renameList))

def doSplit(text,splitBy):
    # A few special cases for different types of whitespace
    ignoreEmptyWords = 1
    if splitBy=="paragraph":
        words = re.split(ParagraphRegexp,text)
    elif splitBy=="newline":
        words = string.split(text,"\n")
    elif splitBy=="whitespace":
        words = string.split(text)
    elif splitBy=="character":
        words = []
        for i in text: words.append(i)
    else:
        words = string.split(text,splitBy)
        ignoreEmptyWords = 0
    if ignoreEmptyWords:
        count = 0
        for i in words[:]:
            if not len(i): del words[count]
            else: count = count + 1
    return words

def do_cdata(text,specials):
    if specials.stateCmds:
        text=specials.updateState(text)
        toClose=[]
        for (sortKey,(elem,val)) in specials.state.items():
            toClose.append((sortKey,elem,val))
        toClose.sort()
        for s,elem,val in toClose:
            start_element(elem,{initPosAttrib:str(val)})
        char_data(text)
        toClose.reverse()
        for s,elem,val in toClose: end_element(elem)
    else: char_data(text)

def parseBody(text,splitList,renameList,specials):
    if not splitList:
        do_cdata(text,specials)
        return
    # Derive a list of words, based on splitList[0]
    words = doSplit(text,splitList[0])
    # Now can make the recursive call
    count = 0
    maxcount = None
    if specials.max.has_key(renameList[0]):
        maxcount = specials.max[renameList[0]]
    for i in words:
        # **** This isn't good enough - what if 'maxgrp' is
        # also mentioned in a 'special:'?
        count = count + 1
        if maxcount and (count % maxcount)==1:
            start_element(specials.maxgrp[renameList[0]],{})
        start_element(renameList[0],{})
        parseBody(i,splitList[1:],renameList[1:],specials)
        end_element(renameList[0])
        if maxcount and ((count % maxcount)==0 or \
                         count==len(words)):
            end_element(specials.maxgrp[renameList[0]])

def parseBody_overlap(text,alternatives,specials):
    # This version can cope with overlapping elements (as
    # long as there are no duplicates in renameList)
    # alternatives contains list of (splitList, renameList)
    renameList = []
    for alt in alternatives:
        renameList = renameList + alt[1]
    assert noDuplicates(renameList),"Duplicate element name in multiple independently-overlapping matrices - MML can't cope with that" # **** raise TransformError?
    for i in renameList: start_element(i,{})
    for i in specials.maxgrp.values(): start_element(i,{})
    pbo_recurse(text,[],[],alternatives,specials)
    renameList = renameList + specials.maxgrp.values()
    renameList.reverse()
    for i in renameList: end_element(i)

def pbo_recurse(text,splitList,renameList,alternatives,specials):
    if not splitList:
        if alternatives:
            pbo_recurse(text,alternatives[0][0],alternatives[0][1],alternatives[1:],specials)
        else: do_cdata(text,specials)
        return
    # Derive a list of words as before, but see if there
    # were ANY operators (even if there was only one item)
    didSplit = 0
    words = doSplit(text,splitList[0])
    if len(words) > 1: didSplit = 1
    elif len(words)==1:
        if not words[0]==text: didSplit = 1
    elif len(text):
        didSplit = 1
        words = [None] # so it does the next "for" loop
    # After every splitList[0] (if any), want to increment
    # renameList[0] and reset other renameLists in this alt
    # - except don't do this after the last one (if more
    # than one)
    count = 0
    for i in words:
        count = count + 1
        if not i==None: pbo_recurse(i,splitList[1:],renameList[1:],alternatives,specials)
        if didSplit and (count<len(words) or len(words)==1):
            if specials.max.has_key(renameList[0]) and \
               (count % specials.max[renameList[0]])==0:
                # (note 0, not 1 (which is where it starts))
                reset_element(renameList[0],0,specials.getLabel(renameList[0],0),specials.nameDic)
                inc_element(specials.maxgrp[renameList[0]],
                            len(renameList)==1,specials.getLabel(specials.maxgrp[renameList[0]],1),specials.nameDic)
                # **** the ,1 in getLabel is wrong (shld be a count of the groupname elem)
            else: inc_element(renameList[0],
                              len(renameList)==1,specials.getLabel(renameList[0],count),specials.nameDic)
            finish = renameList[-1]
            for i in renameList[1:]:
                reset_element(i,i==finish,specials.getLabel(i,0),specials.nameDic)

def noDuplicates(list):
    dict = {}
    for i in list:
        if dict.has_key(i): return 0
        dict[i] = 1
    return 1

class Specials:
    def __init__(self):
        self.max = {}
        self.maxgrp = {}
        self.relabel={}
        self.nameDic={}
        self.stateCmds=[] ; self.stateMnemonics={}
        self.state = {}
    def addMax(self,elem,maxval,group):
        self.max[elem] = maxval
        self.maxgrp[elem] = group
    def addRelabel(self,elem,pos,newlabel):
        self.relabel[(elem,pos)]=newlabel
    def getLabel(self,elem,pos):
        if self.relabel.has_key((elem,pos)): return self.relabel[(elem,pos)]
        else: return elem
    def updateState(self,text):
        count = 0
        for (op,elem) in self.stateCmds:
            count=count+1
            words=string.split(text,op)
            text=words[0] ; del words[0]
            for w in words:
                # Each 'w' will be a string of text that
                # occurs AFTER an operator 'op'
                try:
                    (val,txt2) = string.split(w,None,1)
                except ValueError:
                    # No whitespace - last thing in an item
                    val = w
                    txt2 = ""
                text=text+txt2 # *** (collect & 'join' might be more efficient but anyway)
                (val2,elem2,wasNewVal)=self.decodeMnemonic(val,elem)
                if wasNewVal: text=val+" "+text
                self.state[count]=(elem2,val2)
                # putting 'count' in because original 'elem' might be None, so can't just use stateCmds for the ordering
        return text
    def decodeMnemonic(self,val,elem):
        wasNewVal = 0
        if not self.stateMnemonics.has_key(elem):
            self.stateMnemonics[elem]=({},1)
        (dict,counter)=self.stateMnemonics[elem]
        if not dict.has_key(val):
            dict[val]=counter ; wasNewVal = 1
            self.stateMnemonics[elem]=(dict,counter+1)
        if not elem: elem=val # mnemonic-to-label if label missing
        return dict[val], elem, wasNewVal

def parseBlock(text):
    (header,body) = headerBody(flipUnix(text))
    if body and body[-1]=="\n": body=body[:-1] # strip trailing newline before !endblock, just in case (otherwise parsing with overlaps can register a surplus operator)
    # (calling flipUnix here as well, in case parseBlock is
    # called independently of parseAll)
    specials = Specials()
    (alternatives,encloseIn) = parseHeader(header,specials)
    if encloseIn: start_element(encloseIn,{})
    if len(alternatives)==1 and not specials.nameDic:
        (splitList,renameList) = alternatives[0]
        parseBody(body,splitList,renameList,specials)
    else:
        parseBody_overlap(body,alternatives,specials)
    if encloseIn: end_element(encloseIn)

def parseAll_inner(text):
    text = flipUnix(text)
    elemStack = []
    start_xml()
    start_element(documentName,{})
    while len(text) > 0:
        (word,text) = split2(text)
        if not word: continue
        elif string.lower(word) == "begin":
            (elemName,text) = split2(text)
            elemStack.append(elemName)
            start_element(elemName,{})
        elif string.lower(word) == "end":
            (elemName,text) = split2(text)
            elemToEnd = elemStack.pop()
            if not elemName == elemToEnd: raise TransformError("MML: Imbalanced elements: Begin '%s' incorrectly matched with End '%s'" % (elemToEnd,elemName))
            end_element(elemToEnd)
        elif string.lower(word) == "advance":
            (elemName,text) = split2(text)
            if not elemName in elemStack: raise TransformError("MML: Tried to advance element '%s' which is not in progress" % (elemName,))
            inc_element(elemName)
        elif word[-1] == ":":
            elemName = word[:-1]
            start_element(elemName,{})
            # have rest of line as the cdata
            (line,text) = split2(text,"\n")
            char_data(line)
            end_element(elemName)
        elif string.lower(word) == "!block":
            (block,text) = split2(text,"!endblock")
            parseBlock(block)
        else:
            raise TransformError("MML: Unrecognised word '%s'" % (word,))
    end_element(documentName)
    return end_xml()

def parseAll(text):
    setup_text()
    return parseAll_inner(text)
def alt_parseAll(text):
    assert 0, "Tried to call parseAll after setup_alternatives (need to do it properly with classes)"

def directTo4dml(text,linkName=None):
    setup_alternatives(linkName)
    return parseAll_inner(text)

def mmlToFourspace(text,linkName=None):
    if hasattr(xml_in,'xml'):
        return xml_in.xmlStringToFourspace(parseAll(text),1,0,linkName) # 1 = recognise special attributes
    else: return directTo4dml(text,linkName)

# import version
if __name__ == "__main__":
    print parseAll(sys.stdin.read())
