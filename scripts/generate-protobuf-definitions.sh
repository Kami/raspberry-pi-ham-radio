#!/usr/bin/env bash
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

SCRIPT_DIR=$(readlink -f "$(dirname "${BASH_SOURCE[0]}")")

# Create initial directory structure for each component / sub project
mkdir -p wx_server/wx_server/generated/protobuf/

touch wx_server/wx_server/generated/__init__.py
touch wx_server/wx_server/generated/protobuf/__init__.py

mkdir -p radio_bridge/radio_bridge/generated/protobuf/

touch radio_bridge/radio_bridge/generated/__init__.py
touch radio_bridge/radio_bridge/generated/protobuf/__init__.py

python -m grpc_tools.protoc --experimental_allow_proto3_optional \
    -I${SCRIPT_DIR}/../protobuf \
    --python_out=${SCRIPT_DIR}/../wx_server/wx_server/generated/protobuf/ \
    --mypy_out=${SCRIPT_DIR}/../wx_server/wx_server/generated/protobuf/ \
    --grpc_python_out=${SCRIPT_DIR}/../wx_server//wx_server/generated/protobuf/ \
    ${SCRIPT_DIR}/../protobuf/*.proto

# Fix imports in the generated files - make sure we always use absolute imports
sed -i -E "s/^import messages_pb2 as messages__pb2$/from wx_server.generated.protobuf import messages_pb2 as messages__pb2/" \
    ${SCRIPT_DIR}/../wx_server/wx_server/generated/protobuf/*.py

python -m grpc_tools.protoc --experimental_allow_proto3_optional \
    -I${SCRIPT_DIR}/../protobuf \
    --python_out=${SCRIPT_DIR}/../radio_bridge/radio_bridge/generated/protobuf/ \
    --mypy_out=${SCRIPT_DIR}/../radio_bridge/radio_bridge/generated/protobuf/ \
    --grpc_python_out=${SCRIPT_DIR}/../radio_bridge/radio_bridge/generated/protobuf/ \
    ${SCRIPT_DIR}/../protobuf/*.proto

# Fix imports in the generated files - make sure we always use absolute imports
sed -i -E "s/^import messages_pb2 as messages__pb2$/from radio_bridge.generated.protobuf import messages_pb2 as messages__pb2/" \
    ${SCRIPT_DIR}/../radio_bridge/radio_bridge/generated/protobuf/*.py
