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
