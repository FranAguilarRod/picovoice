#!/bin/bash

python3 demo/python/picovoice_demo_mic.py \
--access_key nPZc5tQYsrNLy8GO+yxso1E96MhjEdhPZXg+OEuB72Bi2Eff2sWSwA== \
--porcupine_model_path porcupine_params_es.pv \
--keyword_path Alfredo_es_raspberry-pi_v2_1_0.ppn \
--rhino_model_path rhino_params_es.pv \
--context_path Custom_es_raspberry-pi_v2_1_0.rhn \
--porcupine_sensitivity 0.2 \
--audio_device_index 9

