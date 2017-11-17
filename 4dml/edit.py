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

# Search **** for things that need doing

from dimens import *
from fourspace import FourSpace

class FourSpaceEdit(FourSpace):
    def __init__(self,fs):
        FourSpace.__init__(self)
        self.thePoints = fs.thePoints
        # **** this might go wrong (sharing thePoints with
        # some FourSpace - need to make sure it's discarded)
    def coveredByElement(self,one_of_the_points):
        # Returns a FourSpace that only includes the values
        # covered by the given element, INCLUDING that
        # element itself (if you need to remove it in a
        # top-down thing, call removeElement as well)
        # Note that this can return points lower OR HIGHER
        # than the given one, unless the given point is at
        # the top level.
        scope = self.scopeOfElementAsDict(one_of_the_points)
        section = self.subSectionFromDict(scopeDimension,scope)
        fs = FourSpace()
        fs.copyPointsFrom(section)
        return fs
    def coveredUnderElement(self,one_of_the_points):
        # Like coveredByElement but only returns elements
        # of strictly greater depth (does not return the
        # element in question)
        fs = self.coveredByElement(one_of_the_points)
        for i in fs.getPoints():
            # was [:] copy because we're calling
            # fs.removePoint, but no longer necessary now
            # using getPoints()
            if i[depthDimension] <= one_of_the_points[depthDimension]: fs.removePoint(i)
        return fs
    def coveredOverElement(self,one_of_the_points):
        # The opposite of coveredUnderElement
        fs = self.coveredByElement(one_of_the_points)
        for i in fs.getPoints():
            # [:] copy - as above
            if i[depthDimension] >= one_of_the_points[depthDimension]: fs.removePoint(i)
        return fs
    def properContainersOf(self,one_of_the_points):
        # Like coveredOverElement, but only returns elements
        # that are "proper" containers of the given element,
        # i.e. all data in the scope of the given element
        # is also in the scope of the container.
        # Returns result as TRIPLES (name,position,depth)
        fs = self.coveredOverElement(one_of_the_points)
        scope = self.scopeOfElement(one_of_the_points)
        # All data in 'scope' should also be in the scope
        # of each point in 'fs'.  We can optimise the check
        # by only taking points in 'fs' that have the given
        # item of data in their scope dimension.
        triples = fs.crossSection(scopeDimension,one_of_the_points[scopeDimension])
        for t in triples.getPoints(): # [:] copy - as above
            point = t[0:scopeDimension]+(one_of_the_points[scopeDimension],)+t[scopeDimension:]
            bigScope = fs.scopeOfElementAsDict(point)
            # Check that all data in 'scope' is also in
            # 'bigScope'
            for s in scope:
                if not bigScope.has_key(s):
                    # Triple t is no good
                    triples.removePoint(t)
                    break
        return triples.getPoints()
    def elementsJustUnder(self,one_of_the_points):
        # Like coveredByElement but removes the element
        # itself and only returns the highest (numerically
        # lowest) depth level of the result (but strictly
        # greater than the depth of the given point).
        fs = self.coveredUnderElement(one_of_the_points)
        return fs.minimum(depthDimension)
    def changeElement(self,one_point,new_point):
        # Changes the name/depth/position (in place)
        scope = self.scopeOfElement(one_point)
        self.changeElement2(one_point,new_point,scope)
    def changeElement2(self,one_point,new_point,scope):
        # (service routine)
        for i in scope:
            self.removePoint(changeCoordinate(one_point,scopeDimension,i))
            self.addPoint(changeCoordinate(new_point,scopeDimension,i))
    def swapElements(self,point_1,point_2):
        # Swaps the depths and positions (not name/data)
        # Returns (new_point1, new_point2)
        scope1 = self.scopeOfElement(point_1)
        scope2 = self.scopeOfElement(point_2)
        # (Need to get both scopes in advance to avoid
        # inadvertedly merging elements that only differ
        # in their scope and position)
        # Swap the positions and depths:
        new_pt1 = changeCoordinate(changeCoordinate(point_1,positionDimension,point_2[positionDimension]),depthDimension,point_2[depthDimension])
        new_pt2 = changeCoordinate(changeCoordinate(point_2,positionDimension,point_1[positionDimension]),depthDimension,point_1[depthDimension])
        self.changeElement2(point_1,new_pt1,scope1)
        self.changeElement2(point_2,new_pt2,scope2)
        return (new_pt1, new_pt2)
    def insertPosition(self,parent,position):
        # Creates a new position 'position' under
        # the element specified by the point 'parent',
        # by adding 1 to all positions >= that position
        # in elements just under 'parent'.  Changes are
        # made in-place.
        subSpace=self.elementsJustUnder(parent)
        # Look at each point and see if its position needs
        # updating
        # (Batching up pointsToAdd to avoid "memcpy"-type
        # errors; could of course do the positions in
        # reverse order as an alternative)
        pointsToAdd = []
        for i in subSpace.getPoints():
            if i[positionDimension] >= position:
                self.removePoint(i)
                pointsToAdd.append(changeCoordinate(i,positionDimension,i[positionDimension]+1))
        self.addPoints(pointsToAdd)
    def deletePosition(self,parent,position):
        # Deletes the empty position 'position' under
        # the element specified by the point 'parent',
        # by subtracting 1 from all positions > that
        # position in elements just under 'parent'.
        # Assertion failure if 'position' is not empty.
        # Changes are made in-place.
        subSpace=self.elementsJustUnder(parent)
        # Look at each point and see if its position needs
        # updating
        # (Batching up pointsToAdd to avoid "memcpy"-type
        # errors; could of course do the positions in order
        # as an alternative)
        pointsToAdd = []
        for i in subSpace.getPoints():
            if i[positionDimension] == position:
                return
            # (since *can* have more than one element of
            # same position (e.g. attributes).  i.e. do
            # nothing (quietly) if 'position' is not empty.)
            #assert not i[positionDimension] == position, \
            #"Position %d not empty, e.g. %s" % (position,i)
            if i[positionDimension] > position:
                self.removePoint(i)
                pointsToAdd.append(changeCoordinate(i,positionDimension,i[positionDimension]-1))
        self.addPoints(pointsToAdd)
    # Moving branches around:
    # For manipulating the model
    # Works best if there is a single tree over the data
    # For each item of data in the scope of the element to
    # move, take a cross-section (or subsection) on it.
    # Delete points with depths <= the point to move.
    # Modify other depths by the difference in depth of the
    # point moving (e.g. if newDepth-oldDepth = 1, add 1 to
    # all depths).
    # Add new points to cover with new element and its
    # containers.
    # pt to move, new parent, new position
    # May need to create null data (if it's the only child of its parent, i.e. parent's scope is no greater than its scope)
    # (x,1,1,<data>) (y,2,1,<data>) (MOVE,3,2,<data>) (z,4,1,<data>) TO
    # (x',1,6,<data>) (y',2,3,<data>) (MOVE,3,14,<data>) ..
    def moveElement(self,toMove,oldParent,newParent,newPos):
        # Return value: New value of toMove (for use in
        # selecting it etc)
        self.insertPosition(newParent,newPos)
        scope = self.scopeOfElement(toMove) # before adding any null data that needs to be added
        # Add null data if oldParent would be empty without
        # toMove
        scope2 = self.scopeOfElement(oldParent)
        needNull = 1
        for i in scope2:
            if i not in scope:
                # oldParent has data other than that
                # contained by toMove, so OK (but keep a
                # reference to this point so it can be
                # used as a handle in deletePosition - we
                # won't be able to use oldParent anymore
                # because that particular point (with that
                # data) won't exist)
                needNull = 0
                oldParent2 = changeCoordinate(oldParent,scopeDimension,i)
                break
        if needNull == 1:
            # We need to add a null item to keep oldParent
            # there, and also add it to all its parents, up
            # to the top level.  The easiest way to do this
            # is to choose the item of data from oldParent
            # and add the null item to anything containing
            # it (with depth <= oldParent.depth)
            nullItem = self.uniquifier.makeUnique("")
            pointsToAdd = []
            for i in self.getPoints():
                if i[scopeDimension] == oldParent[scopeDimension] and i[depthDimension] <= oldParent[depthDimension]:
                    pointsToAdd.append(changeCoordinate(i,scopeDimension,nullItem))
            self.addPoints(pointsToAdd)
        # End of adding null data
        # (NB: This data should probably be removed when
        # it is no longer needed, but not to worry because
        # it can't build up *too* much (max 1 per element))
        newDepth=newParent[depthDimension]+1
        deltaDepth=newDepth-toMove[depthDimension]
        containers = self.properContainersOf(newParent) # before this information gets deleted (in case of overlap, although that might not work anyway (ouch))
        fsToAdd = FourSpaceEdit()
        newToMove = None
        for data in scope:
            section=self.subSection(scopeDimension,[data])
            for i in section.getPoints():
                self.removePoint(i)
                if i[depthDimension] > toMove[depthDimension]:
                    fsToAdd.addPoint(changeCoordinate(i,depthDimension,i[depthDimension]+deltaDepth))
                elif i[depthDimension] == toMove[depthDimension] and i[positionDimension] == toMove[positionDimension] and i[0] == toMove[0]:
                    # part of the element itself
                    newPt = changeCoordinate(changeCoordinate(i,depthDimension,newDepth),positionDimension,newPos)
                    fsToAdd.addPoint(newPt)
                    if newToMove == None:
                        # **** This is a horrible
                        # order-dependency for the
                        # prototype.  The GUI has reverseMap
                        # which ONLY maps the first point it
                        # finds on re-scanning the whole
                        # fourspace.  When moving things
                        # interactively, this has to be the
                        # same as newToMove otherwise you
                        # get a key error in reverseMap.
                        # Hence the above conditional.
                        # Horrible.
                        newToMove = newPt
        fsToAdd.fastCoverWith(newParent[0:scopeDimension]+newParent[scopeDimension+1:]) # (i.e. newParent with scopeDimension taken out)
        fsToAdd.coverWith(containers)
        self.addPoints(fsToAdd.getPoints())
        if needNull == 0: self.deletePosition(oldParent2,toMove[positionDimension])
        return newToMove
    def deleteElement(self,toMove,oldParent):
        # ***** This is a horrible hacked copy of the above
        # Need to change that
        # (and NB the deletePosition is after the new one
        # being added on the above; check if can be
        # re-ordered or not if getting the above to call
        # this)
        scope = self.scopeOfElement(toMove) # before adding any null data that needs to be added
        # Add null data if oldParent would be empty without
        # toMove
        scope2 = self.scopeOfElement(oldParent)
        needNull = 1
        for i in scope2:
            if i not in scope:
                # oldParent has data other than that
                # contained by toMove, so OK (but keep a
                # reference to this point so it can be
                # used as a handle in deletePosition - we
                # won't be able to use oldParent anymore
                # because that particular point (with that
                # data) won't exist)
                needNull = 0
                oldParent2 = changeCoordinate(oldParent,scopeDimension,i)
                break
        if needNull == 1:
            # We need to add a null item to keep oldParent
            # there, and also add it to all its parents, up
            # to the top level.  The easiest way to do this
            # is to choose the item of data from oldParent
            # and add the null item to anything containing
            # it (with depth <= oldParent.depth)
            nullItem = self.uniquifier.makeUnique("")
            pointsToAdd = []
            for i in self.getPoints():
                if i[scopeDimension] == oldParent[scopeDimension] and i[depthDimension] <= oldParent[depthDimension]:
                    pointsToAdd.append(changeCoordinate(i,scopeDimension,nullItem))
            self.addPoints(pointsToAdd)
        # End of adding null data
        section=self.subSection(scopeDimension,scope)
        for i in section.getPoints():
            self.removePoint(i)
        if needNull == 0: self.deletePosition(oldParent2,toMove[positionDimension])
    def coverWith(self,containers):
        # Adds containers - a list of triples
        # (name,posn,depth) - to every item of data
        n=N_Space(self.theNumDimensions-1)
        n.addPoints(containers)
        for i in self.axisProjection(scopeDimension):
            self.addCursorPoints(n,scopeDimension,i)
    def fastCoverWith(self,container):
        # Slightly faster version if only one point
        # (assumes scopeDimension is the last dimension)
        for i in self.axisProjection(scopeDimension):
            # self.addPoint(container+(i,))
            # nasty optimisation
            self.thePoints[container+(i,)] = 1
