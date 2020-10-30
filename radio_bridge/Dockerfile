# -*- coding: utf-8 -*-
# Copyright 2020 Tomaz Muraus
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Example usage:
#
# 1. Build the Docker image
#
# docker build -f Dockerfile -t radio-bridge .
#
# 2. Run the image (in foreground)
#
#
# docker run -it --name radio-bridge --device /dev/snd --volume ${HOME}/radio_bridge:/config:ro --env RADIO_BRIDGE_CONFIG_PATH=/config/radio_bridge.conf --rm -t radio-bridge:latest
#
# To run it in the background, simply add "-d" flag.
# docker run --device /dev/snd -t radio-bridge:latest
#
# On Fedora, you may also need to run chcon -Rt svirt_sandbox_file_t ${HOME}/radio_bridge/
#
# Keep in mind that you need to mound the sound device so the Docker container can access audio in
# and audio out from the host.

FROM python:3.7-slim
MAINTAINER Tomaz Muraus <tomaz@tomaz.me>

RUN apt-get update
RUN apt-get install -y build-essential git

# Needed by pyaudio library
RUN apt-get install -y libportaudio2 portaudio19-dev
# Needed for scipy
RUN apt-get install -y libatlas-base-dev # scipy
# Needed if espeak tts implementation is used
RUN apt-get install -y espeak
# Needed for playing audio files
RUN apt-get install -y mpg123 alsa-utils

# Create virtual into which we will install the deps
RUN python -m venv /opt/virtualenv

ENV PATH="/opt/virtualenv/bin:$PATH"

# Install python dependencies into virtualenv
RUN python -m pip install --upgrade "pip==20.2.4"

ADD requirements.txt requirements.txt
RUN pip --no-cache-dir install -r requirements.txt

# Install the app itself
ADD . /app
WORKDIR /app
RUN python setup.py install

ENV PATH="/opt/virtualenv/bin:$PATH"

ENTRYPOINT ["python", "/opt/virtualenv/bin/radio-bridge"]
