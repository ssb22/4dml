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

year = "2006"
version = "0.691"
# also update manual.txt (and header.txt if year changes)

# if year changes remember to update header.txt also (rm this comment
# for release)

# 0.691 (released) - bugfix in external=clear (and documented it); fixed bug with start-at/end-at interacting with if-changed

# 0.69 (released) - 'no_psyco' environment additionally suppresses for-each result caching (save RAM when processing large datasets)

# 0.68 (released) - debugdump fix; trace speedup
# Fixed bug where MML sometimes dropped empty elements when processing matrices with multiple independent markup, especially if first element is empty

# 0.67 (released) - slight efficiency improvements; trace option (not on command line and not documented)

# 0.66 (released) - broaden optimisations (not documented; server
# thing)

# 0.65 (released) - added "others-only" param (need to doc
# this); mml2xml bugfix re imports; MML special "switches"
# o/p's (to the fourspace) each mnemonic the first time it's
# used; bugfix when using wildcards with
# number/startAt/endAt attribs

# 0.64 (released) - bugfix for 0.63

# 0.63 (released on website) - added emacs mode; added
# "-dump4dml" (for thesis) (*** not documented), also
# environ FDML_LOGFILE (*** not documented), cml2xml bugfix,
# horrible undocumented 'fdml_ignore_expat_error'
# environment variable, quoted strings as items in CML,
# minor doc fix, python 2.3 speedup &c, added "-spaninput"
# and "-spaninpspec"

# 0.62 (released on website) slight code clean-up; minor fix
# in mml parsing and documentation; documented 'merge'
# (oops); underlines to hyphens in PML; multi-threading (***
# document, & make 'maxNumThreads' in transform.py
# controllable; also check why not working properly on SMP
# (global interpreter lock; need jython))

# 0.61 (released on website) speedup (also things like
# export-code more reliable); documentation bugfix (-link
# needs a parameter); slightly better error handling (and
# ANSI colours if 'COLORTERM'); added 'expected', 'discard';
# model as part of the input; no_expat, no_psyco environment
# variables; gui bugfix; fix PML
# wouldn't load if don't specify directory

# 0.6 (released on website) - various bugfixes; added
# "broaden", "badHack" (**** not documented and isn't very
# nice); MML added "switches" and "switches." specials;
# added "label ... as" special; xml_in does cleanup() more
# often; added _InitPos and _Rename; xmlify < and > in cml
# attribs; version only prints if isatty() (for CGI &c);
# added "reverse", "debugdump", "renumber", "total";
# bugfixed value=""; got other-values to reset
# "defaultValueNeeded" (document?); added "advance" in mml;
# 'nomarkup' temp overridden by 'rename/from'; added
# "python" model param and "-python" command-line option;
# bugfix in group-size

# Refactored some code (runs faster); removed is-attribute;
# removed support for lost data (both were awkward to do in
# the refactored code, and were rarely used)

# 0.54 - added _Unfinished; some code changes so works on
# embedded Python (without expat &c); released on website

# 0.53 - additions to MML: "character" split; "!block
# elemName"; bugfix in "flatten", and "start/end/number"
# when out of bounds, and "count" when called twice; added
# "no-strip", "external=clear";
# released on website (for short time)

# 0.52 - bugfixes; released on website
# 0.51 - released on website
# 0.5 - released on website (no downloads?)
# 0.4.2 - distributed on ACCU conference CD

# (bug that doesn't affect PhD; fix or document)
# - Exceptions when running remotely?? (might need to return
# them, & check return types everywhere) (but server stuff
# not documented anyway?)

# pml: sdf problem: comes out as: order = $ class1, class2, .. ]$
# (also indentation all wrong on "class" example)

guiTitle = "4DML Transform Editor"
textTitle = "4DML transformation utility"
copyright = "(c) " + year + " Silas S. Brown.  No warranty."
aboutMsg = textTitle + "\nVersion " + version + "\n" + copyright
textMsg = textTitle + " v" + version + " " + copyright

import sys
try:
    if sys.stderr.isatty(): sys.stderr.write(textMsg+"\n")
except: pass # hack for jython
