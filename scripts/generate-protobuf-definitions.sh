#!/usr/bin/env bash

SCRIPT_DIR=$(readlink -f "$(dirname "${BASH_SOURCE[0]}")")

# Create initial directory strucutre
mkdir -p generated/protobuf/

touch generated/__init__.py
touch generated/protobuf/__init__.py

# TODO: Make nicer directory layout here
python -m grpc_tools.protoc --experimental_allow_proto3_optional -I${SCRIPT_DIR}/../protobuf --python_out=${SCRIPT_DIR}/../generated/protobuf/ --mypy_out=${SCRIPT_DIR}/../generated/protobuf/ --grpc_python_out=${SCRIPT_DIR}/../generated/protobuf/ ${SCRIPT_DIR}/../protobuf/*.proto

# Fix imports in the generated files - make sure we always use absolute imports
sed -i -E "s/^import messages_pb2 as messages__pb2$/from generated.protobuf import messages_pb2 as messages__pb2/" ${SCRIPT_DIR}/../generated/protobuf/*.py
