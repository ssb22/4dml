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

from version import version
import sys

def doTransform((input,model),t=None):
    # note it's a tuple - can change without worrying about
    # the client/server code
    return input.transformWrapper(model,tracer=t)

import sys
serverID = "4DML server v%s ready\n" % version
def server(infile = sys.stdin, outfile = sys.stdout):
    import cPickle,popen2 # here, not top-level, because
    # still want the program to run on (embedded) systems
    # where cPickle and popen2 are not available
    outfile.write("\n") ; outfile.write(serverID)
    outfile.flush()
    try:
        while 1:
            data = cPickle.load(infile)
            result = doTransform(data)
            cPickle.dump(result,outfile)
            outfile.flush()
    except EOFError:
        pass

if __name__ == "__main__": server()
