#!/bin/bash

java -jar demo/java/build/libs/picovoice-mic-demo.jar \
-a nPZc5tQYsrNLy8GO+yxso1E96MhjEdhPZXg+OEuB72Bi2Eff2sWSwA== \
-pm porcupine_params_es.pv \
-k Alfredo_es_raspberry-pi_v2_1_0.ppn \
-rm rhino_params_es.pv \
-c Custom_es_raspberry-pi_v2_1_0.rhn \
-ps 0.3
