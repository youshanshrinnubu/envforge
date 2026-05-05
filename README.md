# envforge

> Snapshot and reproduce dev environments from existing shell sessions.

---

## Installation

```bash
pip install envforge
```

Or install from source:

```bash
git clone https://github.com/yourname/envforge.git && cd envforge && pip install -e .
```

---

## Usage

**Capture a snapshot of your current environment:**

```bash
envforge snapshot --output my-env.json
```

**Reproduce the environment on another machine:**

```bash
envforge restore --from my-env.json
```

**Preview what will be restored before applying:**

```bash
envforge restore --from my-env.json --dry-run
```

Snapshots capture shell variables, installed packages, active virtualenvs, PATH configuration, and tool versions (e.g. Python, Node, Git).

---

## What Gets Captured

| Component         | Supported |
|-------------------|-----------|
| Shell environment | ✅        |
| pip packages      | ✅        |
| conda envs        | ✅        |
| System tools      | ✅        |
| dotfiles (opt-in) | ✅        |

---

## Requirements

- Python 3.8+
- Works on macOS and Linux

---

## License

MIT © 2024 yourname