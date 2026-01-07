#!/bin/bash
echo ""
echo "============================================================"
echo "  AutoGen + A2A Kit - Developer Setup"
echo "  (AutoGen 소스 수정 가능한 개발자용)"
echo "============================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Install Python 3.10+"
    exit 1
fi
echo "[OK] Python found"

# Git is no longer required (autogen_source included in kit)
echo "[OK] Git not required (autogen_source pre-included)"

# Create venv
echo ""
echo "[1/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "       Created: venv/"
else
    echo "       Already exists: venv/"
fi

# Activate venv
source venv/bin/activate

# Check autogen_source (already included in kit with A2A support)
echo ""
echo "[2/5] Checking AutoGen source (with A2A modifications)..."
if [ ! -d "autogen_source" ]; then
    echo "[ERROR] autogen_source folder not found!"
    echo "        This folder should be included in the kit."
    echo "        Please re-download the complete kit."
    exit 1
else
    echo "       Found: autogen_source/ (includes A2A support)"
fi

# Install AutoGen in editable mode
echo ""
echo "[3/5] Installing AutoGen (editable mode)..."
pip install --upgrade pip -q
pip install -e autogen_source/python/packages/autogen-core
pip install -e autogen_source/python/packages/autogen-agentchat
pip install -e "autogen_source/python/packages/autogen-ext[openai]"

# Install other dependencies
echo ""
echo "[4/5] Installing other dependencies..."
pip install -r requirements.txt

# Verify
echo ""
echo "[5/5] Verifying installation..."
python -c "from a2a_client import create_a2a_tool; print('       a2a_client: OK')"
python -c "from agents import quick_agent; print('       agents: OK')"
python -c "from autogen_agentchat.agents import AssistantAgent; print('       autogen-agentchat: OK (editable)')"
python -c "import autogen_agentchat; print('       Source:', autogen_agentchat.__file__)"

echo ""
echo "============================================================"
echo "  Setup Complete! (Developer Mode)"
echo "============================================================"
echo ""
echo "  AutoGen source: autogen_source/"
echo "  Edit AutoGen:   autogen_source/python/packages/..."
echo ""
echo "  Next steps:"
echo "  1. Set API key:  export OPENAI_API_KEY=sk-..."
echo "  2. Activate:     source venv/bin/activate"
echo "  3. Start A2A:    python a2a_demo/remote_agent/agent.py"
echo "  4. Run example:  python example.py"
echo ""
