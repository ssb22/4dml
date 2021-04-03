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
