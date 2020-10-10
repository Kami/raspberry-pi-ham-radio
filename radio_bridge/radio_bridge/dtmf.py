from typing import List
from typing import Dict
from typing import Callable

import structlog
import numpy as np

from scipy.io import wavfile as wav
from scipy.fftpack import fft

from radio_bridge.rx import RX

LOG = structlog.getLogger(__name__)

MAX_SEQUENCE_LENGTH = 6

# Maps DTMF character to frequency boundaries
DTMF_TABLE = {
    '1': [1209, 697], '2': [1336, 697], '3': [1477, 697], 'A': [1633, 697],
    '4': [1209, 770], '5': [1336, 770], '6': [1477, 770], 'B': [1633, 770],
    '7': [1209, 852], '8': [1336, 852], '9': [1477, 852], 'C': [1633, 852],
    '*': [1209, 941], '0': [1336, 941], '#': [1477, 941], 'D': [1633, 941],
}


class DTMFDecoder(object):


    def __init__(self,
                 file_path: str = "/tmp/recording.wav",
                 rate: int = 20000):
        self._file_path = file_path
        self._rate = rate

    def decode(self) -> str:
        # reading voice
        data = wav.read(self._file_path, 'rb')

        # data is voice signal. its type is list(or numpy array)
        # Calculate fourier trasform of data
        FourierTransformOfData = np.fft.fft(np.array(data[1]), self._rate)

        # Convert fourier transform complex number to integer numbers
        for i in range(len(FourierTransformOfData)):
            FourierTransformOfData[i] = int(np.absolute(FourierTransformOfData[i]))

        # Calculate lower bound for filtering fourier trasform numbers
        LowerBound = 20 * np.average(FourierTransformOfData)

        # Filter fourier transform data (only select frequencies that X(jw) is greater than LowerBound)
        FilteredFrequencies = []
        for i in range(len(FourierTransformOfData)):
            if (FourierTransformOfData[i] > LowerBound):
                FilteredFrequencies.append(i)

        # Detect and print pressed button
        for char, frequency_pair in DTMF_TABLE.items():
            if (self._is_number_in_array(FilteredFrequencies, frequency_pair[0]) and
                self._is_number_in_array(FilteredFrequencies, frequency_pair[1])):
                LOG.debug("Foound matching DTMF char %s in recording %s" % (char, self._file_path))
                return char

        LOG.debug("No matching DTMF sequence found in recording %s" % (self._file_path))

        return None

    def _is_number_in_array(self, array: List[int], number: int) -> bool:
        offset = 5

        for i in range(number - offset, number + offset):
            if i in array:
                return True

        return False


class DTMFSequenceReader(object):
    def __init__(self, sequence_to_plugin_map: Dict[str, Callable] = None):
        """
        :param sequence_to_plugin_map: Maps sequence to a plugin class to be invoked when that
                                       sequence is read.
        """
        self._sequence_to_plugin_map = sequence_to_plugin_map or {}

        self._started = False
        self._dtmf_decoder = DTMFDecoder()
        self._rx = RX()

    def start(self):
        self._started = True

        return self._read_sequence_and_invoke_plugin()

    def stop(self):
        self._started = False

    def _read_sequence_and_invoke_plugin(self) -> None:
        last_char = None
        read_sequence = ""
        iteration_counter = 0

        # How many loop iterations before we reset the read_sequence array
        max_loop_iterations = 15

        while self._started:
            if iteration_counter >= max_loop_iterations:
                # Max iterations reached, reset read_sequence and start from scratch
                LOG.info("Max iterations reached, reseting read_sequence and iteration counter")

                read_sequence = ""
                iteration_counter = 0

            self._rx.record_audio()
            char = self._dtmf_decoder.decode()

            if char != last_char:
                if not char:
                    iteration_counter += 1
                    continue

                iteration_counter = 0
                read_sequence += char

                LOG.info("Got char %s, current sequence: %s" % (char, read_sequence))

                # If sequence is valid
                plugin = self._sequence_to_plugin_map.get(read_sequence, None)

                if plugin or len(read_sequence) > MAX_SEQUENCE_LENGTH:
                    if plugin:
                        LOG.info("Found valid sequence \"%s\", invoking callback" % (read_sequence))
                        plugin.run()
                    else:
                        LOG.info("Max sequence length limit reached, reseting sequence")

                    read_sequence = ""
            else:
                iteration_counter += 1
                continue

            last_char = char
