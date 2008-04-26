#!/bin/bash

# Build the PYTHONPATH for the application.
#export LD_LIBRARY_PATH=../../usr/local/lib
current_python_path=$PYTHONPATH
python_path=.:../share
for f in ../share/eggs/*.egg; do
    python_path=$python_path:$f
done
python_path=$python_path:$current_python_path

case "$1" in

    run)
        PYTHONPATH=$python_path twistd -n -o -y admin.tac
        ;;
        
    start)
        PYTHONPATH=$python_path twistd -o -y admin.tac
        ;;
        
    stop)
        if [ -f twistd.pid ]; then
            kill `cat twistd.pid`
        else
            echo "No twistd.pid found"
        fi
        ;;
    kill)
        if [ -f twistd.pid ]; then
            kill -9 `cat twistd.pid`
            rm twistd.pid
        else
            echo "No twistd.pid found"
        fi
        ;;
        
esac
