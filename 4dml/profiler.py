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

# python2 -O

# This thing doesn't work - needs sorting out

import profile,pstats
from main import main

p = profile.OldProfile()
# (OldProfile since profile.Profile in Python 2.1 is buggy and says "Bad call" erroneously)
# (also HotProfile goes wrong)
# (however, note that recursive functions will be wrong)
# and we get "invalid timing data"

p = p.run('main()') # should parse args OK

print "Writing p.timings to file.profile"
f=open("file.profile","w")
import marshal
marshal.dump(p.timings,f)
# f.write("%s" % (p.timings,))
f.close()

# p.timings - pstats.Stats throws exception

stats = pstats.Stats(p)
stats = stats.sort_stats('cumulative')
stats.print_stats(15)
