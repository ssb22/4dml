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
