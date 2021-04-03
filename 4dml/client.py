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

# Default is to do it on the client, so import doTransform
from server import doTransform,serverID
import sys

def connect(command):
    import popen2 # here, not top-level, because
    # still want the program to run on (embedded) systems
    # where cPickle and popen2 are not available
    global child_stdout, child_stdin
    sys.stderr.write("Connecting to server... ")
    (child_stdout, child_stdin) = popen2.popen2(command)
    while child_stdout.readline() != serverID: pass
    sys.stderr.write("connection established\n")
    # Re-bind the doTransform to do it on the server
    global doTransform
    doTransform = requestTransform

def requestTransform(data):
    import cPickle # see above
    cPickle.dump(data,child_stdin)
    child_stdin.flush()
    return cPickle.load(child_stdout)
