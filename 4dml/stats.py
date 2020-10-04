#!/usr/bin/env python2

#    4DML Transformation Utility
#
#    (C) 2002-2006 Silas S. Brown (University of Cambridge Computer Laboratory,
#        Cambridge, UK, http://ssb22.user.srcf.net )
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

# Note: imports are below

# These variables may be set during the run
uses_renumber = 0
non_renumber_matters = 0
used_extern_stack = 0
numPoints = 0
was_error = 0

def logStats():
    if was_error or not numPoints: return
    cpuTime = time.clock()
    log = open(os.environ["FDML_LOGFILE"],'a')

    if os.environ.has_key("FDML_LOG_TYPE"):
        logType = os.environ["FDML_LOG_TYPE"]
    else: logType="dict"
    if os.environ.has_key("FDML_LOG_XAXIS"):
        xaxis = os.environ["FDML_LOG_XAXIS"]
    else: xaxis = " ".join(sys.argv[1:])
    
    if logType=="dict": logDict(log,cpuTime,xaxis)
    elif logType=="point": logPoint(log,cpuTime,xaxis)
    elif logType=="point2": logPoint2(log,cpuTime,xaxis)
    elif logType=="table1": logTable1(log,cpuTime,xaxis)
    elif logType=="table2": logTable2(log,cpuTime,xaxis)
    log.close()

def logPoint(log,cpuTime,xaxis): log.write("%d %.2f # xaxis=%s\n" % (numPoints,cpuTime,xaxis))
def logPoint2(log,cpuTime,xaxis): log.write("%s %.2f # numpoints=%d\n" % (xaxis,cpuTime,numPoints))
def logTable1(log,cpuTime,xaxis): log.write("%s & %s \\\\ \\hline\n" % (xaxis,doTime(cpuTime)))
def logTable2(log,cpuTime,xaxis): log.write("%s & %s & %s \\\\ \\hline\n" % (xaxis,numPoints,doTime(cpuTime)))

def logDict(log,cpuTime,xaxis):
    log.write("""\n
{ \"argv\": %s, \"xaxis\": %s,
  \"uses_renumber\":%d, \"non_renumber_matters\":%d, \"used_extern_stack\":%d,
  \"psyco\":%d, \"expat\":%d, \"__debug__\":%d,
  \"4D pointset size\":%d,
  \"machine_readable_cpu_time\":%.2f,\"Total CPU time\":\"%s\"},\n"""
              % (sys.argv,xaxis,
                 uses_renumber, non_renumber_matters,
                 used_extern_stack,
                 sys.modules.has_key("psyco"),
                 sys.modules.has_key("xml.parsers.expat"),
                 __debug__,numPoints,
                 cpuTime,doTime(cpuTime)))
    # did have clock time as well, but it's not reliable
    # (sometimes get clock < CPU, because it started late)

import os
if os.environ.has_key("FDML_LOGFILE"):
    import atexit, time, sys
    atexit.register(logStats)

def doTime(secs):
    if secs<60: return "%d.%02d" % (secs,secs%1.0*100)
    return "%02d:%02d.%02d" % (secs/60,secs%60,secs%1.0*100)
