# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import customtkinter
from PyInstaller.utils.hooks import collect_data_files

# Get CustomTkinter path
ctk_path = os.path.dirname(customtkinter.__file__)

block_cipher = None

# Assets and resources
added_files = [
    (ctk_path, 'customtkinter'), # Crucial for CTK themes
    ('src/llm_scribe/config.py', 'llm_scribe'),
    # ('assets/icon.ico', 'assets'), 
]

hiddenimports = [
    "PIL.ImageTk",
    "PIL.ImageResampling",
    "llm_scribe.ui.styles",
    "llm_scribe.ui.components",
    "llm_scribe.core.ollama_provider",
]

if sys.platform == "win32":
    hiddenimports += [
        "pystray._win32",
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
    ]
elif sys.platform == "darwin":
    hiddenimports += [
        "pystray._darwin",
        "pynput.keyboard._darwin",
        "pynput.mouse._darwin",
    ]
else:
    hiddenimports += [
        "pystray._xorg",
        "pynput.keyboard._xorg",
        "pynput.mouse._xorg",
    ]

a = Analysis(
    ['src/llm_scribe/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LLMScribePro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=(
        "assets/icon.ico"
        if sys.platform == "win32" and os.path.exists("assets/icon.ico")
        else ("assets/icon.icns" if sys.platform == "darwin" and os.path.exists("assets/icon.icns") else None)
    ),
)
