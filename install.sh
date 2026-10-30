#!/bin/sh
# Install cfast without modifying shell startup files or system Python.
set -eu

repo=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
if [ "$(uname -s)" != Linux ]; then
    echo 'cfast currently requires Linux (including Linux in WSL).' >&2
    exit 1
fi
for dependency in python3 g++ prlimit time sh cat; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "Missing $dependency. On Ubuntu/Debian: sudo apt install python3 python3-venv g++ time util-linux" >&2
        exit 1
    fi
done
if ! time --version 2>&1 | command grep -q GNU; then
    echo 'GNU time is required. On Ubuntu/Debian: sudo apt install time' >&2
    exit 1
fi

if [ ! -x "$repo/.venv/bin/python" ]; then
    if ! python3 -m venv "$repo/.venv"; then
        echo 'Could not create the virtual environment. Install python3-venv and rerun ./install.sh.' >&2
        exit 1
    fi
fi
"$repo/.venv/bin/python" -m pip install --disable-pip-version-check -r "$repo/requirements.txt"
"$repo/.venv/bin/oj" test --help >/dev/null

mkdir -p "$HOME/.cf/tests" "$HOME/.local/bin"
chmod +x "$repo/cf.py"
destination="$HOME/.local/bin/cfast"
if [ -e "$destination" ] && [ ! -L "$destination" ]; then
    echo "Refusing to replace a non-symlink: $destination" >&2
    exit 1
fi
ln -sfn "$repo/cf.py" "$destination"
echo "Installed cfast -> $repo/cf.py"
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) printf '%s\n' 'Add this line to ~/.bashrc (or ~/.zshrc), then open a new terminal:' 'export PATH="$HOME/.local/bin:$PATH"' ;;
esac
printf '%s\n' \
    'Next: install Competitive Companion in Chrome/Firefox.' \
    'In its settings, add custom port 27121. Start: cfast listen' \
    'Click the extension on a Codeforces problem, save ID.cpp in Sublime, then run: cfast ID'
