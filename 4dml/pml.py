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

# Python Model Language (with introspection etc)
# (could do with other class-based languages also)

import re,types,sys,os,string

import matrix,xml_in
from xml_in import start_element, end_element, char_data
from xmlutil import documentName

def load_pml(module):
    # Loads a Python module and returns the Fourspace
    # (uses xml_in).  Note that the global 'classList' in
    # this module is needed during the transform (hack
    # **** fix?)
    global classList
    xml_in.state.__init__()
    classList = [] # list of classes with filter() methods
    introspect(myImport(module),0)
    xml_in.state.cleanup()
    return xml_in.state.result

def myImport(filename):
    lastSlash = string.rfind(filename,os.sep)
    # **** There is also os.altsep
    if lastSlash>=0:
        sys.path.insert(0,filename[:lastSlash])
        # (inserting at position 0 means modules are
        # preferred from there even before the 4dml
        # directory)
        filename = filename[lastSlash+1:]
    else:
        # Still need to insert current directory, because
        # directory of 4DML code might be different (hence
        # Python might not check the current directory for
        # modules)
        sys.path.insert(0,".")
    dot = string.rfind(filename,".")
    if dot>=0: filename = filename[:dot]
    r=__import__(filename)
    if lastSlash>=0: del sys.path[0] # restore (imported
    # module should still load things from its own
    # directory)
    import cml ; r.cml = cml # **** hack for Chinese notes (not used in thesis); document or something
    return r

def introspect(aClass,haveName=1):
    name = aClass.__name__
    attribs = {} ; children = [] ; children2 = None
    dict = aClass.__dict__
    for k in dict.keys():
        if not re.match("^__.*__$",k):
            k2 = string.replace(k,"_","-")
            val = dict[k]
            if type(val) == types.ClassType:
                children.append(val)
            elif type(val) == types.ListType:
                children2 = val
            elif type(val) == types.StringType:
                if k=="realname": name = val
                else: attribs[k2] = val
            elif (type(val) == types.MethodType or \
                  type(val) == types.FunctionType) and \
                  k=="filter":
                # It has a "filter" method - keep it
                global classList
                attribs[k2] = str(len(classList))
                classList.append(aClass())
            elif type(val)==types.FloatType or \
                 type(val)==types.IntType or \
                 type(val)==types.LongType:
                attribs[k2] = str(val)
    if not children2:
        children2 = children
        if len(children2) > 1:
            sys.stderr.write("Warning: Children of %s may not be ordered correctly (need a list)\n" % (name,))
    if haveName==0 and len(children2)>1:
        # Did say (attribs or len(children2)>1)
        # but attributes of the MODULE are probably not
        # document attributes
        haveName = 1
        name = documentName
    if haveName: start_element(name,attribs)
    for i in children2: introspect(i)
    # **** Need to support renaming the classes (i will be
    # a tuple of (newName, class) or something - handle at
    # start of introspect() )
    if haveName: end_element(name)
