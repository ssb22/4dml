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

from cml import cml2fs,cml2fs_embedded
from xml_in import xmlFileToFourspace, xmlStringToFourspace
import matrix, client
from pml import load_pml, myImport
import transform
from error import TransformError

from sys import stdin
import sys

def parseCommandLine():
    # runGUI = 1
    runGUI = 0
    input = model = None
    linkName = None
    # Go through the options
    i = 1
    while i < len(sys.argv):
        j = i + 1 # some versions of python don't support ++
        # (code below has "j = i" when it DOESN'T want to
        # use an extra argument)
        if sys.argv[i] == "-model":
            model=xmlFileToFourspace(getFile(sys.argv[j]))
        elif sys.argv[i] == "-cmod":
            model=cml2fs(sys.argv[j])
        elif sys.argv[i] == "-cmodel":
            model=cml2fs_embedded(getFile(sys.argv[j]))
        elif sys.argv[i] == "-pmodel":
            model=load_pml(sys.argv[j])
        elif sys.argv[i] == "-link":
            linkName=sys.argv[j]
        elif sys.argv[i] == "-input":
            input=xmlFileToFourspace(getFile(sys.argv[j]),0,0,linkName)
        elif sys.argv[i] == "-inpspec":
            input=xmlFileToFourspace(getFile(sys.argv[j]),1,0,linkName)
        elif sys.argv[i] == "-spaninput":
            input=xmlFileToFourspace(getFile(sys.argv[j]),0,1,linkName)
        elif sys.argv[i] == "-spaninpspec":
            input=xmlFileToFourspace(getFile(sys.argv[j]),1,1,linkName)
        elif sys.argv[i] == "-minput":
            input=matrix.mmlToFourspace(getFile(sys.argv[j]).read(),linkName)
        elif sys.argv[i] == "-gui": runGUI = 1 ; j = i
        elif sys.argv[i] == "-guidebug": runGUI = 2 ; j = i
        # **** don't like the "magic" number 2
        elif sys.argv[i] == "-dump4dml": runGUI = 3 ; j = i # horrible
        elif sys.argv[i] == "-transform": runGUI = 0 ; j = i
        elif sys.argv[i] == "-python":
            # This is HORRIBLE:
            transform.userModule = myImport(sys.argv[j])
        elif sys.argv[i] == "-remote":
            command = sys.argv[j]
            client.connect(command)
        else:
            j = i
            sys.stderr.write("Warning: Unrecognised option '%s'\n" % (sys.argv[i],))
        i = j + 1
    # Check we've got everything
    errexit = 0
    if not input:
        sys.stderr.write("Error: No input\n")
        errexit = 1
    else:
        if runGUI==3:
            # yuck, horrible hack, misuse of that variable
            # -dump4dml was specified
            runGUI = 0
            print input.thePoints.keys()
        if not model:
            # Try to get one from the input
            model=cml2fs("model expected nomarkup number=1")
            try:
                model=input.transformWrapper(model)
            except TransformError:
                model = None
                sys.stderr.write("Error: No model (and couldn't extract one from input)\n")
                errexit = 1
            if model: model=cml2fs(model)
    if errexit: sys.exit(1)
    return (runGUI, model, input)

def getFile(str):
    if str=="-": return stdin
    else: return open(str,'r')
