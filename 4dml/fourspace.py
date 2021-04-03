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

# search **** for things that need doing

from nspace import N_Space
from str_unique import StringUniquifier
import transform
sortEntities=transform.sortEntities
import string
from dimens import *

import os
try:
    if os.environ.has_key("no_psyco"): raise ImportError
    from psyco.classes import *
# except ImportError: pass
except: pass # hack for jython

def unXmlify(str):
    str = string.replace(str,"&lt;","<")
    str = string.replace(str,"&amp;","&")
    # That was just the reverse of sortEntities.
    # Now a hack for the M-Tx lyrics example - **** sort this out (&#10; etc)
    # **** probably want to expand more
    # entities than this
    str = string.replace(str,"&quot;",'"')
    str = string.replace(str,"&gt;",">")
    str = string.replace(str,"&#10;","\n")
    return str

def listsToPairs((a,b,throwaway)):
    # transpose a pair of lists into a list of pairs
    # (3rd argument is a hack - used in calc_foreach)
    assert len(a) == len(b), "Lists must be of equal length"
    r = []
    for i in range(len(a)):
        r.append((a[i],b[i]))
    return r

class FourSpace(N_Space):
    def __init__(self):
        N_Space.__init__(self,4)
        self.foreachCache = {}
    def getInstance(self): return FourSpace() # hack
    def copyPointsFrom(self,nspace):
        self.thePoints = nspace.thePoints.copy()
        # NB: [:] is a SHALLOW copy
    def makeCopy(self):
        f = FourSpace()
        f.copyPointsFrom(self)
        return f
    def subSection(self,dimension,values):
        # (make sure it's returned as a FourSpace)
        n = N_Space.subSection(self,dimension,values)
        r = FourSpace()
        r.thePoints = n.thePoints
        return r
    def subSectionFromDict(self,dimension,values):
        # (make sure it's returned as a FourSpace)
        n = N_Space.subSectionFromDict(self,dimension,values)
        r = FourSpace()
        r.thePoints = n.thePoints
        return r
    def minimum(self,dimension):
        # (make sure it's returned as a FourSpace)
        n = N_Space.minimum(self,dimension)
        r = FourSpace()
        r.thePoints = n.thePoints
        return r
    def flatten(self):
        r = FourSpace()
        for i in self.getPoints():
            # r.addPoint(changeCoordinate(i,depthDimension,1))
            # nasty optimisation:
            r.thePoints[changeCoordinate(i,depthDimension,1)] = 1
        self.thePoints = r.thePoints
    def scopeOfElementAsDict(self,one_of_the_points):
        assert self.thePoints.has_key(one_of_the_points), \
               "Point %s does not exist in %s" % (one_of_the_points,self.getPoints())
        # Getting scope is like crossSection *3 (and
        # axisProjection to make it into a list)
        # x = self.crossSection(0,one_of_the_points[0])
        # x =    x.crossSection(0,one_of_the_points[1])
        # x =    x.crossSection(0,one_of_the_points[2])
        # (up to theNumDimensions but excluding
        # scopeDimension)
        # (first param becomes 1 if need to go past
        # scopeDimension)
        x = self.crossSection2(one_of_the_points[0:scopeDimension])
        return x.axisProjectionAsDict(0)
    def scopeOfElement(self,one_of_the_points):
        # Returns a list of values in the data dimension
        return self.scopeOfElementAsDict(one_of_the_points).keys()
    def scopeOfElementAsString(self,one_of_the_points,
                               usedData = None):
        data = ""
        for i in self.scopeOfElement(one_of_the_points):
            if not usedData==None:
                # Hack for marking down spaces that have
                # been "flattened" - don't use the same data
                # twice
                if usedData.has_key(i): continue
                else: usedData[i] = 1
            data = data + i[0]
        return data
    def stuffUnderElement(self,one_of_the_points,
                          constraintList,childrenOnly):
        # Returns all points "under" the given element
        # (**** could be more efficient; could cache)
        spaceToInspect = self
        if constraintList:
            # Keep constant any such elemName that exists ABOVE one_of_the_points
            # (keepConstList is (key, point) where key is
            # depth, for sort())
            keepConstList = []
            # debugNegatedList = []
            for pt in self.subSection(scopeDimension,[one_of_the_points[scopeDimension]]).getPoints():
                # (a 'column' of points above that data item; should be short)
                if pt[0] in constraintList and pt[depthDimension] < one_of_the_points[depthDimension]:
                    keepConstList.append((pt[depthDimension],pt))
                # else: debugNegatedList.append(pt)
            keepConstList.sort()
            for _,pt in keepConstList: spaceToInspect=spaceToInspect.stuffUnderElement(pt,[],childrenOnly) # (**** assumes all different depths; might want "covered by" or something)
            # print "Content-type: text/plain\n\nabout to try: point:",one_of_the_points,"keeping const:",keepConstList,"negated list:",debugNegatedList
            # print "attributes:",spaceToInspect.stuffUnderElement(one_of_the_points,[]).getAttributes(),"point:",one_of_the_points,"keeping const:",keepConstList,"negated list:",debugNegatedList
        # End of constraintList stuff
        scope=spaceToInspect.scopeOfElementAsDict(one_of_the_points)
        fs = spaceToInspect.subSectionFromDict(scopeDimension,scope)
        if childrenOnly:
            r = FourSpace()
            for i in fs.getPoints():
                if i[depthDimension] > one_of_the_points[depthDimension]: r.addPoint(i)
            return r
        else: return fs
    def removeElement(self,one_of_the_points):
        # Removes the indicated element (in place)
        scope = self.scopeOfElement(one_of_the_points)
        for i in scope:
            self.removePoint(changeCoordinate(one_of_the_points,scopeDimension,i))
    def pointInFirstElement(self):
        if self.isEmpty(): return None
        return self.minimum(depthDimension).minimum(positionDimension).getAPoint()
    def getAttributes(self):
        # Returns a dictionary; removes from self the
        # points that specify the attributes (destructive)
        # Note: Don't remove in the case where you've got
        # <!attributes>text</!attributes> - this is for
        # model tags like "ALT" when called from markDown
        # (horrible hack)
        retVal = {}
        for (i,rest) in listsToPairs(self.calc_foreach(None)):
            if i[0]=="!attributes":
                pointsToRemove = rest.getPoints()
                rest.removeElement(i)
                firstTime = 1
                for (attrib,val) in listsToPairs(rest.calc_foreach(None)):
                    if firstTime and not attrib[0] == "":
                        # (condition is a hack for markDown
                        # which sometimes leaves an empty
                        # !attributes as cdata)
                        firstTime = 0
                        self.removePoints(pointsToRemove)
                    elif firstTime: break # part of the hack
                    # retVal[attrib[0]]=val.markDown()
                    # **** changing to get around badHack
                    # thing that didn't work (really needs
                    # sorting out) (some attributes somehow
                    # ended up having their data duplicated;
                    # in the code below we assume that there
                    # are no spurious 'blank' points in
                    # there and that the point that happens
                    # to be first gives the true value of
                    # the attribute)
                    # **** THIS WORKAROUND MIGHT BE OBSOLETE
                    # (need to re-test on dieter's thing)
                    retVal[attrib[0]]=""
                    for pt in val.getPoints():
                        if pt[scopeDimension][0]:
                            retVal[attrib[0]]=pt[scopeDimension][0]
                            break
                    # retVal[attrib[0]]=val.pointInFirstElement()[scopeDimension][0]
                break
        return retVal
    def calc_foreach(self,identifier,childrenOnly=0,
                     toplevel_only=0,strip=0):
        # n log n algorithm for forEach
        # identifier can be none; extension could have
        # dictionary or list
        # Return value is two lists; first is of points
        # representing the actual elements over each
        # FourSpace in the second list (if identifier is
        # None then this can be useful)
        if toplevel_only:
            allValidID = self.minimum(depthDimension)
        else: allValidID=self
        if identifier:
            allValidID=allValidID.subSection(0,[identifier])
        if not toplevel_only:
            allValidID = allValidID.minimum(depthDimension)
        # (essential to call minimum(depthDimension) at some
        # point, due to assumption below)
        if allValidID.isEmpty(): return ([], [], self)
        theDepth = allValidID.getAPoint()[depthDimension]

        dict = {}
        for i in allValidID.getPoints():
            # Get the element name and position that this
            # data "belongs" to (at the depth in question).
            # Assumes can't be covered by more than one of
            # the same (name,position,depth)
            # Optimisation: Also assume that no two values
            # of 'scope' are equal unless they are the same
            # object.
            # 2m 18.7 raised to 2m 22.5 !? (2m 6.3 opt)
            # some addPoint optimisations in fourspace: 1m56
            # and some in n_space: 1m57.5 (neglig)
            # checkinterval 10->100: 1m53
            dict[id(i[scopeDimension])] = (i[0],i[positionDimension])
        retVal = {}
        for_rest = FourSpace()
        for i in self.getPoints():
            key = id(i[scopeDimension])
            if dict.has_key(key):
                # This data is going to end up in a subset
                # This particular point might not, depending
                # on childrenOnly etc
                if (not childrenOnly or \
                    i[depthDimension]>=theDepth) and not \
                    (strip and i[0:2]==dict[key] and i[depthDimension]==theDepth):
                    # (**** dimension-specific here)
                    # OK go ahead
                    (name,pos) = dict[key]
                    if not retVal.has_key(pos):
                        retVal[pos] = {}
                    if not retVal[pos].has_key(name):
                        retVal[pos][name] = FourSpace()
                    # retVal[pos][name].addPoint(i)
                    # nasty optimisation:
                    retVal[pos][name].thePoints[i] = 1
                # else pass
            else: # The point will be in for_rest
                for_rest.thePoints[i] = 1
        # Now convert to an ordered list
        positions = retVal.keys()
        positions.sort()
        namesList = []
        retList = []
        for i in positions:
            retList = retList + retVal[i].values()
            for name in retVal[i].keys():
                data = retVal[i][name].getAPoint() \
                       [scopeDimension]
                namesList.append((name, i, theDepth, data))
        return (namesList, retList, for_rest)
    def forEach(self,identifier,childrenOnly=0,
                toplevel_only=0,strip=1,broaden=None):
        #print "Debugger: forEach %s" % identifier
        # Returns a sorted list of N_Space's, one for each
        # position of the element "identifier" (at the
        # highest level that it is found), each containing
        # all the
        # points that intersect the "identifier" at that
        # position.  Returns the empty list if no
        # "identifier" found.  The "identifier" element
        # itself is removed so that nesting (with the same
        # name) works; the value of its position shouldn't
        # matter since the position is only relative.

        # If 'broaden' is not None, it should be a tuple
        # (other,retVal,constraintList,childrenOnly), where
        # 'other' is presumably the 'global' space (see
        # notes on 'broaden') and 'retVal' is a list; for
        # each of the 'foreach' results, the list will be
        # appended with the results of calling
        # 'stuffUnderElement' in 'other' (after applying
        # 'constraintList' to it - see notes)
        # (added a 5th param, broaden[4] - if true, retVal
        # does not include any points in the normal result)

        # start of cache stuff
        cacheElement = None ; calc_foreach = None
        if not broaden: # don't cache "broaden" stuff
            cacheElement = (identifier,childrenOnly,toplevel_only,strip)
            if self.foreachCache.has_key(cacheElement):
                calc_foreach = self.foreachCache[cacheElement]
        if not calc_foreach:
            calc_foreach = self.calc_foreach(identifier,childrenOnly,toplevel_only,strip)
            if cacheElement and not os.environ.has_key("no_psyco"):
                self.foreachCache[cacheElement] = calc_foreach
        (names,listToReturn,for_rest)=calc_foreach
        # end of cache stuff
        actualPositions = []
        for i in range(len(listToReturn)):
            actualPositions.append(names[i][positionDimension])
            if broaden:
                retSpace = broaden[0].stuffUnderElement(names[i],broaden[2],broaden[3]) # broaden[2] is constraint list, broaden[3] is childrenOnly
                if broaden[4]: retSpace.removePoints(listToReturn[i].getPoints()) # broaden to others only (not this subset)
                if broaden[3] and not strip:
                    # broaden and no-strip and childrenOnly
                    # - this is a bit hacky
                    for dat in retSpace.axisProjection(scopeDimension): retSpace.addPoint(changeCoordinate(names[i],scopeDimension,dat))
                broaden[1].append(retSpace)
        return (listToReturn, actualPositions, for_rest)
    def forEachElement(self,broaden=None):
        (names,listToReturn,_) = self.calc_foreach(None)
        if broaden:
            for i in range(len(listToReturn)): broaden[1].append(broaden[0].stuffUnderElement(names[i],broaden[2],broaden[3]))
        return listToReturn
    def transformWrapper(self,model,tracer=None,in_no_markup=0,alwaysOutputXML=0):
        model = model.convertToTuples() # as that should run faster (really need to pass it IN as tuples rather than fourspace, when got time to re-write everything)
        model = transform.preParseModel(model,tracer)
        # (tracer indicates to it whether or not it needs to
        # encode trace information in the parse - otherwise
        # omitted for memory (so tuples cn be de-ref'd after
        # parse))
        xml = self.transformByModel(model,in_no_markup=in_no_markup,tracer=tracer)
        if alwaysOutputXML and xml and not xml[0]=='<':
            # e.g. for the GUI - need to make sure it's a
            # well-formed XML string for converting to tree
            # (Note: if not xml, then it's OK to leave tree
            # empty)
            xml = "<text>"+xml+"</text>"
        if xml and xml[0]=='<':
            xml = """<?xml version="1.0"?>\n""" + xml
        else:
            # It was nomarkup or something; put it back
            # to plain text (i.e. undo the above
            # 'sortEntities')
            xml = unXmlify(xml)
        return xml
    def transformByModel(self,model,ext_stack=None,in_no_markup=0,beginList=[],endList=[],in_wildcard=None,countDic=None,toplevel_only=0,positionCounter=None,tracer=None,ifChangedMap=None,refToGlobal=None):
        # Returns the output as a new FourSpace
        # import sys ; sys.stdout.flush() # *******
        # othrwise never gets to "done" after transform
        # (?? even though that's stderr)
        # (but non-fast versn doesn't throw assert fail)

        # 2.2.2 doesn't crash, 2.2.1 does
        # (2.2.2 doesn't report an error)
        # (& it's not to do with expat - tried 2.2.1 w/out)
        # weather (2.1.3) is ok

        # 2.1.3 and 2.2.2
        # might be some problems with 2.2.1

        # main: 2.2.1 fails, 2.2.2 ok
        # fastmain: 2.2.1 fails, 2.2.2 ok

        # gdb: it threw a segfault (SIGSEGV) (not dumped)
        # couldn't bt, but sthg to do with PyList_Type

        if tracer: transform.beginTrace(tracer,model,self)
        if ifChangedMap == None: ifChangedMap = {}
        if ext_stack == None: ext_stack = []
        if countDic == None: countDic = {}
        if refToGlobal == None: refToGlobal = self

        # positionCounter is for sequential
        # (it's now only used for the firstTime hack)
        retVal = [] # list of strings to concat & return
        for i in beginList:
            retVal.append(sortEntities(i)) # as cdata
        # *** This nesting is getting a bit deep - some of
        # it could do with being put into more methods
        dynamic = None # stuff that cuts across iterations
        # of different model elements in the same data
        for (params,children) in model:
            if dynamic: temp=dynamic.defaultValueNeeded,dynamic.cache
            else: temp = {},{}
            dynamic = transform.DynamicParams(ifChangedMap,refToGlobal)
            dynamic.defaultValueNeeded,dynamic.cache = temp
            # Is it cdata:
            if params.oldName == "": # cdata
                retVal.append(sortEntities(params.asString))
            else:
                # if not explicit cdata, can do some
                # processing
                (fsList, new_ext_stack, need_to_pop) = transform.getFourspaceList(params,dynamic,self,ext_stack,toplevel_only,countDic,not children and not params.modelToCall)
                # Now ready to go
                transform.processFSList(fsList,params,dynamic,children,new_ext_stack,countDic,tracer,retVal)
                # Restore ext_stack:
                if need_to_pop: ext_stack.pop()
                # (need_to_pop is true if new_ext_stack is an alias for ext_stack)
            # end of if not cdata
        # end of for each model element
        for i in endList:
            retVal.append(sortEntities(i))
        if positionCounter:
            positionCounter.firstTime = 0
        retVal = "".join(retVal)
        if tracer: transform.endTrace(tracer,retVal)
        return retVal
    # ############################################
    # Printing out
    # ############################################
    def convertToXML(self,init="MAYBE_XML"):
        # (Note: After transformWrapper was implemented,
        # this method is only used for GUI & tracers &c)
        maybeAddXML = 0
        if init=="MAYBE_XML":
            # Might be XML, or might be plain text
            # (if nomarkup)
            maybeAddXML = 1
            init = ""
        retVal = [init]
        self.convertToXML_inner(retVal,maybeAddXML)
        ret = "".join(retVal)
        if maybeAddXML:
            if ret and ret[0]=='<':
                ret = """<?xml version="1.0"?>\n""" + ret
            else:
                # It was nomarkup or something; put it back
                # to plain text (i.e. undo the below
                # 'sortEntities')
                ret = unXmlify(ret)
        else: pass # use convertToXML("") to get a fragment
        return ret
    def convertToXML_inner(self,retVal,maybeAddXML=0):
        for (p,subspace) in listsToPairs(self.calc_foreach(None)):
            subspace.optimiseForCrossSectioningLastDimension() # as will call scopeOfElementAsString a lot
            rename = p[0]
            if rename == "!attributes": rename="attributes"
            # (to make it valid XML - should only occur if
            # debugging and !attributes is at top level)
            stringToPrint=rename
            subspace.removeElement(p)
            wasEmpty = subspace.isEmpty()
            scope = self.scopeOfElementAsString(p)
            for i in subspace.getAttributes().items():
                stringToPrint="".join([stringToPrint," ",i[0],"=\"",sortEntities(i[1]),"\""])
            # Can we use the <BR /> notation?
            needToClose=1
            if scope == "" and subspace.isEmpty():
                stringToPrint=stringToPrint+" /"
                needToClose=0
            if not rename=="":
                retVal.append("<")
                retVal.append(stringToPrint)
                retVal.append(">")
            if wasEmpty: retVal.append(sortEntities(scope))
            subspace.convertToXML_inner(retVal)
            if not rename=="" and needToClose:
                retVal.append("</")
                retVal.append(rename)
                retVal.append(">")
    def markDownOrAttr(self):
        # Cut-down version of convertToXML that only outputs
        # text.  NB: Destructive! (can rm attributes)
        # (2003-02-05: made non-destructive so cn ref the foreach_cache w/out copying)
        # Has a special case - if the only thing there is
        # an attribute (possibly covered by other elements),
        # returns the value of the attribute rather than
        # taking it away
        attribData = self.subSection(0,["!attributes"]) \
                     .axisProjection(scopeDimension)
        allData = self.axisProjection(scopeDimension)
        if not len(attribData) == len(allData):
            # Remove the attributes
            r = self.makeCopy()
            r.removePoints(self.subSection(\
                scopeDimension,attribData).getPoints())
        else: r=self
        return r.markDown()
    def markDown(self,retVal="",usedData=None):
        if usedData==None: usedData = {}
        for (p,subspace) in listsToPairs(self.calc_foreach(None)):
            subspace.removeElement(p)
            if subspace.isEmpty():
                scope = self.scopeOfElementAsString(p,usedData)
                retVal = retVal + scope
            retVal = subspace.markDown(retVal,usedData)
        return retVal
    def convertToTuples(self):
        # Returns list of [name,attribs,children]
        # (normally length 1 if root node)
        # ('children' can be a string - data; name cn be "")
        retVal = []
        for (p,subspace) in listsToPairs(self.calc_foreach(None)):
            subspace.removeElement(p)
            wasEmpty = subspace.isEmpty()
            attribs = subspace.getAttributes()
            if wasEmpty: # cdata under p
                children=self.scopeOfElementAsString(p)
            else: children = subspace.convertToTuples()
            retVal.append((p[0],attribs,children))
        return retVal
    def debugDump(self):
        ret = []
        # (empty fourspaces on the list w. name=None ??  strip (but within debugdump's call??))
        # **** put "if not el.isEmpty()" for now
        for el in self.forEachElement():
            if not el.isEmpty(): ret.append(el.pointInFirstElement()[0])
        return string.join(ret)

# psyco bug workaround - it segfaults on transformByModel
# (perhaps the pre-parsed model is too complicated)
# 2003-01-30
try:
    import psyco
    psyco.unbind(FourSpace.transformByModel)
    psyco.bind(listsToPairs) # while we're at it
except ImportError:
    pass
