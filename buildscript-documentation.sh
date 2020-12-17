#!/bin/bash

mkdir docs
echo >docs/.nojekyll 
sphinx-build scripts/sphinx docs
