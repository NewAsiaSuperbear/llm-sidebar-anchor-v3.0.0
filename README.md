# LLM Scribe Pro v3.0.0 🚀

**LLM Scribe Pro** is a professional-grade, automated recording and management tool for AI conversations. It silently monitors your system clipboard, captures AI dialogues, and organizes them into a secure, searchable local knowledge base.

---

## 🌟 Key Features
- **Smart Scribe Mode**: Real-time clipboard capture with async processing.
- **Modern UI**: YouTube-style dark theme built with `CustomTkinter`.
- **Hardware-Bound Security**: Local data encryption using PBKDF2 + Fernet, tied to your machine's hardware ID.
- **Advanced Export**: Seamless integration with **Obsidian** and **Logseq** via customizable templates (Jinja2).
- **AI-Ready**: Built-in abstraction for local AI providers like **Ollama**.
- **Privacy First**: Zero data leaves your machine. No cloud, no tracking.

---

## 🛠️ Installation

### 1. Prerequisites
- Python 3.9 or higher.
- [Ollama](https://ollama.com) (optional, for AI features).

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/llm-scribe-pro.git
cd llm-scribe-pro

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Configure Secrets
Copy the example environment file and set your custom salt:
```bash
cp .env.example .env
# Edit .env and change LLM_SCRIBE_SALT to a random string
```

---

## 🚀 Usage

### Quick Start (Double-click `app.py`)
After cloning, you can launch the app by double-clicking `app.py` (Windows), or running it from a terminal.
克隆仓库后，可直接双击 `app.py`（Windows），或在终端运行：
```bash
python app.py
```
This launcher will automatically create/reuse a virtual environment and install dependencies on first run.
启动器会在首次运行时自动创建/复用虚拟环境并安装依赖。

**Virtual environment location**
- Default / 默认：`<repo>/.venv`（与 `app.py` 同级）
- Fallback / 备用（当仓库目录不可写时）：
  - Windows: `%LOCALAPPDATA%\LLMScribePro\venvs\...`
  - Other: `$XDG_STATE_HOME/llm_scribe_pro/venvs/...` (or `~/.local/state/...`)
- Override（可选）：设置环境变量 `LLM_SCRIBE_VENV_DIR` 来指定自定义虚拟环境目录。

### Run the Application
```bash
python src/llm_scribe/main.py
```

### Build Standalone EXE (Windows)
```bash
pip install .[dev]
python scripts/build_exe.py
```
The generated EXE will be in the `dist/` folder.

---

## 📂 Project Structure
- `src/llm_scribe/`: Core package containing UI, Core logic, and Utils.
- `assets/`: UI resources and icons.
- `docs/`: Documentation and guides.
- `scripts/`: Build and deployment scripts.
- `tests/`: Unit and integration tests.

---

## 🔒 Security Notice
- All session data is stored in `%APPDATA%\LLMScribePro` (Windows) or `~/.llm_scribe_pro` (Other).
- Encryption is performed locally using keys derived from your `LLM_SCRIBE_SALT` and machine UUID. **Keep your .env file safe and do not share it.**

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
