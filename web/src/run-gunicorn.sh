#!/bin/bash

#
# This script starts the gunicorn web server for the
# Flask web application. Gunicorn is the production
# web server, but if you are working on development
# tasks, you may find the Flask development server
# Werkzueg to be more user-friendly. See `run-flask.sh`
# for more information about that.  
#
#

source venv/bin/activate
gunicorn pubhealth.pubhealth:app -k eventlet