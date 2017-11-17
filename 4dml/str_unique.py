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

import os
try:
    if os.environ.has_key("no_psyco"): raise ImportError
    from psyco.classes import *
# except ImportError: pass
except: pass # jython hack

class StringUniquifier:
    def __init__(self): self.theCounter = 0
    def makeUnique(self,string):
        self.theCounter += 1
        return (string, self.theCounter)
    def reUnique(self,(string,counter)):
        return self.makeUnique(string)

class StringUniquifierForTesting:
    def __init__(self):
        self.theCounters = {}
        # Actually we only need one counter, but using a
        # dictionary keeps the numbers low (for each string)
        # and this makes the tests a little more readable.
    def makeUnique(self,string):
        if self.theCounters.has_key(string):
            counter = self.theCounters [string]
        else:
            counter = 1
        self.theCounters [string] = counter + 1
        return (string, counter)
    def reUnique(self,(string,counter)):
        return self.makeUnique(string)

# 2001-07-18: We need a "global" uniquifier if we want
# things to be unique across different fourspaces (as in
# transformByModel's "divide and conquer" approach).
# Actually it only needs to be shared over each top-level
# one, and you *could* implement this, but this is only
# a prototype (and it's only a uniquifier).  Still, the
# constructor takes a copy of the reference to
# globalUniquifier, so it should be easy to re-implement
# things if necessary.
globalUniquifier = StringUniquifier()

# "import thread" is below (catch errors on EPOC etc)

# (the globalUniquifier is re-constructed as a thread-safe
# version when threads are about to be used)
class ThreadSafeStringUniquifier:
    def __init__(self,oldUniquifier):
        self.theUniquifier = oldUniquifier
        self.theLock = thread.allocate_lock()
    def makeUnique(self,string):
        self.theLock.acquire()
        r = self.theUniquifier.makeUnique(string)
        self.theLock.release()
        return r
    def reUnique(self,param):
        self.theLock.acquire()
        r = self.theUniquifier.reUnique(param)
        self.theLock.release()
        return r

def makeThreadSafe():
    # May be called multiple times, so first time disables
    # itself
    global globalUniquifier
    globalUniquifier = ThreadSafeStringUniquifier(globalUniquifier)
    global makeThreadSafe
    makeThreadSafe = idleFunction
def idleFunction(): pass

try:
    import thread
except ImportError:
    makeThreadSafe = idleFunction
