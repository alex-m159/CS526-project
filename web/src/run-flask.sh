#!/bin/bash

#
# This script will run the development server for 
# the Flask framework, called Werkzueg. Werkzueg is
# unsuitable for production deployments, so for anything 
# other than local development, the Gunicorn web server
# will be used. See the `run-gunicorn.sh` file for more
# information.
#
flask run