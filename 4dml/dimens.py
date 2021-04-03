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

# element definition: (name, position, depth, [scope])
# "scope": could also say "domain"
global scopeDimension,positionDimension,depthDimension
scopeDimension = 3 # how do you make it constant?
# NB Don't change that without revising e.g. scopeOfElement
positionDimension = 1
depthDimension = 2
# (0 is element name)

def changeCoordinate(point,dimension,newVal):
    return point[0:dimension]+(newVal,)+point[dimension+1:]
