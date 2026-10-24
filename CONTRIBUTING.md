# Contributing

Thanks for wanting to help. This project exists to make checking AI model files accessible to anyone, so we value clarity, simplicity and honesty about what the tool does and does not do.

Available in: **English** · [Português (PT)](CONTRIBUTING.pt-PT.md) · [Français](CONTRIBUTING.fr.md) · [Español](CONTRIBUTING.es.md) · [Italiano](CONTRIBUTING.it.md) · [中文](CONTRIBUTING.zh.md)

> ⚠️ **This tool does not guarantee that a model is safe.** No contribution may weaken or hide that warning: it stays in the interface, in the reports and in the documentation, in every language.

## Before you start

- **`good first issue`**: small tasks with enough context to start. **`help wanted`** marks the larger ones.
- Open an issue or a discussion before starting something big, so the approach can be agreed first.

## Run the project from the source code

```text
git clone https://github.com/antonioferreira2/ALF_PickleScan.git
cd ALF_PickleScan
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ALF_picklescan_gui.py
```

Python **3.11 or newer** is needed to build the executables; the tests run on 3.11 and 3.12, on Windows and Linux. On Linux the interface needs `python3-tk` (`sudo apt install python3-tk`).

`requirements.txt` is the only place where the picklescan version is written: the workflows and the build scripts read it from there, so change it there and nowhere else.

To open the interface with a model already loaded — the same as dropping a file onto the executable:

```text
python ALF_picklescan_gui.py model.gguf
```

## Checks before opening a pull request

```text
python -m py_compile ALF_picklescan.py ALF_picklescan_gui.py i18n.py
python -m unittest discover -s tests -v
```

The tests generate their own harmless samples in temporary folders, need no network, and never execute what they inspect. GitHub also runs them on Windows and Linux for every push and pull request (`.github/workflows/tests.yml`).

## What is welcome

- **False positives and false negatives.** Open an issue with the model's public link, the version you used and the check that was flagged.
- **Tests with harmless sample files** that reproduce a bug or cover a new detection.
- **Translations**, including a native-speaker review of the READMEs and of this guide.
- **Whitelist improvements** for popular architectures (Llama, Mistral, Qwen, …), always with the source that justifies the import.
- **Documentation** fixes and clarifications.

## What not to send

- **Real malicious files**, not even as a test. A test may only *reference* a dangerous function, never call it.
- **Model weights** that are private, or third-party without permission to share.
- **Executables**: they belong in [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases).
- **Generated files**: `ALF_relatorios/`, `build/`, `dist/`, `*.spec` and the local `ALF_whitelist.txt`.

## Security

Vulnerabilities go through GitHub's **private vulnerability reporting**: repository **Security** tab, then **Report a vulnerability**. Never a public issue. See [SECURITY.md](SECURITY.md).

A legitimate model flagged as dangerous, or a hostile model that passed every test, is not a vulnerability: that is a normal issue, with the details of the check.

## AI-assisted contributions

- Part of the code and documentation of this project was written with help from AI tools, including the Codebuff agent. The maintainer reviews every change before it reaches `main`, and the Git history keeps the authorship of each commit.
- **You are responsible for what you submit.** If you use AI to write code, understand it and be able to explain it.
- **Untested changes are not accepted.** Run the commands above and say in the pull request what you ran.
- Pull requests that look generated without review may be refused: code that ignores the project's style, tests that assert nothing, generic comments that do not match the code.
- **Dependabot** updates go through the same review. Nothing enters `main` without passing the tests.

## Review and merge

- The maintainer reviews the pull requests. There is no guaranteed deadline.
- Changes to the verification logic (analysis layers, verdicts, GGUF and safetensors parsers) need new tests and an explanation in the pull request.
- Changes that make the check **less strict** are the most scrutinised: when in doubt, the verdict must be yellow, not green.
- One pull request per topic, with the problem and the solution in a sentence or two.

## Code rules

1. **Never load a malicious model to test.** Create a pickle that only *references* a dangerous function, as the tests already do.
2. **Do not remove the limitation warnings.** The tool does not guarantee safety, and the documentation must keep saying so.
3. Text shown to the user lives in `i18n.py`, in the six languages (`en`, `pt`, `fr`, `es`, `it`, `zh`). A missing key falls back to English, but the tests check that no language is incomplete.
4. Whitelist changes must come with the source of the import (the model or its documentation).
5. Prefer the Python standard library over new dependencies. picklescan is the only external one.
6. Keep the code simple and readable: short functions, the `_check()` and `veredicto()` style already used in the project.
7. If you touch the interface or the engine, test at least in English, Portuguese and Chinese: three different alphabets (Latin, Latin with accents and CJK).

## Code of conduct

Be respectful. Criticise ideas, not people. Questions from newcomers are welcome and deserve an answer.
