# Deployment

## Recommended Layout

Use GitHub for source files and a separate portable runtime archive for execution.

Keep in the GitHub repository:

- `main.py`
- `afkbot/`
- `config.json`
- `templates/`
- `start_bot.bat`
- `start_portable.bat`

Do not keep in the GitHub repository:

- `portable_runtime/`
- `dist/`
- `.venv/`

## Build a Portable Runtime

On your main development machine:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_portable_runtime.ps1
```

This creates:

- `portable_runtime/`

To package it for upload:

```powershell
powershell -ExecutionPolicy Bypass -File .\package_portable_runtime.ps1
```

This creates:

- `dist/portable_runtime.zip`

## Publish to GitHub

1. Push the repository to GitHub.
2. Create or update a GitHub Release.
3. Upload `dist/portable_runtime.zip` as a release asset.

Recommended release contents:

- Source code from the repository
- `portable_runtime.zip` as the runtime package

## Deploy on Another PC

1. Clone or download the repository from GitHub.
2. Download `portable_runtime.zip` from the matching GitHub Release.
3. Extract it into the project root so you have `portable_runtime/python/python.exe`.
4. Double-click `start_portable.bat`.

You can also use `start_bot.bat`. It will prefer `portable_runtime/` when present.

## Updating After New Features

When you change only Python code, config, or templates:

1. Commit and push the repo changes.
2. No runtime rebuild is needed unless dependencies changed.

When you add or update Python packages:

1. Install the packages in your dev environment.
2. Run `build_portable_runtime.ps1` again.
3. Run `package_portable_runtime.ps1` again.
4. Upload the new `portable_runtime.zip` to GitHub Releases.

## Compatibility Notes

- Best for Windows 64-bit machines.
- The target PC should be able to run the same general Python/OpenCV stack.
- If input behavior differs across PCs or games, retest key actions after deployment.
