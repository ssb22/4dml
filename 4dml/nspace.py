#!/usr/bin/env python

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

#!/usr/bin/env python

import types

# NB a lot of the inline expansions here didn't get
# significant speedups

import os
try:
    if os.environ.has_key("no_psyco"): raise ImportError
    from psyco.classes import *
# except ImportError: pass
except: pass # jython hack

class N_Space:
    def __init__(self,numDimensions):
        self.thePoints = {}
        self.theNumDimensions = numDimensions
        self.hasChanged = 1
    def isEmpty(self):
        return not self.thePoints
    def getPoints(self): return self.thePoints.keys()
    def getAPoint(self):
        # one point only (arbitrary); exception if empty
        # return self.thePoints.popitem()[0]
        # (NO!  it erases the item!)
        return self.thePoints.keys()[0] # back to the inefficient one
    def addPoint(self,newPoint):
        # newPoint is a tuple
        assert len(newPoint) == self.theNumDimensions, \
               "Wrong number of dimensions"
        assert not self.thePoints.has_key(newPoint), \
               "Duplicate point %s" % (newPoint,)
        self.thePoints[newPoint]=1
        self.hasChanged = 1
    def addPoints(self,newPoints):
        for i in newPoints:
            # self.addPoint(i)
            # Expand inline for optimisation
            assert len(i) == self.theNumDimensions, \
                   "Wrong number of dimensions"
            assert not self.thePoints.has_key(i), \
                   "Duplicate point %s" % (i,)
            self.thePoints[i]=1
        self.hasChanged = 1
    def removePoint(self,pointToRemove):
        try:
            del self.thePoints[pointToRemove]
            self.hasChanged = 1
        except KeyError:
            assert 0, "Tried to remove a non-existent point"
    def removePoints(self,pointsToRemove):
        # for i in pointsToRemove: self.removePoint(i)
        # return
        try:
            for i in pointsToRemove: del self.thePoints[i]
        except KeyError:
            assert 0, "Tried to remove a non-existent point"
        self.hasChanged = 1
    def addCursorPoints(self,cursor,cursorDimens,cursorPos):
        # inserts value 'cursorPos' BEFORE cursorDimens (0+)
        assert 0 <= cursorDimens < self.theNumDimensions
        # < not <=, because theNumDimensions is the NEW
        # number (we're adding a dimension)
        for i in cursor.getPoints():
            assert len(i) == self.theNumDimensions-1, \
                   "Wrong number of dimensions"
            newPt = i[0:cursorDimens] + \
                    (cursorPos,) + \
                    i[cursorDimens:]
            # self.addPoint(newPt)
            # expanding for optimisation
            self.thePoints[newPt] = 1
        self.hasChanged = 1
    def crossSection(self,dimension,value):
        # Opposite to addCursorPoints
        # Takes points where dimension=value and removes
        # that dimension; returns result as a new N_Space
        assert 0 <= dimension < self.theNumDimensions
        section = N_Space(self.theNumDimensions-1)
        for i in self.getPoints():
            if i[dimension] == value:
                newPt=i[0:dimension] + \
                       i[dimension+1:]
                # section.addPoint(newPt)
                # expanding for optimisation
                section.thePoints[newPt] = 1
        return section
    def crossSection2(self,values):
        # for optimisation
        l = len(values)
        if self.__dict__.has_key("optimiseDict1") and l==self.theNumDimensions-1: return self.optimisedCrossSection2(values)
        assert l < self.theNumDimensions
        section = N_Space(self.theNumDimensions-l)
        for i in self.getPoints():
            if i[0:l] == values:
                # section.addPoint(i[l:])
                # expanding for optimisation
                section.thePoints[i[l:]] = 1
        return section
    def optimiseForCrossSectioningLastDimension(self):
        optimiseDict1 = {}
        for i in self.getPoints():
            key = i[:-1]
            if not optimiseDict1.has_key(key): optimiseDict1[key] = N_Space(1)
            optimiseDict1[key].thePoints[i[-1:]] = 1
        self.optimiseDict1 = optimiseDict1
    def optimisedCrossSection2(self,values):
        try:
            return self.optimiseDict1 [ values ]
        except: return N_Space(1)
    def optimiseForSubSectionSingleValue(self,dimension):
        optimiseDict2 = {}
        for i in self.getPoints():
            key = i[dimension]
            if not optimiseDict2.has_key(key): optimiseDict2[key] = N_Space(self.theNumDimensions)
            optimiseDict2[key].thePoints[i] = 1
        self.optimiseDict2 = optimiseDict2
        self.ssOptimisedFor = dimension
    def optimisedSubSectionSingleValue(self,dimension,value):
        try:
            return self.optimiseDict2 [value]
        except: return N_Space(self.theNumDimensions)
    def subSection(self,dimension,values):
        # Removes all points where dimension != values
        # Returns new N_Space with same number of dimensions
        assert isinstance(values, types.ListType), \
               "Argument of subSection %s must be a LIST of values" % (values,)
        if self.__dict__.has_key("optimiseDict2") and len(values)==1 and self.ssOptimisedFor==dimension: return self.optimisedSubSectionSingleValue(dimension,values[0])
        # Convert 'values' to a dictionary because sometimes
        # it's quite long (e.g. as used in scopeOfElement)
        valuesDict = {}
        for i in values: valuesDict[i]=1
        return self.subSectionFromDict(dimension,valuesDict)
    def subSectionFromDict(self,dimension,values):
        if self.__dict__.has_key("optimiseDict2") and self.ssOptimisedFor==dimension:
            r = N_Space(self.theNumDimensions)
            for v in values.keys(): r.addPoints(self.optimisedSubSectionSingleValue(dimension,v).getPoints())
            return r
        # Non-optimised version:
        assert 0 <= dimension < self.theNumDimensions
        section = N_Space(self.theNumDimensions)
        for i in self.getPoints():
            if values.has_key(i[dimension]):
                # section.addPoint(i)
                section.thePoints[i] = 1
        return section
    def minimum(self,dimension):
        # Returns new N_Space only including the points
        # where 'dimension' is at its minimum (the datatype
        # of that dimension has to be sortable for this to
        # work)
        vals = self.axisProjection(dimension)
        if vals == []: return N_Space(self.theNumDimensions)
        # (not just return self, in case later modified)
        vals.sort()
        return self.subSection(dimension,vals[0:1])
    def axisProjectionAsDict(self,dimension):
        assert 0 <= dimension < self.theNumDimensions
        projection = {}
        for i in self.getPoints():
            projection[i[dimension]] = 1
        return projection
    def axisProjection(self,dimension):
        return self.axisProjectionAsDict(dimension).keys()
