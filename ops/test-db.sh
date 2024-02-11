#!/bin/bash

#
#
#   Use this script to test connectivity to the database.
#   Should return the database version number:
#
#       24.1.2.5
#   
#   Source: https://hub.docker.com/r/clickhouse/clickhouse-server/
#

echo 'SELECT version()' | curl 'http://localhost:18123/' --data-binary @-