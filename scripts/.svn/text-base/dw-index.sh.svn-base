#!/bin/sh

# Build the PYTHONPATH for the application.
current_python_path=$PYTHONPATH
python_path=.:../share:/home/tim/svn/pollen/python/trunk
for f in ../share/eggs/*.egg; do
    python_path=$python_path:$f
done
python_path=$python_path:$current_python_path
echo $python_path

#PYTHONPATH=$python_path python index_products.py --config ../public/config.yaml --admin ../admin/indexes/product --public ../public/indexes/product
PYTHONPATH=$python_path python index_static.py -o ../public/indexes/static -n "^/basket/.*$,.*_first$,.*_last$" -s http://www.into-the-light.com/ -a into-the-light.com -i body

