#!/bin/bash

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

#!/bin/bash

export BinDir=/usr/local/bin
export ManDir=/usr/local/man
export InfoDir=/usr/local/info
export InstallDir=/usr/local/lib/site-python/4dml

export Commands="fast4dml 4dml2.2 fast4dml2.2 cml2xml mml2xml"
export Commands2="4dml $Commands"
# (don't change that without also changing references below)
echo "This will install the 4DML code to $InstallDir"
echo "(overwriting anything that was there before)"
echo "Commands will be installed in $BinDir"
echo "(Commands: $Commands2)"
echo "Manual pages will be installed in $ManDir/man1"
if which install-info >/dev/null; then
  echo "4dml Info page will be installed in $InfoDir"
else
  unset InfoDir
  echo "Info pages will NOT be installed (install-info command not found)"
fi
echo
echo "If you want to change any of these directories, edit"
echo "the variables at the start of Install.sh."
echo
echo "Press Ctrl-C to abort or Enter to continue."
read

echo "Installing files"
mkdir -p $BinDir
mkdir -p $ManDir/man1
mkdir -p $InstallDir
rm -rf $InstallDir/*
cp *.py 4dml.el $InstallDir
cp 4dml.1.gz $ManDir/man1
chmod +x $InstallDir/main.py $InstallDir/fastmain.py $InstallDir/cml.py $InstallDir/matrix.py $InstallDir/main.2.py $InstallDir/fastmain.2.py
ln -sf $InstallDir/main.py       $BinDir/4dml
ln -sf $InstallDir/fastmain.py   $BinDir/fast4dml
ln -sf $InstallDir/main.2.py     $BinDir/4dml2.2
ln -sf $InstallDir/fastmain.2.py $BinDir/fast4dml2.2
ln -sf $InstallDir/cml.py        $BinDir/cml2xml
ln -sf $InstallDir/matrix.py     $BinDir/mml2xml
for N in $Commands; do
  ln -sf $ManDir/man1/4dml.1.gz  $ManDir/man1/$N.1.gz
done
echo "Compiling"
pushd $InstallDir >/dev/null
python2 compile.py
python2 -O compile.py
if which emacs >/dev/null; then
  echo "Compiling emacs major mode"
  emacs -batch -f batch-byte-compile 4dml.el 2>/dev/null
elif which xemacs >/dev/null; then
  echo "Compiling xemacs major mode"
  xemacs -batch -f batch-byte-compile 4dml.el 2>/dev/null
fi

# export EmacsFile=$(python2 -c "import string;print string.replace(raw_input(),'FILE','$InstallDir/')" < 4dml.el)

popd >/dev/null

if ! test a$InfoDir == a; then
  echo "Installing info page"
  mkdir -p $InfoDir
  rm -f $InfoDir/4dml.info*
  cp 4dml.info $InfoDir
  pushd $InfoDir >/dev/null
  install-info --section Miscellaneous Miscellaneous 4dml.info
  gzip -9 4dml.info
  popd >/dev/null
fi

echo "Finished."
