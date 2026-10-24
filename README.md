<p align="center"><img src="assets/logo.png" alt="ALF_picklescan" width="150"></p>

# ALF_picklescan

**Free, open-source checker for AI model files.** Before you load a model you downloaded, check its integrity, its structure and whether it hides dangerous code. Works with **GGUF**, **safetensors** and **pickle/PyTorch** files (`.bin`, `.pt`, `.pth`, `.pkl`). Windows and Linux. No installation, no programming knowledge needed.

> ⚠️ **This tool does not guarantee that the model is safe.** It only runs tests on the file: integrity (SHA-256), structure, and imports in pickle files. It does not analyse the model's behaviour, and a model trained for a hidden trigger can pass every test. It is a first filter, never a safety guarantee. See [Limitations](#limitations).

Available in: **English** · [Português (PT)](README.pt-PT.md) · [Français](README.fr.md) · [Español](README.es.md) · [Italiano](README.it.md) · [中文](README.zh.md) — the app interface itself is available in all six languages.

![ALF_picklescan verifying a model file and showing a green result](screenshots/gui-en.png)

---

## Why this project exists

Anyone can upload a model to a public hub, and anyone can download it. Model files are not inert data: a **pickle** (used by most PyTorch checkpoints, `.bin`, `.pt`, `.pth`) can execute code the moment you load it. A file that was fine when it was published can be replaced later, and a download can be corrupted or tampered with in transit.

Most people who run local models have no practical way to answer one simple question: *is this file the one the author published, and does it contain anything obviously hostile?* They install the model and hope for the best.

Private scanners and paid platforms answer that question for companies. This project answers it for everyone else: students, researchers, small teams, curious people on a laptop. **Basic safety should not be a paid feature.** ALF_picklescan is free, MIT-licensed, has no account, no telemetry, no server and no limits. It is meant to be copied, improved and given away again.

The author is not selling anything, not collecting data and not asking for donations. The goal is that more people check what they download, and fewer machines are compromised by a file nobody looked at.

## What it does

- Computes the **SHA-256** of the file and compares it with the hash published by the model author.
- Validates the **structure** of GGUF, safetensors and PyTorch zip files — including the GGUF metadata and its **chat template**, which the inference engine renders, and whether each safetensors tensor really has the size its shape and dtype require.
- Reads the **imports** of pickle files **without executing them** (based on the same technique as [picklescan](https://github.com/mmaitre314/picklescan)) and flags known dangerous functions such as `os.system`, `subprocess`, `eval` or `exec`.
- Shows **what the suspicious call would run**: the command, URL or encoded block carried inside the pickle, printed as evidence, together with shell, download, credential-theft, persistence and obfuscation patterns. Nothing is executed.
- Flags **executable files** hidden inside a model package.
- Shows a **traffic-light verdict** and creates an **HTML report** you can keep or share.
- Shows every **check name and detail in the language you choose** (English, Portuguese, French, Spanish, Italian or Chinese), including the report.

The analysis is read-only. The tool never loads, imports or executes the model.

## Download

Go to the [**Releases**](https://github.com/antonioferreira2/ALF_PickleScan/releases) page and pick the file for your system. Windows and Linux builds are published separately.

| System | File | Requirements |
|---|---|---|
| **Windows 10 / 11** (64-bit) | `ALF_picklescan-windows-x64.exe` | None. Double-click. Built with Python 3.11 on Windows Server 2022. |
| **Linux** (x86-64) | `ALF_picklescan-linux-x86_64` | glibc **2.35** or newer — Ubuntu 22.04+, Debian 12+, Fedora 36+, Linux Mint 21+. Built on Ubuntu 22.04. |

Every file has a `.sha256` companion. **Check it before you run the file.**

**Windows** (Command Prompt or PowerShell):
```
certutil -hashfile ALF_picklescan-windows-x64.exe SHA256
```

**Linux:**
```
sha256sum -c ALF_picklescan-linux-x86_64.sha256
chmod +x ALF_picklescan-linux-x86_64
./ALF_picklescan-linux-x86_64
```

### Verify where the executable came from

Every new release also carries a GitHub **build attestation** (*Artifact Attestations*), which ties the file to the workflow that built it and to the exact commit. With the [GitHub CLI](https://cli.github.com/) installed:

```
gh attestation verify ALF_picklescan-windows-x64.exe --repo antonioferreira2/ALF_PickleScan
gh attestation verify ALF_picklescan-linux-x86_64 --repo antonioferreira2/ALF_PickleScan
```

A valid attestation proves **who built** the file and from which code — it does not prove the code is safe. The v2.1.0 release predates this and only has the `.sha256`.

If Windows SmartScreen says the app is not recognised, click **More info → Run anyway**. That warning appears because the executable is not code-signed; a code-signing certificate costs money every year, and this project is free. Always check the hash first, and compare it with the one published on the release page.

Other platforms: the source code runs anywhere Python and Tk are available (macOS included). See [CONTRIBUTING.md](CONTRIBUTING.md) to run it from source.

## How to use

1. Open the app and choose your language in the top-right corner.
2. Click **Choose file** and select the model.
3. Paste the **SHA-256 published by the author** (strongly recommended — look for it on the model's official page).
4. Click **Verify model**.
5. Read the verdict. Click **Open report** for the full details.

You can also **drag the model file onto the executable**: the window opens already analysing that file. On Linux, pass the path as an argument — `./ALF_picklescan model.gguf`.

The report is saved next to the program, in `ALF_relatorios/`.

Command line (Linux or Windows, with Python installed):

```
python ALF_picklescan.py model.gguf --sha256 <hash>
```

Exit codes make it easy to use in scripts and CI pipelines: `0` green, `1` yellow, `2` red, `3` error.

With `--json` the same result is printed as one JSON document (checks, verdict and exit code) and no HTML report is written — handy for pipelines and scripts.

## Verdicts

| Colour | Meaning | What to do |
|---|---|---|
| 🟢 **GREEN** — approved with limitations | Hash confirmed, no alerts | You may use it, respecting the limitations |
| 🟡 **YELLOW** — manual review | No reference hash, imports outside the whitelist, suspicious text or incomplete analysis | Review the details before using |
| 🔴 **RED** — do not use | Hash mismatch, malware found, dangerous imports or invalid structure | Do not use this file |

A green result is **never** shown without a confirmed reference hash.

![ALF_picklescan showing a red verdict, with the download-and-run command found in the file](screenshots/gui-red.png)

A file can pass the hash check and still be hostile. Here the hash is confirmed and the verdict is red, because the file carries a download-and-run command. The sample was generated for this screenshot: it only *references* the function and never runs anything.
## Limitations

- **Not a safety guarantee.** A malicious model trained to behave badly only under a specific trigger can pass every test.
- **No behaviour analysis.** The tool checks the file, not what the model does when it runs.
- **Pickle analysis uses a list of known dangerous functions.** A new payload that is not on the list may pass. Calls with no identifiable imports are flagged yellow for this reason.
- **Trusting the hash.** The hash proves the file matches what was published, not that the publisher is trustworthy.
- **GGUF and safetensors are only structurally validated.** That confirms the file is well-formed, not that the weights are good or honest.

For models you use with tools or access to data (agents, local assistants with file access), **run them isolated**: a container or a virtual machine with no network and no credentials.

## Whitelist of imports

On first run the app creates `ALF_whitelist.txt` next to the program. It lists imports considered normal for PyTorch and NumPy checkpoints. If a legitimate model is flagged yellow only because of a normal import, you may add that import after checking it is expected for that model. Contributions improving the default whitelist for other architectures are very welcome.

If the folder is read-only, the app uses the built-in list and does not fail.

## What this repository contains

Only what is needed to use, build and improve the tool is published here:

| Path | Purpose |
|---|---|
| `ALF_picklescan.py` | Verification engine and command-line interface |
| `ALF_picklescan_gui.py` | Desktop interface (Tk) |
| `i18n.py` | Translations of the interface (EN, PT, FR, ES, IT, ZH) |
| `requirements.txt` | Pinned version of picklescan, the only external dependency |
| `assets/logo.png` | Project logo, used at the top of the READMEs |
| `build_exe.bat`, `build_linux.sh` | Reproducible builds for Windows and Linux |
| `tests/test_smoke.py` | Automated tests with harmless generated samples |
| `screenshots/` | Images used in the documentation |
| `README*.md`, `CONTRIBUTING*.md`, `SECURITY.md`, `LICENSE` | Documentation and licence |
| `.github/workflows/` | Automated tests and the release build for both platforms |

**Not** in the repository, on purpose:

- the **executables** — they live in [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases), so that a new clone stays small and history is not bloated with binaries;
- build output (`build/`, `dist/`, `*.spec`), generated reports (`ALF_relatorios/`) and the local `ALF_whitelist.txt`;
- **model files** of any kind, and any test sample that could be used to attack someone.

To build from source, run `build_exe.bat` on Windows or `./build_linux.sh` on Linux. Both need Python 3.11 or newer and produce a single-file executable that already includes picklescan.

## Roadmap

Public plan. Items may change; progress is tracked in [Issues](https://github.com/antonioferreira2/ALF_PickleScan/issues) and [Discussions](https://github.com/antonioferreira2/ALF_PickleScan/discussions).

1. **v2.1: multilingual interface and Linux build.** ✅ English, Portuguese, French, Spanish, Italian and Chinese in the app; Windows and Linux builds; picklescan included in the executables.
2. **v2.2: payload evidence.** ✅ When a dangerous function is referenced, the report shows the arguments it would receive — the command, the URL, the encoded block — plus shell, download, credential-theft, persistence and obfuscation patterns.
3. **v2.3: translated verification messages.** ✅ Check names, details and the report follow the chosen language, in all six languages.
4. **v2.4: more detections and automation.** ✅ Own detection of `pydoc`, `timeit` and `pip`, plus indirection imports; GGUF chat template; tensor sizes in safetensors; signed build attestations; `--json` output for CI.
5. **v2.5: correctness and robustness.** ✅ Fixes the false warning when the hash was pasted with `sha256:` or in upper case; malformed safetensors headers, truncated ZIPs and very long model names no longer interrupt the analysis; large GGUF arrays are read at full speed; a command-line mistake no longer exits with code 2; the interface no longer stops on an invalid path.
6. **v3.0: more formats.** Support for ONNX and other model formats.

## Contributing

New here? Start with a **`good first issue`**: small, well-described tasks for first contributions.

- Translate the check messages of the engine (`ALF_picklescan.py`) so the reports can be read in other languages.
- Improve the import whitelist for popular architectures (Llama, Mistral, Qwen, etc.), with reviewed examples.
- Add automated tests with harmless sample files.
- Review one of the README translations if you are a native speaker.

To report a false positive, open an issue with the model's public link, the version you used, and the check that was flagged. Do not upload private model files. For the full process, see [CONTRIBUTING.md](CONTRIBUTING.md) — also available in [Português](CONTRIBUTING.pt-PT.md), [Français](CONTRIBUTING.fr.md), [Español](CONTRIBUTING.es.md), [Italiano](CONTRIBUTING.it.md) and [中文](CONTRIBUTING.zh.md).

## Security

To report a vulnerability, follow [SECURITY.md](SECURITY.md). Please do not open a public issue for security problems.

## Author

Created by **António Ferreira** (ALF), to help the community use AI models with a little more safety. It is not a fact-check of any model and it certifies nothing: it is only a basic test, and it can be wrong.

Improvements, forks and better tools are welcome. If you can make something better for society, please do.

## Licence

MIT. See [LICENSE](LICENSE). picklescan is also MIT-licensed.
