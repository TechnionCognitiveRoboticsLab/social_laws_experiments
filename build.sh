#!/bin/sh

for x in `pwd`/unified-planning `pwd`/up-*; do
  cd $x;
  python3 setup.py build;
done
