#!/bin/bash
git pull --no-edit
wget -N http://ssb22.user.srcf.net/4dml.tgz
tar -zxvf 4dml.tgz
git add 4dml/*
git commit -am update && git push
