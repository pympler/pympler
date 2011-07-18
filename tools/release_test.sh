#!/bin/bash

function check {
    status=$?
    if [ $status -eq 0 ]; then
        echo "$1 ... OK"
    else
        echo "$1 ... FAILED (status=$status)"
    fi
}

python setup.py sdist &> tmp/create_dist.log
check "python setup.py sdist"

for py in '2.4' '2.5' '2.6' '2.7' '3.1' '3.2' 
do
    python="python$py"
    echo "Testing with $python"
    tar xzf dist/Pympler-0.2.0.tar.gz
    cd Pympler-0.2.0
    $python setup.py try &> ../tmp/$python.pre_install.log
    check "$python setup.py try"
    $python setup.py install &> ../tmp/$python.install.log
    check "$python setup.py install"
    $python setup.py test &> ../tmp/$python.post_install.log
    check "$python setup.py test"
    cd ..
    rm -rf Pympler-0.2.0
done
