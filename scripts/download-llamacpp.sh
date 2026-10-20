#!/bin/bash
# One-time download of the llama.cpp inference binary (MIT licensed).
# No compilation needed.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p llamacpp
if [ -x "llamacpp/llama-b11580/llama-cli" ]; then
  echo "llama-cli already present."
  exit 0
fi
VER="b11580"
URL="https://github.com/ggml-org/llama.cpp/releases/download/${VER}/llama-b${VER}-bin-ubuntu-x64.tar.gz"
echo "Downloading llama.cpp ${VER} (ubuntu x64)..."
curl -sL --retry 3 -o /tmp/llamacpp.tgz "$URL"
tar xzf /tmp/llamacpp.tgz -C llamacpp --no-same-owner
rm -f /tmp/llamacpp.tgz
chmod +x llamacpp/llama-b11580/llama-cli
./llamacpp/llama-b11580/llama-cli --version
echo "Installed under llamacpp/"
