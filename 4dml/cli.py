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
