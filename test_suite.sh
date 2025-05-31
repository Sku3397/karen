#!/bin/bash

# Exit on any failure
set -e

# Run unit tests
python -m unittest discover -s tests