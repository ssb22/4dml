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
