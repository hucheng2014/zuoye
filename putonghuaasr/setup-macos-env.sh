#!/usr/bin/env bash
# setup-macos-env.sh — Set up putonghuaasr Python environment on macOS
# Usage: cd ~/zuoye/putonghuaasr && bash setup-macos-env.sh
set -euo pipefail

CONDA_ROOT="${HOME}/miniconda3"
ENV_NAME="asr"
ASR_PYTHON="${CONDA_ROOT}/envs/${ENV_NAME}/bin/python3"
ASR_PIP="${CONDA_ROOT}/envs/${ENV_NAME}/bin/pip"

echo "==> Setting up '${ENV_NAME}' conda environment for putonghuaasr on macOS"

# Ensure conda env exists
if [ ! -x "$ASR_PYTHON" ]; then
  echo "    Creating conda env '${ENV_NAME}' with Python 3.12..."
  "${CONDA_ROOT}/bin/conda" create -n "$ENV_NAME" python=3.12 -y
fi

echo "    Python: $($ASR_PYTHON --version)"

# Install PyTorch for macOS (CPU + MPS/Apple Silicon)
$ASR_PIP install torch torchvision torchaudio

# Install FireRedASR + Qwen3-ASR dependencies
$ASR_PIP install kaldi_native_fbank kaldiio cn2an sentencepiece peft transformers accelerate qwen-asr soundfile

echo ""
echo "==> Environment ready. To use:"
echo "    conda activate asr"
echo ""
echo "    Or run directly:"
echo "    ${ASR_PYTHON} _work_context/local_segment_dual_asr.py --url AUDIO_URL --segments '[{\"id\":1,\"start\":0,\"end\":5}]'"
echo ""
echo "    Verify with:"
echo "    ${ASR_PYTHON} -c \"import torch; print(f'torch {torch.__version__}, MPS={torch.backends.mps.is_available()}')\""
