#!/bin/bash

source /srv/dav-prc/dav-prc/venv/bin/activate && davprc_add_collection.sh $1 && python /srv/dav-prc/manage.py eoxs_collection_synchronize -i $2

