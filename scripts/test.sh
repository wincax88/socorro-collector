#!/bin/bash -ex

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Test script that does some minor linting for obvious test errors before
# running tests.
#
# Usage: ./scripts/test.sh [NOSEARGS]

NOSE="nosetests collector -s"
ENV=env
PYTHONPATH=.

# Make sure all the test directories have a __init__.py, otherwise they're not
# valid Python modules.
errors=0
while read d
do
    if [ ! -f "$d/__init__.py" ]
    then
        if [ "$(ls -A $d/test*py)" ]
        then
            echo "$d is missing an __init__.py file, tests will not run"
            errors=$((errors+1))
        else
            echo "$d has no tests - ignoring it"
        fi
    fi
done < <(find collector/unittest/* -not -name logs -type d)

if [ $errors != 0 ]
then
    exit 1
fi

# Run tests with any additional parameters that were passed to test.sh
${ENV} PYTHONPATH=${PYTHONPATH} ${NOSE} $@
