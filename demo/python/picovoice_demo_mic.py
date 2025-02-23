#
# Copyright 2020-2022 Picovoice Inc.
#
# You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
# file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
import argparse
import os
import struct
import sys
import wave
from threading import Thread
import json

from random import randrange
from picovoice import *
from pvrecorder import PvRecorder


class PicovoiceDemo(Thread):
    def __init__(
            self,
            access_key,
            audio_device_index,
            keyword_path,
            context_path,
            porcupine_library_path=None,
            porcupine_model_path=None,
            porcupine_sensitivity=0.5,
            rhino_library_path=None,
            rhino_model_path=None,
            rhino_sensitivity=0.5,
            endpoint_duration_sec=1.,
            require_endpoint=True,
            output_path=None):
        super(PicovoiceDemo, self).__init__()

        try:
            self._picovoice = Picovoice(
                access_key=access_key,
                keyword_path=keyword_path,
                wake_word_callback=self._wake_word_callback,
                context_path=context_path,
                inference_callback=self._inference_callback,
                porcupine_library_path=porcupine_library_path,
                porcupine_model_path=porcupine_model_path,
                porcupine_sensitivity=porcupine_sensitivity,
                rhino_library_path=rhino_library_path,
                rhino_model_path=rhino_model_path,
                rhino_sensitivity=rhino_sensitivity,
                endpoint_duration_sec=endpoint_duration_sec,
                require_endpoint=require_endpoint)
        except PicovoiceInvalidArgumentError as e:
            args = (
                access_key,
                keyword_path,
                self._wake_word_callback,
                context_path,
                self._inference_callback,
                porcupine_library_path,
                porcupine_model_path,
                porcupine_sensitivity,
                rhino_library_path,
                rhino_model_path,
                rhino_sensitivity,
                endpoint_duration_sec,
                require_endpoint
            )
            print("One or more arguments provided to Picovoice is invalid: ", args)
            print("If all other arguments seem valid, ensure that '%s' is a valid AccessKey" % access_key)
            raise e
        except PicovoiceActivationError as e:
            print("AccessKey activation error")
            raise e
        except PicovoiceActivationLimitError as e:
            print("AccessKey '%s' has reached it's temporary device limit" % access_key)
            raise e
        except PicovoiceActivationRefusedError as e:
            print("AccessKey '%s' refused" % access_key)
            raise e
        except PicovoiceActivationThrottledError as e:
            print("AccessKey '%s' has been throttled" % access_key)
            raise e
        except PicovoiceError as e:
            print("Failed to initialize Picovoice")
            raise e

        self.audio_device_index = audio_device_index
        self.output_path = output_path

    @staticmethod
    def _wake_word_callback():
        print('[wake word]\n')
        os.system("aplay -D sysdefault:CARD=Device mixkit-positive-interface-beep-221.wav")

    @staticmethod
    def _inference_callback(inference):
        if inference.is_understood:
            json_dumps = json.dumps(inference.slots)
            print(json_dumps)
            os.system("curl --location --request POST 'http://192.168.1.128:8123/api/events/rhasspy_%s' "
                      "--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZjQ1MjUzMGRmOTc0MmM5YTQzZTYxNDcwOGZiY2U0MiIsImlhdCI6MTY2OTEzOTc1NywiZXhwIjoxOTg0NDk5NzU3fQ.i05deYebPb6JfRQTVdAKFdnGFEtV1EL3ifK_Vqcm3YQ' "
                      "--header 'Content-Type: application/json' "
                      "--data-raw '%s'" % (inference.intent, json_dumps))
        else:
            understand = [
                "No te he entendido",
                "Que dise cabesa",
                "¿Me lo puedes repetir?"
            ]
            os.system("curl --location --request POST 'http://192.168.1.128:12101/api/text-to-speech' "
                      "--header 'Content-Type: text/plain' "
                      "--data-raw '%s'" % understand[randrange(2)])
            print("Didn't understand the command.\n")

    def run(self):
        recorder = None
        wav_file = None

        try:
            recorder = PvRecorder(device_index=self.audio_device_index, frame_length=self._picovoice.frame_length)
            print("pvrecorder.py version: %s" % recorder.version)
            recorder.start()

            if self.output_path is not None:
                wav_file = wave.open(self.output_path, "w")
                # noinspection PyTypeChecker
                wav_file.setparams((1, 2, 16000, 512, "NONE", "NONE"))

            print("Using device: %s" % recorder.selected_device)
            print('[Listening ...]')

            while True:
                pcm = recorder.read()

                if wav_file is not None:
                    wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

                self._picovoice.process(pcm)
        except KeyboardInterrupt:
            sys.stdout.write('\b' * 2)
            print('Stopping ...')
        finally:
            if recorder is not None:
                recorder.delete()

            if wav_file is not None:
                wav_file.close()

            self._picovoice.delete()

    @classmethod
    def show_audio_devices(cls):
        devices = PvRecorder.get_audio_devices()

        for i in range(len(devices)):
            print('index: %d, device name: %s' % (i, devices[i]))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--access_key',
        help='AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)',
        required=True)

    parser.add_argument('--keyword_path', help="Absolute path to a Porcupine keyword file.")

    parser.add_argument('--context_path', help="Absolute path to a Rhino context file.")

    parser.add_argument('--porcupine_library_path', help="Absolute path to Porcupine's dynamic library.", default=None)

    parser.add_argument('--porcupine_model_path', help="Absolute path to Porcupine's model file.", default=None)

    parser.add_argument(
        '--porcupine_sensitivity',
        help="Sensitivity for detecting wake word. Each value should be a number within [0, 1]. A higher sensitivity " +
             "results in fewer misses at the cost of increasing the false alarm rate.",
        type=float,
        default=0.5)

    parser.add_argument('--rhino_library_path', help="Absolute path to Rhino's dynamic library.", default=None)

    parser.add_argument('--rhino_model_path', help="Absolute path to Rhino's model file.", default=None)

    parser.add_argument(
        '--rhino_sensitivity',
        help="Inference sensitivity. It should be a number within [0, 1]. A higher sensitivity value results in fewer" +
             "misses at the cost of (potentially) increasing the erroneous inference rate.",
        type=float,
        default=0.5)

    parser.add_argument(
        '--endpoint_duration_sec',
        help="Endpoint duration in seconds. An endpoint is a chunk of silence at the end of an utterance that marks "
             "the end of spoken command. It should be a positive number within [0.5, 5]. A lower endpoint duration "
             "reduces delay and improves responsiveness. A higher endpoint duration assures Rhino doesn't return "
             "inference pre-emptively in case the user pauses before finishing the request.",
        type=float,
        default=1.)

    parser.add_argument(
        '--require_endpoint',
        help="If set to `True`, Rhino requires an endpoint (a chunk of silence) after the spoken command. If set to "
             "`False`, Rhino tries to detect silence, but if it cannot, it still will provide inference regardless. "
             "Set to `False` only if operating in an environment with overlapping speech (e.g. people talking in the "
             "background).",
        default='True',
        choices=['True', 'False'])

    parser.add_argument('--audio_device_index', help='index of input audio device', type=int, default=-1)

    parser.add_argument('--output_path', help='Absolute path to recorded audio for debugging.', default=None)

    parser.add_argument('--show_audio_devices', action='store_true')

    args = parser.parse_args()

    if args.require_endpoint.lower() == 'false':
        require_endpoint = False
    else:
        require_endpoint = True

    if args.show_audio_devices:
        PicovoiceDemo.show_audio_devices()
    else:
        if not args.keyword_path:
            raise ValueError("Missing path to Porcupine's keyword file.")

        if not args.context_path:
            raise ValueError("Missing path to Rhino's context file.")

        PicovoiceDemo(
            access_key=args.access_key,
            audio_device_index=args.audio_device_index,
            keyword_path=args.keyword_path,
            context_path=args.context_path,
            porcupine_library_path=args.porcupine_library_path,
            porcupine_model_path=args.porcupine_model_path,
            porcupine_sensitivity=args.porcupine_sensitivity,
            rhino_library_path=args.rhino_library_path,
            rhino_model_path=args.rhino_model_path,
            rhino_sensitivity=args.rhino_sensitivity,
            endpoint_duration_sec=args.endpoint_duration_sec,
            require_endpoint=require_endpoint,
            output_path=os.path.expanduser(args.output_path) if args.output_path is not None else None).run()


if __name__ == '__main__':
    main()
