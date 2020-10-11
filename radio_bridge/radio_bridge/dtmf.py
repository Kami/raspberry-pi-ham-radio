from typing import List
from typing import Dict
from typing import Any
from typing import Callable
from typing import Optional

import abc
import wave

import structlog
import numpy as np

from scipy.io import wavfile
from scipy.fftpack import fft

from radio_bridge.rx import RX

LOG = structlog.getLogger(__name__)

MAX_SEQUENCE_LENGTH = 6

# Maps DTMF character to frequency boundaries
DTMF_TABLE_HIGH_LOW = {
    '1': [1209, 697], '2': [1336, 697], '3': [1477, 697], 'A': [1633, 697],
    '4': [1209, 770], '5': [1336, 770], '6': [1477, 770], 'B': [1633, 770],
    '7': [1209, 852], '8': [1336, 852], '9': [1477, 852], 'C': [1633, 852],
    '*': [1209, 941], '0': [1336, 941], '#': [1477, 941], 'D': [1633, 941],
}

DTMF_TABLE_LOW_HIGH = {(697, 1209): "1", (697, 1336): "2", (697, 1477): "3", (770, 1209): "4", (770, 1336): "5", (770, 1477): "6", (852, 1209): "7", (852, 1336): "8", (852, 1477): "9", (941, 1209): "*", (941, 1336): "0", (941, 1477): "#", (697, 1633): "A", (770, 1633): "B", (852, 1633): "C", (941, 1633): "D"}

class BaseDTMFDecoderImplementation(object):

    def __init__(self, file_path: str = "/tmp/recording.wav",
                 **implementation_kwargs: Any):
        self._file_path = file_path

    @abc.abstractmethod
    def decode(self) -> str:
        pass

    def _get_sample_rate(self):
        """
        Return sample (frame) rate for the input file.
        """
        with wave.open(self._file_path, 'r') as wav:
            (_, _, sample_rate, _, _, _) = wav.getparams()

        return sample_rate



class FFT1DTMFDecoderImplementation(BaseDTMFDecoderImplementation):
    """
    DTMF decoder based on simple FFT.
    """
    def decode(self, return_on_first_char: bool = True) -> str:
        sample_rate = self._get_sample_rate()

        # Read audio data
        data = wavfile.read(self._file_path, 'rb')

        # data is voice signal. its type is list(or numpy array)
        # Calculate fourier trasform of data
        FourierTransformOfData = np.fft.fft(np.array(data[1]), sample_rate)

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
        result = ""

        for char, frequency_pair in DTMF_TABLE_HIGH_LOW.items():
            if (self._is_number_in_array(FilteredFrequencies, frequency_pair[0]) and
                self._is_number_in_array(FilteredFrequencies, frequency_pair[1])):
                LOG.debug("Found matching DTMF char %s in recording %s" % (char, self._file_path))

                result += char

                if return_on_first_char:
                    return result

        if not result:
            LOG.debug("No matching DTMF sequence found in recording %s" % (self._file_path))

        return result

    def _is_number_in_array(self, array: List[int], number: int) -> bool:
        offset = 5

        for i in range(number - offset, number + offset):
            if i in array:
                return True

        return False


class FFT2DTMFDecoderImplementation(BaseDTMFDecoderImplementation):
    # Based on https://github.com/ribt/dtmf-decoder

    def __init__(self, file_path: str = "/tmp/recording.wav",
                 acceptable_error: int = 20, process_intervals: float = 0.05):
        """
        :param acceptable_error. Acceptable frequency error in hertz.
        :param process_intervals: Process in <x> second intervals.
        """
        super(FFT2DTMFDecoderImplementation, self).__init__(file_path=file_path)

        self._acceptable_error = acceptable_error
        self._process_intervals = process_intervals

    def decode(self, return_on_first_char: bool = True) -> str:
        fps, data = wavfile.read(self._file_path, 'rb')

        assert len(data.shape) == 1, "input is not mono"

        precision = self._process_intervals
        duration = len(data) / fps
        step = int(len(data) // (duration // precision))

        result = ""
        char = ""

        for i in range(0, len(data)-step, step) :
            signal = data[i:i+step]

            fourier = np.fft.fft(signal)
            frequencies = np.fft.fftfreq(signal.size, d=1/fps)

            # Low
            debut = np.where(frequencies > 0)[0][0]
            fin = np.where(frequencies > 1050)[0][0]

            freq = frequencies[debut:fin]
            amp = abs(fourier.real[debut:fin])

            lf = freq[np.where(amp == max(amp))[0][0]]

            delta = self._acceptable_error
            best = 0

            for f in [697, 770, 852, 941] :
                if abs(lf-f) < delta :
                    delta = abs(lf-f)
                    best = f

            lf = best

            # High
            debut = np.where(frequencies > 1100)[0][0]
            fin = np.where(frequencies > 2000)[0][0]

            freq = frequencies[debut:fin]
            amp = abs(fourier.real[debut:fin])

            hf = freq[np.where(amp == max(amp))[0][0]]

            delta = self._acceptable_error
            best = 0

            for f in [1209, 1336, 1477, 1633] :
                if abs(hf-f) < delta :
                    delta = abs(hf-f)
                    best = f

            hf = best

            t = int(i//step * precision)

            if lf == 0 or hf == 0 :
                char = ""
            elif DTMF_TABLE_LOW_HIGH[(lf,hf)] != char:
                char = DTMF_TABLE_LOW_HIGH[(lf,hf)]
                result += char

                if return_on_first_char:
                    return result

        return result



class DTMFDecoder(object):

    implementations = {
        "fft_1": FFT1DTMFDecoderImplementation,
        "fft_2": FFT2DTMFDecoderImplementation
    }

    def __init__(self, file_path: str = "/tmp/recording.wav",
                 implementation: str = "fft_2", **implementation_kwargs: Any):
        self._file_path = file_path
        self._implentation = implementation
        self._implentation_kwargs = implementation_kwargs

        if not implementation in self.implementations:
            raise ValueError("Invalid implementation: %s. Valid implementation are: %s" %
                             (implementation, ",".join(self.implementations)))

        self._decoder = self.implementations[implementation](file_path=file_path,
                                                             **self._implentation_kwargs)

    def decode(self, return_on_first_char: bool = True) -> str:
        """
        :param return_on_first_char: True if we should return on a first matching character instead
                                     of processing the whole sequence.
        """
        return self._decoder.decode()


class DTMFSequenceReader(object):
    def __init__(self, server, sequence_to_plugin_map: Dict[str, Callable] = None):
        """
        :param sequence_to_plugin_map: Maps sequence to a plugin class to be invoked when that
                                       sequence is read.
        """
        self._server = server
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
            # TODO: Check if there are any cron jobs scheduled to run now and run them
            print("in loop")
            print(self._server._cron_jobs_to_run)
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
