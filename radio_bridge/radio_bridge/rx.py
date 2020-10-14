import logging
import atexit

import wave
import pyaudio
import structlog

from scipy.io import wavfile as wav

LOG = structlog.getLogger(__name__)

# Based on https://github.com/notpike/Hambone (MIT license)

class RX(object):
    def __init__(self,
                 input_device_index: int = 0,
                 file_path: str ="/tmp/recording.wav",
                 audio_format=pyaudio.paInt16,
                 channels: int = 1,
                 rate: int = 48000,
                 chunk_size: int = 2 ** 12,  # frames per buffer
                 time: int = 0.2):
        self._device_index = input_device_index
        self._file_path = file_path
        self._audio_format = audio_format
        self._channels = channels
        self._rate = rate
        self._chunk_size = chunk_size
        self._record_time = time

        self.audio = pyaudio.PyAudio()
        self.stream = None

        self.frames_buffer = []

        device_info = self._get_device_info(self._device_index)
        LOG.debug("Using audio device with index %s and name %s." % (self._device_index,
                                                                     device_info["name"]), **device_info)

        atexit.register(self.stop)

    def _get_device_info(self, device_index: int) -> dict:
        p = pyaudio.PyAudio()
        result = p.get_device_info_by_host_api_device_index(0, device_index)
        return result

    def record_audio(self):
        LOG.trace("Starting recording")

        # Start Recording
        self.stream = self.audio.open(format=self._audio_format,
                                channels=self._channels,
                                input_device_index=self._device_index,
                                rate=self._rate,
                                input=True,
                                frames_per_buffer=self._chunk_size)

        # Read frames
        for i in range(0, int(self._rate / self._chunk_size * self._record_time)):
            data = self.stream.read(self._chunk_size, exception_on_overflow=False)
            self.frames_buffer.append(data)

        # Stop recording
        self.stream.stop_stream()
        self.stream.close()

        self._write_frames_buffer_to_file()

    def _write_frames_buffer_to_file(self):
        if not self.frames_buffer:
            return None

        LOG.trace("Writting frame buffer to %s" % (self._file_path))

        with wave.open(self._file_path, 'wb') as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(self.audio.get_sample_size(self._audio_format))
            wf.setframerate(self._rate)
            wf.writeframes(b''.join(self.frames_buffer))

            self.frames_buffer = []

    def stop(self):
        if self.stream or self.audio:
            LOG.debug("Stopping recording and saving it to a file")

        if self.stream:
            self.stream.close()

        if self.audio:
            self.audio.terminate()

        self._write_frames_buffer_to_file()
