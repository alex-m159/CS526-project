#!/bin/bash
jupyter lab --no-browser --port=8888 --ip hub.publichealthhq.xyz --certfile ~/hub.fullchain.pem --keyfile ~/hub.privkey.pem
