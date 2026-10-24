# 参与贡献

感谢你愿意帮忙。本项目旨在让任何人都能检查 AI 模型文件，因此我们重视清晰、简洁，以及对工具能做与不能做的诚实说明。

可用语言：[English](CONTRIBUTING.md) · [Português (PT)](CONTRIBUTING.pt-PT.md) · [Français](CONTRIBUTING.fr.md) · [Español](CONTRIBUTING.es.md) · [Italiano](CONTRIBUTING.it.md) · **中文**

> ⚠️ **本工具不能保证模型是安全的。** 任何贡献都不得削弱或隐藏这一提示：它必须保留在界面、报告和文档中，并出现在所有语言里。

## 开始之前

- **`good first issue`**：任务较小，附有足够上下文，适合首次贡献。**`help wanted`** 标记较大的任务。
- 开始大改动之前，请先开 issue 或讨论，先把方案对齐。

## 从源码运行项目

```text
git clone https://github.com/antonioferreira2/ALF_PickleScan.git
cd ALF_PickleScan
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ALF_picklescan_gui.py
```

编译可执行文件需要 Python **3.11 或更新版本**；测试在 Windows 和 Linux 的 3.11、3.12 上运行。在 Linux 上界面需要 `python3-tk`（`sudo apt install python3-tk`）。

picklescan 的版本只写在 `requirements.txt` 里：workflow 和构建脚本都从那里读取，所以只在那一处修改。

若想打开界面时已加载模型——等同于把文件拖到可执行文件上：

```text
python ALF_picklescan_gui.py model.gguf
```

## 提交 pull request 之前的检查

```text
python -m py_compile ALF_picklescan.py ALF_picklescan_gui.py i18n.py
python -m unittest discover -s tests -v
```

测试会在临时目录生成自己的无害样本，不需要网络，也从不执行它所检查的内容。GitHub 也会在每次 push 和 pull request 时在 Windows 和 Linux 上运行它们（`.github/workflows/tests.yml`）。

## 欢迎的贡献

- **误报与漏报**：请开 issue，附上模型的公开链接、你使用的版本以及被标记的检查项。
- **使用无害示例文件的测试**，用于复现缺陷或覆盖新的检测。
- **翻译**，包括由母语者审阅 README 和本指南。
- **白名单改进**，针对常见架构（Llama、Mistral、Qwen 等），始终附上支持该导入项的来源。
- **文档**：更正与澄清。

## 请不要提交

- **真实的恶意文件**，即使作为测试也不行。测试只能*引用*危险函数，绝不能调用它。
- **私有的或未经授权分享的第三方模型权重**。
- **可执行文件**：它们属于 [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases)。
- **生成的文件**：`ALF_relatorios/`、`build/`、`dist/`、`*.spec` 以及本地的 `ALF_whitelist.txt`。

## 安全

漏洞请使用 GitHub 的**私密漏洞报告**：仓库的 **Security** 标签页，然后 **Report a vulnerability**。绝不要开公开 issue。见 [SECURITY.md](SECURITY.md)。

正常模型被标记为危险，或者恶意模型通过了所有测试，都不属于漏洞：那是普通 issue，请附上检查细节。

## 由 AI 协助的贡献

- 本项目的部分代码和文档是在 AI 工具（包括 Codebuff 代理）协助下编写的。维护者在每个改动进入 `main` 之前都会审阅，Git 历史保留每次提交的作者信息。
- **你要对自己提交的内容负责。** 如果用 AI 写代码，你必须理解它，并能解释它。
- **未测试的改动不予接受。** 请运行上面的命令，并在 pull request 中说明你运行了什么。
- 看起来未经审阅、由 AI 直接生成的 pull request 可能被拒绝：无视项目风格的代码、什么都不验证的测试、与代码不符的空泛注释。
- **Dependabot** 的更新走同样的审阅流程。没有通过测试的内容不会进入 `main`。

## 审阅与合并

- 由维护者审阅 pull request，没有承诺的时限。
- 涉及验证逻辑（分析层、结论、GGUF 与 safetensors 解析器）的改动需要新测试，并在 pull request 中说明。
- 让检查**变得宽松**的改动会被审视得最严格：有疑问时，结论应是黄色而不是绿色。
- 每个 pull request 只做一件事，用一两句话说明问题和解决办法。

## 代码规则

1. **绝不要为了测试而加载恶意模型。** 像现有测试那样，创建一个只*引用*危险函数的 pickle。
2. **不要删除局限性提示。** 本工具不保证安全，文档必须继续这样写。
3. 用户看到的文字位于 `i18n.py`，包含六种语言（`en`、`pt`、`fr`、`es`、`it`、`zh`）。缺失的键会回退到英文，但测试会检查没有语言是不完整的。
4. 白名单改动必须附上导入项的来源（模型或其文档）。
5. 优先使用 Python 标准库而不是新依赖。picklescan 是唯一的外部依赖。
6. 保持代码简单易读：短函数，沿用项目中已有的 `_check()` 和 `veredicto()` 风格。
7. 如果改动界面或引擎，至少用英语、葡萄牙语和中文测试：三种不同文字（拉丁、带重音的拉丁、CJK）。

## 行为准则

请保持尊重。批评想法，而不是人。新人的提问是受欢迎的，值得回答。
