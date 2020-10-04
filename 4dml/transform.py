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

# Service routines for transform

import string,types
from xmlutil import tuple2text_raw
from error import TransformError
import str_unique, stats

def beginTrace(tracer,model,input):
    # These functions are only called if actually tracing
    # (no need for a "null tracer")
    tracer.addString("<transform><model>")
    for params,children in model:
        tracer.addString(tuple2text_raw(params.trace))
        # which contains all children info
    tracer.addString("</model><input>")
    tracer.addString(input.convertToXML(""))
    tracer.addString("</input>")

def endTrace(tracer,retVal):
    tracer.addString("<result>")
    tracer.addString(retVal)
    tracer.addString("</result></transform>")

def preParseModel(model,needTrace=None,modelDictionary=None,in_no_markup=0,in_wildcard=None,ret=None,toplevel_only=0):
    # Returns list of (params,children-list) or (params,[])
    if modelDictionary==None: modelDictionary={}
    if ret==None: ret = [] # see below
    # ('ret' might be ref to empty list & the ref is also in modelDictionary for the recursion, hence 'ret==None' not 'not ret')
    if type(model)==types.StringType or type(model)==types.UnicodeType: return ret # will already have been included
    for (name,attribs,subModel) in model:
        # subModel might be a string or a tuple
        # If it's a tuple then we want to change it into
        # a reference to our child-list (for recursion)
        # This needs to be done BEFORE parsing Params
        childRef = [] # for the children
        params = Params(attribs,subModel,childRef,name,modelDictionary,in_no_markup,in_wildcard,needTrace)
        newModelDic = modelDictionary
        if not params.exportCode:
            newModelDic = newModelDic.copy()
        subs = preParseModel(subModel,needTrace,newModelDic,params.no_markup,params.wildcard,childRef,params.sequential)
        ret.append((params,subs))
    return ret

class DynamicParams:
    # stuff that changes on different iterations of the
    # model (i.e. don't re-use these objects like you can
    # re-use Params)
    def __init__(self,ifChangedMap,refToGlobal):
        self.ifChangedMap = ifChangedMap
        self.refToGlobal = refToGlobal
        self.extraBegin = "" # e.g. for debugdump
        self.extraAttributes = {} # if added from input

class Params:
    def __init__(self,attribs,subModel,childRef,oldName,modelDictionary,no_markup,wildcard,needTrace):
        self.oldName = self.newName = oldName
        self.no_markup = no_markup
        self.wildcard = wildcard
        if needTrace: self.trace=(oldName,attribs,subModel)
        if oldName=="": self.asString=subModel # cdata
        if attribs.has_key("nomarkup"): self.no_markup=1
        if self.no_markup: self.newName=""
        if attribs.has_key("rename"):
            self.newName=attribs["rename"]
        if attribs.has_key("from"):
            self.newName=self.oldName
            self.oldName=attribs["from"]
        if attribs.has_key("discard"):
            self.newName=""
        self.count=attribs.has_key("count")
        self.ifChanged=attribs.has_key("if-changed")
        self.unconditional=attribs.has_key("no-input")
        self.debugDump=attribs.has_key("debugdump")
        self.allowEmpty=attribs.has_key("allow-empty")
        self.expected=attribs.has_key("expected")
        if self.allowEmpty and self.expected: raise TransformError("Doesn't make sense to have both 'allow-empty' and 'expected' on same element")
        self.writeBefore=self.writeAfter=\
                          self.writeBetween=None
        self.writeGroup = None ; self.groupSize = 10
        if attribs.has_key("before"):
            self.writeBefore=attribs["before"]
        if attribs.has_key("after"):
            self.writeAfter=attribs["after"]
        if attribs.has_key("between"):
            self.writeBetween=attribs["between"]
        if attribs.has_key("group"):
            self.writeGroup=attribs["group"]
        if attribs.has_key("group-size"):
            self.groupSize=int(attribs["group-size"])
        self.newBegin=self.newEnd=None
        if attribs.has_key("begin"):
            self.newBegin=attribs["begin"]
        if attribs.has_key("end"):
            self.newEnd=attribs["end"]
        self.startAt=self.endAt=None
        if attribs.has_key("start-at"):
            self.startAt=int(attribs["start-at"])
            # NB explicit numeric conversion needed!
        if attribs.has_key("end-at"):
            self.endAt=int(attribs["end-at"])
        self.reverse=attribs.has_key("reverse")
        self.random=attribs.has_key("random")
        if attribs.has_key("number"):
            self.endAt=self.startAt=int(attribs["number"])
        self.renumber=attribs.has_key("renumber")
        if self.renumber: stats.uses_renumber = 1
        self.sequential = self.writeCData = 0
        self.childrenOnly = attribs.has_key("children-only")
        if attribs.has_key("sequential"):
            self.sequential = self.childrenOnly = 1
            if attribs["sequential"]=="cdata":
                self.writeCData = 1
        self.external = None
        self.clearExternal = 0
        import os
        if os.environ.has_key("no_external"): attribs["external"]="clear" # hack
        # Value of "external": None = auto-determine;
        # 0 = never, 1 = always
        if attribs.has_key("external"):
            if attribs["external"] == "never":
                self.external = 0
            elif attribs["external"] == "always":
                self.external = 1
            elif attribs["external"] == "clear":
                self.external = 0
                self.clearExternal = 1
            else:
                raise TransformError("Incorrect value of 'external' parameter: %s" % attribs["external"])
        self.include_rest = 0
        self.broaden = [] ; self.badHack = []
        self.broadenToOthersOnly = attribs.has_key("others-only")
        if attribs.has_key("broaden"): self.broaden = string.split(attribs["broaden"],"/")
        if attribs.has_key("badHack"): self.badHack = string.split(attribs["badHack"],"/")
        # (*** not really satisfied with using string.split & 'complex' attribute syntax, but this features shouldn't be used that much)
        self.include_rest = attribs.has_key("include-rest")
        self.strip = not attribs.has_key("no-strip")
        self.stripHack = attribs.has_key("strip")
        self.merge = attribs.has_key("merge")
        self.flatten = attribs.has_key("flatten")
        if attribs.has_key("wildcard"):
            self.wildcard=attribs["wildcard"]
        self.valueCondition = None
        self.defaultValueCondition = 0
        self.lengthCondition = None
        if attribs.has_key("value"):
            self.valueCondition=attribs["value"]
        elif attribs.has_key("other-values"):
            self.defaultValueCondition = 1
        if attribs.has_key("total"):
            self.lengthCondition=int(attribs["total"])
        self.hackyFilterClass = None
        if attribs.has_key("python"):
            # **** This is a bit hacky, and has the bug that
            # if you specify both "python" and "filter" then
            # only one gets done
            self.hackyFilterClass = SpecialPythonFilter(attribs["python"])
        if attribs.has_key("filter"):
            # Hack - run the PML filter through it
            import pml
            self.hackyFilterClass = pml.classList[int(attribs["filter"])]
        self.modelToCall = self.exportCode = None
        if attribs.has_key("call"): self.modelToCall=modelDictionary[attribs["call"]]
        else: modelDictionary[oldName]=childRef # **** really "else"?
        # (note childRef not subModel - see comment above)
        if attribs.has_key("export-code"): self.exportCode=1
        self.extraAttributes = {}
        for i in attribs.keys():
            if i[0]=="_":
                self.extraAttributes[i[1:]]=attribs[i]

def searchDisplayStack(ext_stack,elemName,childrenOnly,toplevel_only,strip,dont_need_extern):
    #print "Debugger: Searching display stack"
    fsList = []
    posList = []
    index = 0
    space = None
    while not fsList and \
          index > -len(ext_stack):
        index = index - 1
        space = ext_stack[index]
        fsList,posList,for_rest = space.forEach(elemName,childrenOnly,toplevel_only,strip)
    if fsList and not dont_need_extern:
        ext_stack = ext_stack[0:index]
        # ext_stack[0:index] would EXCLUDE
        # index - need to replace this with
        # the for_rest from whatever space
        # we got fsList from
        ext_stack.append(for_rest)
    # (needed the 'if fsList' condition
    # because 'space' needs to be defined in
    # the above code - the condition is not just for
    # efficiency)
    #print "Debugger: Done display stack"
    if fsList: stats.used_extern_stack = 1
    return fsList, posList, ext_stack

def getFourspaceList(params,dynamic,data,ext_stack,toplevel_only,countDic,dont_need_extern):
    # (dont_need_extern is an optimisation - if a leaf node
    # with no modelToCall (determined at the call in
    # fourspace.py), don't need to bother calculating
    # for_rest)
    if params.unconditional:
        return ([data], ext_stack, 0)
    elif params.count:
        if not countDic.has_key(params.oldName): raise TransformError("Can't count '%s' here" % (params.oldName,))
        numberData = data.getInstance()
        # (hack to get around the imports problem - can't import fourspace because fourspace imports transform)
        numberData.addPoint(("",0,0,str_unique.globalUniquifier.makeUnique(str(countDic[params.oldName]))))
        return ([numberData], ext_stack, 0)
    elemName = params.oldName
    posList = []
    broadenParam = None
    external = params.external # take a copy (going to mess with it)
    if params.broaden or params.badHack:
        assert not (params.broaden and params.badHack), "Can't do broaden and badHack at the same time"
        # should really be raise TransformError but still
        broadenParam=(dynamic.refToGlobal,[],params.broaden+params.badHack,params.childrenOnly or params.badHack,params.broadenToOthersOnly)
    if elemName == params.wildcard:
        fsList = data.forEachElement(broadenParam)
        # For now, only supporting broaden w/out putting on extern stack, so:
        if params.broaden: fsList = broadenParam[1]
        external = 0
        # **** Get posList properly? (only needed if doing 'wildcard number=n' stuff)
        if params.stripHack:
            # Remove top-most elem from fsList anyway
            for fs in fsList:
                if not fs.isEmpty():
                    fs.removeElement(fs.pointInFirstElement())
    elif not external:
        # Maybe never search display stack, or maybe search
        # it only if this fails.
        fsList,posList,for_rest = data.forEach(elemName,params.childrenOnly,toplevel_only,params.strip,broadenParam)
        # For now, only supporting broaden w/out putting on extern stack, so:
        if params.broaden:
            fsList = broadenParam[1]
            posList = [] # **** not supported ?
        if external == None:
            # DON'T change to "if not external".  external
            # could be 0, in which case we DON'T want this
            # to run.
            external = (not fsList)
    if external:
        fsList, posList, ext_stack = searchDisplayStack(ext_stack,elemName,params.childrenOnly,toplevel_only,params.strip,dont_need_extern)
        need_to_pop = 0
        # (**** broaden not supported in conjunction with ext stack?)
    else:
        # Not external
        # fsList,posList,for_rest = data.forEach(elemName,params.childrenOnly,toplevel_only,params.strip) # done
        if not elemName==params.wildcard and not dont_need_extern:
            ext_stack.append(for_rest)
            need_to_pop = 1
        else: need_to_pop = 0
    # Now got fsList; badHack thing follows: ****
    if params.badHack:
        for fs in broadenParam[1]:
            # There should only be one of these 'fs's
            # ('badHack' doesn't really make much sense if
            # there's more than one; that's why it's called
            # 'badHack'; this should be implemented properly
            # or done in 4dml
            for k,v in fs.getAttributes().items():
                dynamic.extraAttributes[k] = v
    # End of badHack thing ****
    # Got fsList
    # Only including things that have changed?
    # (doing this before numerical constraints so that e.g. 'if-changed start-at=2' will register if it has gone back to 1 in the interim even though this 1 is not processed)
    if params.ifChanged:
        if dynamic.ifChangedMap.has_key(params.oldName):
            lastVal = dynamic.ifChangedMap[params.oldName]
        else: lastVal = None
        if posList:
            if posList[-1] == lastVal:
                # Not changed
                fsList = []
            else:
                dynamic.ifChangedMap[params.oldName] = posList[-1]
                posList = posList[-1:]
                fsList = fsList[-1:]
            # (Note the -1, not 0, in case the position
            # advances DURING this element (maybe after an
            # epsilon at the beginning) - take the HIGHEST
            # position #) (**** is this really OK?)
    # Any numerical constraints?
    # (At present startAt and endAt begin at 1; we want them
    # to begin at 0 (with 'endAt' beginning at 1 for ending
    # AT 0), using the flags 'isStartAt' and 'isEndAt' to
    # indicate whether their values are valid or not.  So if
    # 'renumber' then subtract 1 from startAt, otherwise
    # look it up in posList.)
    isStartAt = isEndAt = 0
    startAt = params.startAt ; endAt = params.endAt
    # (take copies because we'll mess with them)
    if startAt:
        isStartAt=1
        if params.renumber: startAt=startAt-1
        else:
            if startAt in posList:
                startAt=posList.index(startAt)
            elif posList and posList[0] > startAt:
                startAt = 0
            else: startAt=len(fsList)
            if not startAt==params.startAt-1: stats.non_renumber_matters = 1
    if endAt:
        isEndAt=1
        if params.renumber: pass # no change
        else:
            if endAt in posList:
                endAt=posList.index(endAt)+1
            elif posList and posList[-1] < endAt:
                endAt = len(fsList)
            else: endAt=0
            if not endAt==params.endAt: stats.non_renumber_matters = 1
    if isStartAt and isEndAt:
        fsList = fsList[startAt:endAt]
        posList = posList[startAt:endAt]
    elif isStartAt:
        fsList = fsList[startAt:]
        posList = posList[startAt:]
    elif isEndAt:
        fsList = fsList[:endAt]
        posList = posList[:endAt]
    # Do we need to merge in the last display stack item?
    if params.include_rest and fsList and ext_stack:
        space = ext_stack[-1]
        for i in fsList:
            # i.addPoints(space.getPoints())
            i.thePoints.update(space.thePoints)
        if need_to_pop:
            ext_stack.pop()
            need_to_pop = 0
        else: ext_stack=ext_stack[:-1]
    # or clear the display stack altogether?
    if params.clearExternal:
        if need_to_pop: ext_stack.pop() # restore consistency (because the caller might have a reference to it)
        ext_stack = []
        need_to_pop = 0
    # Do we need to flatten everything?
    if params.flatten:
        for i in fsList: i.flatten()
    # Any value constraints?
    if not params.valueCondition==None:
        lp = 0
        copiedList = fsList[:]
        for fs in fsList:
            if fs.markDownOrAttr() == params.valueCondition:
                dynamic.defaultValueNeeded [elemName] = 0
                lp = lp + 1
            # self.defaultValueCondition
            else: del copiedList[lp]
            # (Don't modify original!  It will be cached.)
        fsList = copiedList
    # Any length constraints?
    elif not params.lengthCondition==None:
        if not len(fsList) == params.lengthCondition:
            fsList = []
        else: dynamic.defaultValueNeeded [elemName] = 0
    elif params.defaultValueCondition:
        # Only proceed if haven't already had something
        if dynamic.defaultValueNeeded.has_key(elemName):
            fsList = []
            del dynamic.defaultValueNeeded[elemName]
    # Need to reverse?
    if params.reverse: fsList.reverse()
    # Need to choose one at random?
    if params.random:
        import random
        fsList=[random.choice(fsList)]
    # Merging (goes after all numerical selection)
    if params.merge and len(fsList) > 1:
        newFS = data.getInstance()
        for fs in fsList:
            # **** optimisation hack - going straight in
            newFS.thePoints.update(fs.thePoints)
        fsList = [newFS]
    # If nothing left, do we allow empty?
    if not fsList:
        if params.expected: raise TransformError("Expected '%s' but none found\n(Positions: %s)" % (params.oldName,countDic))
        if params.allowEmpty:
            emptyData = data.getInstance()
            # (getInstance() is a hack to get around the imports problem)
            # emptyData.addPoint(("",0,0,str_unique.globalUniquifier.makeUnique(""))) # not needed
            fsList = [emptyData]
    # debugdump code
    if params.debugDump:
        # debugData = data.getInstance()
        # # (hack to get around the imports problem)
        # for f in fsList:
        #     debugData.addPoint(("",0,0,str_unique.globalUniquifier.makeUnique(f.debugDump())))
        # return ([debugData], ext_stack, need_to_pop)
        for f in fsList:
            dynamic.extraBegin=dynamic.extraBegin+f.debugDump()
    # OK, return it
    return (fsList, ext_stack, need_to_pop)

def doRecursiveCall(fs2,subModel,new_ext_stack,params,dynamic,afterBegin,countDic,newName,newCounter,tracer):
    beginList = []
    if params.newBegin:
        beginList.append(params.newBegin)
    if dynamic.extraBegin:
        beginList.append(dynamic.extraBegin)
    if afterBegin: beginList.append(afterBegin)
    elif params.allowEmpty: beginList.append("")
    endList = []
    if params.newEnd: endList.append(params.newEnd)
    firstTime = newCounter.firstTime
    retVal = [] # strings to concatenate & return

    middleBit = fs2.transformByModel(subModel,new_ext_stack,params.no_markup,beginList,endList,params.wildcard,countDic,params.sequential,newCounter,tracer,dynamic.ifChangedMap,dynamic.refToGlobal)
    needToClose = 0
    if newName and firstTime:
        # firstTime - this is a nasty implementation detail
        # - main idea is 'for each model elem' & 'for each
        # i/p elem that matches it', but 'sequential' adds a
        # third level but does not adjust position #s etc
        # (it's just to hack further processing into
        # non-amalgamation) so don't want to set up an elem
        retVal.append("<"+newName)
        for i in params.extraAttributes.items()+dynamic.extraAttributes.items():
            retVal.append(" "+i[0]+"=\""+sortEntities(i[1])+"\"")
        # Can we use the <BR /> notation?
        needToClose=1
        if not middleBit:
            retVal.append(" /")
            needToClose=0
        retVal.append(">")
    retVal.append(middleBit)
    if needToClose: retVal.append("</"+newName+">")
    return "".join(retVal)

class Counter: # used for "sequential" in model transforms
    def __init__(self):
        # self.value = 1  # no longer used
        self.firstTime = 1

def doAFourspace(fs,params,dynamic,subModel,new_ext_stack,countDic,tracer):
    elemName = params.oldName
    if elemName == params.wildcard and \
       params.newName == params.wildcard:
        # rename to whatever i/p was (**** really 'newName' here?)
        newName=fs.pointInFirstElement()[0]
        # (should always work, since top-
        # level element is not removed on
        # wildcard match)
    else: newName = params.newName
    listForRecursiveCall = [fs]
    # If this is a leaf node in the model
    # then we want all data in fs
    # (but not attributes?) ****
    afterBegin = None
    if not subModel and not params.modelToCall:
        if params.sequential: raise TransformError("Doesn't make sense for empty element '%s' to have 'sequential' attribute" % (elemName,)) # **** really? / can be ignored (no effect anyway)
        afterBegin = fs.markDownOrAttr()
        if params.hackyFilterClass:
            params.hackyFilterClass.count=countDic[params.oldName] ; params.hackyFilterClass.countDic = countDic # hack for the Chinese notes **** document or something (not used in thesis)
            params.hackyFilterClass.refToGlobal = dynamic.refToGlobal # even nastier hack **** sort out! (not used in thesis)
            afterBegin = params.hackyFilterClass.filter(afterBegin)
        # afterBegin = fs.convertToXML("") # TEST Debugger
        # (done this way so that it's
        # between "begin" and "end")
    elif params.sequential:
        # Need to split it into an item for
        # each top-level element (and keep
        # that top-level element) and do the
        # recursive call on each.
        listForRecursiveCall = fs.forEachElement()
    newCounter = Counter()
    # Make the recursive call
    retVal = []
    for fs2 in listForRecursiveCall:
        if params.writeCData:
            assert params.sequential
            pt = fs2.pointInFirstElement()
            if pt[0] == "":
                # cdata in input that needs
                # to be copied to output
                afterBegin = fs2.markDownOrAttr()
            else: afterBegin = None
            # (Note that this does not interfere with the
            # above use of 'afterBegin' (e.g. calling the
            # filter on it), since THAT was for empty
            # models; THESE models are not empty.)
        if params.modelToCall and subModel: raise TransformError("Doesn't make sense for non-empty element to have 'call' attribute") # **** (?) (NB if *both* of the calls below happen, might be contradictions with 'newElement') (but now using 'newName' instead of 'newElement', should be OK apart from a few 'position' mishaps in grouping, so might be OK to allow this)
        if params.modelToCall: retVal.append(doRecursiveCall(fs2,params.modelToCall,new_ext_stack,params,dynamic,afterBegin,countDic,newName,newCounter,tracer))
        if not params.modelToCall or subModel: retVal.append(doRecursiveCall(fs2,subModel,new_ext_stack,params,dynamic,afterBegin,countDic,newName,newCounter,tracer))
    # end of listForRecursive call
    return "".join(retVal)

class SpecialPythonFilter:
    def __init__(self,function):
        self.function = eval(function,userModule.__dict__)
        # (note that self.function does NOT become a method)
    def filter(self,text): return self.function(text)

def sortEntities(str):
    # Used in convertToXML to ensure that valid XML is
    # written (assumes the existence of "amp" and "lt")
    str = string.replace(str,"&","&amp;")
    str = string.replace(str,"<","&lt;")
    return str

def processFSList(fsList,params,dynamic,children,new_ext_stack,countDic,tracer,retVal):
    # process a list of fourspaces, maybe in parallel
    # add to retVal
    if not fsList: return
    if params.writeBefore:
        retVal.append(sortEntities(params.writeBefore))
    offset = 1 # for printing the count
    if params.startAt: offset = params.startAt
    # **** really need proper memory of posn #
    # OK, how many other threads can we have?
    if tracer: managers, a = [], 0
    else: managers, a = makeManagers(len(fsList))
    for m in managers:
        thread.start_new_thread(fsListThread_copy,(fsList,offset,params,dynamic,children,new_ext_stack[:],countDic.copy(),m))
    # Now do something in the current thread
    if countDic.has_key(params.oldName):
        oldCount = countDic[params.oldName]
    else: oldCount = None
    thisThreadsAnswer = fsListThread(fsList,a,len(fsList),offset,params,dynamic,children,new_ext_stack,countDic,tracer)
    if oldCount:
        countDic[params.oldName] = oldCount
    else: del countDic[params.oldName]
    # Now collate the output
    for m in managers:
        m.lock.acquire() # wait for it to finish
        if m.exception: raise m.exception # oops
        else: retVal.extend(m.retVal)
    retVal.extend(thisThreadsAnswer)
    if params.writeAfter:
        retVal.append(sortEntities(params.writeAfter))

def fsListThread(fsList,a,b,offset,params,dynamic,children,new_ext_stack,countDic,tracer):
    # processes all items from a to b, returns list
    # can change 'new_ext_stack' and 'countDic'
    # Better not do multithreading if 'tracer'
    retVal = []
    count = a
    while count < b:
        countDic[params.oldName] = count+offset
        lastOne = (count+1 == b == len(fsList))
        retVal.append(doAFourspace(fsList[count],params,dynamic,children,new_ext_stack,countDic,tracer))
        if not lastOne:
            if params.writeGroup and (count+offset) % params.groupSize == 0:
                retVal.append(sortEntities(params.writeGroup))
            elif params.writeBetween:
                retVal.append(sortEntities(params.writeBetween))
        count = count + 1
    return retVal

import sys
def fsListThread_copy(fsList,offset,params,dynamic,children,new_ext_stack,countDic,manager):
    # This one is meant to be run in a thread
    # copies new_ext_stack and countDic
    # (NO!  race condition with main thread - now copied in
    # the caller)
    # 'manager' is the ManagerForAThread
    # note: no 'tracer'
    # sys.stderr.write("Debugger: I'm in a new thread\n")
    try:
        manager.retVal = fsListThread(fsList,manager.a,manager.b,offset,params,dynamic,children,new_ext_stack,countDic,None)
    except: # oops
        manager.exception = sys.exc_info()[1]
    manager.lock.release()
    theThreadMaster.threadHasFinished()
    # sys.stderr.write("Debugger: Thread is finishing\n")

class ThreadMaster:
    # keeps track of the total number of threads running
    def __init__(self):
        self.lock = thread.allocate_lock()
        self.numThreads = 1 # the main thread
    def startedThreads(self,n):
        self.lock.acquire()
        str_unique.makeThreadSafe()
        self.numThreads = self.numThreads + n
        self.lock.release()
    def threadHasFinished(self):
        self.lock.acquire()
        self.numThreads = self.numThreads - 1
        self.lock.release()
try:
    import thread
    theThreadMaster = ThreadMaster()
except ImportError:
    class FakeThreadMaster:
        def __init__(self): self.numThreads = 1
    theThreadMaster = FakeThreadMaster()
maxNumThreads = 1 # ***************************
class ManagerForAThread:
    def __init__(self,a,b):
        self.a = a
        self.b = b
        self.lock = thread.allocate_lock()
        self.lock.acquire() # released when finished
        self.retVal = None
        self.exception = None

def makeManagers(nItems):
    # Shares the nItems between threads, and leaves some
    # for this thread.  Makes some ManagerForAThread objs.
    # Returns (managers, a) where a is the starting place
    # for the current thread.
    nThreads = min(nItems-1,maxNumThreads - theThreadMaster.numThreads) # num new threads
    if not nThreads: return ([], 0)
    theThreadMaster.startedThreads(nThreads)
    perThread = nItems/(nThreads+1)
    extraToShare = nItems % (nThreads+1)
    managers = []
    a = 0
    for i in range(nThreads):
        b = a + perThread
        if i < extraToShare: b = b + 1
        managers.append(ManagerForAThread(a,b))
        a = b
    return (managers, a)
