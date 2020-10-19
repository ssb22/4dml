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
