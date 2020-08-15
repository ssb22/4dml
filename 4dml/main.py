#!/usr/bin/env python2

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

#!/usr/bin/env python2

from xml_in import makePrintable
from cli import parseCommandLine
from error import TransformError
import version, client, stats
import sys,os

try:
    sys.setcheckinterval(100)  # default 10
except: pass # hack for jython

def main():
    try:
        (runGUI,model,input)=parseCommandLine()
        stats.numPoints = len(input.thePoints)
        # print makePrintable(input.convertToXML())
        if runGUI:
            from gui import doGUI
            doGUI(input, model, runGUI==2)
            # **** don't like the "magic" number 2
        else:
            sys.stderr.write("Transforming...")
            result = client.doTransform((input,model))
            result = makePrintable(result)
            sys.stderr.write(" done\n")
            print result
    except TransformError:
        sys.stderr.write(" error\n")
        stats.was_error = 1
        try:
            useAnsi = os.environ.has_key("COLORTERM")
        except NameError:
            useAnsi = 1 # jython hack
        if useAnsi: ansiColour(15)
        sys.stderr.write("%s\n" % (sys.exc_info()[1],))
        if useAnsi: ansiColour(7)
        sys.exit(1)

def ansiColour(foreground=15,background=0):
    sys.stderr.write("\x1b[%dm\x1b[%d;%dm" % ((background&7)+40,(foreground&8)!=0,(foreground&7)+30))

if __name__ == "__main__":
    main()
