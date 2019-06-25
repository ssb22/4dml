#!/bin/bash
git pull --no-edit
wget -N http://people.ds.cam.ac.uk/ssb22/4dml.tgz
tar -zxvf 4dml.tgz
git add 4dml/*
git commit -am update && git push
