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

# hack for jython:
# (some versions fail on "import re" because of its "from
# types import *", but if we do it beforehand and catch the
# exception, it seems to work OK)
try:
    from types import *
    import types
    types.NoneType = type(None)
    types.TupleType = type(())
    types.StringType = type("")
    types.UnicodeType = type(u"")
except: pass
