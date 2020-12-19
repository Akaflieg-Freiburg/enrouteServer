#!/bin/bash

rm -rf docs
mkdir docs
echo >docs/.nojekyll 
sphinx-build scripts/sphinx docs
