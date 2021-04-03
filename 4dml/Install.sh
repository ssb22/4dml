#!/bin/bash

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

export BinDir=/usr/local/bin
export ManDir=/usr/local/man
export InstallDir=/usr/local/lib/site-python/4dml

export Commands="fast4dml 4dml2.2 fast4dml2.2 cml2xml mml2xml"
export Commands2="4dml $Commands"
# (don't change that without also changing references below)
echo "This will install the 4DML code to $InstallDir"
echo "(overwriting anything that was there before)"
echo "Commands will be installed in $BinDir"
echo "(Commands: $Commands2)"
echo "Manual pages will be installed in $ManDir/man1"
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

popd >/dev/null

echo "Finished."
