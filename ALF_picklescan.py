#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALF_picklescan v2.3
Verificação de modelos de IA antes de os usar.

Formatos suportados:
  - pickle / PyTorch (.bin, .pt, .pth, .pkl)  -> picklescan + análise de imports
  - safetensors (.safetensors)                 -> validação de cabeçalho
  - GGUF (.gguf)                               -> validação de assinatura e versão

Uso:
  python ALF_picklescan.py                              (modo interativo)
  python ALF_picklescan.py modelo.bin
  python ALF_picklescan.py modelo.bin --sha256 <hash>   (hash publicado pelo autor)

Requisitos:
  pip install picklescan==1.0.5

Saída:
  Semáforo no ecrã + relatório HTML em ALF_relatorios/
  Códigos de saída: 0 = verde, 1 = amarelo, 2 = vermelho, 3 = erro
"""

import argparse
import hashlib
import html
import json
import os
import pickletools
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from i18n import DEFAULT_LANG, STRINGS, t

VERSION = "2.3"
if getattr(sys, "frozen", False):
    # Executável empacotado: usar a pasta onde está o .exe (não a pasta temporária do PyInstaller)
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
WHITELIST_FILE = BASE_DIR / "ALF_whitelist.txt"
REPORT_DIR = BASE_DIR / "ALF_relatorios"

PICKLE_EXT = {".bin", ".pt", ".pth", ".pkl", ".pickle"}
SAFETENSORS_EXT = {".safetensors"}

# Ficheiros executáveis não devem vir dentro de um modelo
CODE_EXT_BLOCK = {".so", ".dll", ".exe", ".dylib", ".pyd", ".sh", ".bat", ".ps1", ".jar"}

# Módulos que nunca devem aparecer num pickle de modelo
DANGEROUS_MODULES = {
    "os", "posix", "nt", "subprocess", "sys", "socket", "shutil", "runpy",
    "importlib", "pty", "ctypes", "pickle", "_pickle", "code", "codeop",
    "webbrowser", "multiprocessing", "asyncio", "commands", "platform",
    # Acrescentados na v2.2: usados para esconder ou descarregar código
    "_codecs", "codecs", "marshal", "base64", "binascii", "tempfile",
    "urllib", "http", "ftplib", "smtplib", "requests", "signal",
    "resource", "fcntl", "tty", "termios",
    # Módulos da biblioteca padrão que, por si só, conseguem localizar e
    # executar código (por isso são vermelhos).
    "pydoc", "timeit", "pip", "pkgutil", "pdb", "site", "zipimport",
    "sysconfig", "ntpath", "shlex", "cProfile", "profile", "distutils",
    "idlelib",
}

# Módulos que não executam nada sozinhos mas servem para esconder a chamada
# verdadeira (indireção). Isolados dão AMARELO; junto com um import perigoso
# acompanham o vermelho. Nenhum destes pode estar na DEFAULT_WHITELIST.
SUSPICIOUS_INDIRECTION = {"functools", "operator", "copyreg", "types", "weakref"}
DANGEROUS_BUILTINS = {"eval", "exec", "compile", "__import__", "getattr", "open", "input", "breakpoint"}

# Funções conhecidas por serem usadas em payloads maliciosos em pickle.
# O valor é a chave da razão mostrada ao utilizador (traduzida em i18n.py).
KNOWN_MALICIOUS = {
    "os.system": "reason_exec",
    "os.popen": "reason_exec",
    "posix.system": "reason_exec",
    "nt.system": "reason_exec",
    "subprocess.Popen": "reason_process",
    "subprocess.call": "reason_process",
    "subprocess.run": "reason_process",
    "subprocess.check_output": "reason_process",
    "builtins.eval": "reason_code",
    "builtins.exec": "reason_code",
    "builtins.compile": "reason_code",
    "builtins.__import__": "reason_import",
    "builtins.getattr": "reason_attr",
    "runpy.run_path": "reason_run",
    "socket.socket": "reason_net",
    "urllib.request.urlopen": "reason_net",
    "pty.spawn": "reason_shell",
    "webbrowser.open": "reason_net",
    "_codecs.encode": "reason_obfusc",
    "codecs.encode": "reason_obfusc",
    "codecs.decode": "reason_obfusc",
    "base64.b64decode": "reason_obfusc",
    "marshal.loads": "reason_obfusc",
    "builtins.open": "reason_file",
    "builtins.bytes": "reason_attr",
    "os.environ": "reason_secret",
    "os.environ.get": "reason_secret",
    "os.chmod": "reason_file",
    "os.makedirs": "reason_file",
    "os.remove": "reason_file",
    "os.rename": "reason_file",
    "shutil.rmtree": "reason_file",
    "urllib.request.urlretrieve": "reason_net",
    "socket.create_connection": "reason_net",
}

# Opcodes que chamam funções ao carregar o pickle.
# Normais em PyTorch: o risco avalia-se pelo que é chamado (ver imports).
CALL_OPCODES = {"REDUCE", "BUILD", "INST", "OBJ", "NEWOBJ", "NEWOBJ_EX"}

STRING_OPS = {"SHORT_BINUNICODE", "BINUNICODE", "BINUNICODE8", "UNICODE",
              "SHORT_BINSTRING", "BINSTRING", "STRING"}

# Lista inicial de imports considerados normais em modelos PyTorch/NumPy.
# Editável em ALF_whitelist.txt. Só acrescentar o que confirmares como normal.
DEFAULT_WHITELIST = """\
# Imports normais em checkpoints PyTorch e NumPy.
# Um import por linha, formato modulo.nome. Linhas com # são comentários.
# Só acrescenta um import depois de confirmares que é normal para o modelo.
collections.OrderedDict
torch._utils._rebuild_tensor
torch._utils._rebuild_tensor_v2
torch._utils._rebuild_parameter
torch.FloatStorage
torch.HalfStorage
torch.BFloat16Storage
torch.DoubleStorage
torch.LongStorage
torch.IntStorage
torch.ShortStorage
torch.CharStorage
torch.ByteStorage
torch.BoolStorage
torch.Size
numpy.core.multiarray._reconstruct
numpy._core.multiarray._reconstruct
numpy.ndarray
numpy.dtype
"""

# Padrões procurados nos textos que o pickle transporta. Servem para mostrar o
# payload que seria executado, não para provar que o ficheiro é malicioso.
# O segundo elemento é a chave da razão (traduzida em i18n.py).
PAYLOAD_RULES = (
    (re.compile(r"(?i)\b(curl|wget|powershell|pwsh|certutil|bitsadmin|mshta)\b"),
     "why_download"),
    (re.compile(r"(?i)(base64\s+-d|frombase64string|atob\s*\()"),
     "why_b64"),
    (re.compile(r"(?i)(/bin/(?:ba)?sh|\bcmd(?:\.exe)?\s+/c|\bsh\s+-c\b|\bexec\s+\()"),
     "why_shell"),
    (re.compile(r"(?i)\b(nc|ncat|netcat|socat)\b\s"),
     "why_net"),
    (re.compile(r"(?i)\b(rm\s+-rf|del\s+/[sq]|format\s+c:)"),
     "why_delete"),
    (re.compile(r"(?i)\b(chmod\s+\+x|chattr)\b"),
     "why_execbit"),
    (re.compile(r"(?i)\b(crontab|systemd-run|schtasks|reg\s+add|\.bashrc|\.profile)\b"),
     "why_persist"),
    (re.compile(r"(?i)(os\.environ|AWS_|TOKEN|PASSWORD|SECRET|\.ssh/|id_rsa|credentials)"),
     "why_secret"),
    (re.compile(r"(?i)(https?://|ftp://)"),
     "why_url"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
     "why_ip"),
    (re.compile(r"(?i)\b(eval\s*\(|exec\s*\(|__import__\s*\(|pickle\.loads|__reduce__)"),
     "why_code"),
)

# Blocos longos de base64: possível comando escondido.
BASE64_BLOCK = re.compile(r"[A-Za-z0-9+/=]{120,}")

MAX_STRINGS = 20000      # textos analisados por ficheiro
MAX_EVIDENCE = 10        # chamadas mostradas ao utilizador

HTML_LANG = {"en": "en", "pt": "pt-PT", "fr": "fr", "es": "es", "it": "it", "zh": "zh-CN"}

OK, AVISO, REPROVADO, INFO = "OK", "ATENÇÃO", "REPROVADO", "INFO"


# ---------------------------------------------------------------- utilitários

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_whitelist() -> set:
    try:
        if not WHITELIST_FILE.exists():
            WHITELIST_FILE.write_text(DEFAULT_WHITELIST, encoding="utf-8")
        text = WHITELIST_FILE.read_text(encoding="utf-8")
    except OSError:
        text = DEFAULT_WHITELIST  # pasta só de leitura: usa a lista embutida
    items = set()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            items.add(line)
    return items


def fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.2f} GB"


def _check(nome: str, estado: str, chave: str, detalhe_fn) -> dict:
    """Um resultado de verificação.

    `nome` e `detalhe` ficam em português (compatibilidade e testes). `chave` e
    `detalhe_fn` permitem mostrar o mesmo resultado em qualquer idioma, o que é
    o que a interface e o relatório usam.
    """
    return dict(nome=nome, estado=estado, chave=chave,
                detalhe=detalhe_fn("pt"), detalhe_fn=detalhe_fn)


def texto_check(check: dict, lang: str = DEFAULT_LANG):
    """Devolve (título, detalhe) da verificação no idioma pedido."""
    chave = check.get("chave", "")
    titulo = t(chave, lang) if chave else ""
    if not chave or titulo == chave:
        titulo = check.get("nome", titulo)
    fn = check.get("detalhe_fn")
    detalhe = fn(lang) if callable(fn) else check.get("detalhe", "")
    return titulo, detalhe


# ------------------------------------------------------ análise de pickle

def _is_suspicious_name(full: str) -> bool:
    mod, _, attr = full.partition(".")
    root = mod.split(".")[0]
    return (root in DANGEROUS_MODULES or full in KNOWN_MALICIOUS
            or (root in ("builtins", "__builtin__") and attr in DANGEROUS_BUILTINS))


def _as_text(arg) -> str:
    if isinstance(arg, str):
        return arg
    if isinstance(arg, (bytes, bytearray)):
        return bytes(arg).decode("latin-1", "replace")
    return str(arg)


def _analyse_stream(fh) -> dict:
    """Lê os opcodes sem executar nada e recolhe os globals (imports).

    Além dos imports, guarda **os argumentos** que cada chamada suspeita receberia
    e os textos que o ficheiro transporta. É isso que permite mostrar o payload
    (o comando, o URL) sem nunca correr o pickle.
    """
    globals_found = []
    opcodes = {}
    unresolved = 0
    recent_strings = []
    calls = []
    texts = []
    current = None      # global à espera dos argumentos
    pending = []        # textos entre o global e a chamada
    for opcode, arg, _pos in pickletools.genops(fh):
        name = opcode.name
        opcodes[name] = opcodes.get(name, 0) + 1
        if name in STRING_OPS:
            text = _as_text(arg)
            recent_strings.append(text)
            recent_strings = recent_strings[-2:]
            if current is not None and len(pending) < 8:
                pending.append(text)
            if len(texts) < MAX_STRINGS:
                texts.append(text[:2000])
        elif name in ("GLOBAL", "INST"):
            mod, _, attr = str(arg).partition(" ")
            globals_found.append((mod, attr))
            full = f"{mod}.{attr}"
            current, pending = (full, []) if _is_suspicious_name(full) else (None, [])
            recent_strings = []
        elif name == "STACK_GLOBAL":
            if len(recent_strings) == 2:
                mod, attr = recent_strings
                globals_found.append((mod, attr))
                full = f"{mod}.{attr}"
                current, pending = (full, []) if _is_suspicious_name(full) else (None, [])
            else:
                unresolved += 1
                current, pending = None, []
            recent_strings = []
        elif name in CALL_OPCODES:
            if current is not None and len(calls) < MAX_EVIDENCE * 5:
                calls.append((current, list(pending)))
            current, pending = None, []
    return {"globals": globals_found, "opcodes": opcodes, "unresolved": unresolved,
            "calls": calls, "texts": texts}


def analyse_pickle(path: Path) -> list:
    """Devolve [(nome_interno, resultado)] para cada pickle do ficheiro."""
    results = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.endswith(".pkl")]
            if not names:
                raise ValueError("no .pkl entry (data.pkl)")
            for n in names:
                with z.open(n) as fh:
                    results.append((n, _analyse_stream(fh)))
    else:
        with open(path, "rb") as fh:
            results.append(("(whole file)", _analyse_stream(fh)))
    return results


def indirection_imports(globals_found) -> list:
    """Imports de indireção encontrados, ordenados e sem repetições."""
    return sorted({f"{mod}.{attr}" for mod, attr in globals_found
                   if mod.split(".")[0] in SUSPICIOUS_INDIRECTION})


def check_globals(globals_found, whitelist):
    """Devolve ({nome: chave_da_razão}, [imports fora da whitelist])."""
    danger, unknown = {}, set()
    for mod, attr in globals_found:
        full = f"{mod}.{attr}"
        root = mod.split(".")[0]
        if root in DANGEROUS_MODULES or full in KNOWN_MALICIOUS:
            danger[full] = KNOWN_MALICIOUS.get(full, "reason_system")
        elif root in ("builtins", "__builtin__") and attr in DANGEROUS_BUILTINS:
            danger[full] = "reason_code"
        elif full not in whitelist:
            unknown.add(full)
    return dict(sorted(danger.items())), sorted(unknown)


def _texto_curto(texto, limite=160) -> str:
    """Uma linha legível: sem caracteres de controlo e sem blocos enormes."""
    t = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", str(texto))
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= limite else t[: limite - 1] + "…"


def _payload_hits(texts) -> list:
    """Devolve [(texto, [chaves_de_razão])] — uma linha por texto, sem repetir."""
    hits, index = [], {}
    for text in texts:
        razoes = [why for pattern, why in PAYLOAD_RULES if pattern.search(text)]
        if not razoes:
            continue
        key = text[:160]
        if key in index:
            index[key].extend(r for r in razoes if r not in index[key])
            continue
        index[key] = razoes
        hits.append((text, index[key]))
        if len(hits) >= MAX_EVIDENCE:
            break
    return hits


def _picklescan_library(path: Path):
    """Corre o picklescan dentro deste processo.

    É o caminho usado pelo executável empacotado (o picklescan vai lá dentro) e
    também serve quando o comando `picklescan` não está no PATH.
    """
    try:
        from picklescan import scanner
    except ImportError:
        return None
    try:
        result = scanner.scan_file_path(str(path))
    except Exception as ex:
        return 2, f"analysis failed: {ex}"
    globais = "\n".join(
        f"{g.module}.{g.name} [{getattr(g.safety, 'value', g.safety)}]" for g in result.globals
    )
    if result.scan_err:
        return 2, "picklescan could not read one or more parts of the file.\n" + globais
    return (1 if result.issues_count else 0), (globais or "no suspicious global found")


def run_picklescan(path: Path):
    """Devolve (código, saída).

    0 = limpo, 1 = padrão malicioso, 2 = análise incompleta, None = indisponível.
    Tenta, por ordem: o comando `picklescan`, a biblioteca no próprio processo e
    `python -m picklescan`. Assim funciona com pip install, sem o comando no PATH,
    e dentro do .exe/.bin que já leva o picklescan embutido.
    """
    exe = shutil.which("picklescan")
    if exe:
        try:
            r = subprocess.run([exe, "--path", str(path)], capture_output=True,
                               text=True, timeout=7200,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired:
            return 2, "picklescan timed out"
        except OSError as ex:
            return 2, f"could not run picklescan: {ex}"
        return r.returncode, (r.stdout + r.stderr).strip()

    embutido = _picklescan_library(path)
    if embutido is not None:
        return embutido

    if not getattr(sys, "frozen", False):
        try:
            import picklescan  # noqa: F401
        except ImportError:
            pass
        else:
            try:
                r = subprocess.run([sys.executable, "-m", "picklescan", "--path", str(path)],
                                   capture_output=True, text=True, timeout=7200,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except subprocess.TimeoutExpired:
                return 2, "picklescan timed out"
            return r.returncode, (r.stdout + r.stderr).strip()

    return None, "picklescan is not installed"


def pickle_checks(path: Path, whitelist: set) -> list:
    checks = []

    # 1. Conteúdo do ZIP (formato PyTorch)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
        bad = tuple(n for n in names if Path(n).suffix.lower() in CODE_EXT_BLOCK)
        checks.append(_check(
            "Ficheiros executáveis dentro do modelo", REPROVADO if bad else OK, "chk_exec",
            (lambda bad: lambda lang: "\n".join(bad[:20]) if bad else t("d_none", lang))(bad)))
        py = tuple(n for n in names if n.lower().endswith(".py"))
        if py:
            checks.append(_check(
                "Código Python dentro do modelo", AVISO, "chk_pycode",
                (lambda py: lambda lang: t("d_pycode", lang, list="\n".join(py[:20])))(py)))

    # 2. picklescan
    code, saida = run_picklescan(path)
    if code == 0:
        checks.append(_check("picklescan", OK, "chk_picklescan",
                             lambda lang: t("d_picklescan_ok", lang)))
    elif code == 1:
        checks.append(_check("picklescan", REPROVADO, "chk_picklescan",
                             (lambda s: lambda lang: t("d_picklescan_bad", lang, output=s))(saida)))
    elif code is None:
        checks.append(_check("picklescan", AVISO, "chk_picklescan",
                             lambda lang: t("d_picklescan_missing", lang)))
    else:
        checks.append(_check("picklescan", AVISO, "chk_picklescan",
                             (lambda c, s: lambda lang: t("d_picklescan_partial", lang,
                                                          code=c, output=s))(code, saida)))

    # 3. Análise própria de imports (whitelist)
    try:
        streams = analyse_pickle(path)
    except Exception as e:
        checks.append(_check("Leitura da estrutura pickle", AVISO, "chk_read",
                             (lambda m: lambda lang: t("d_read_error", lang, error=m))(str(e))))
        return checks

    all_globals, unresolved = [], 0
    all_calls, all_texts = [], []
    for _name, r in streams:
        all_globals += r["globals"]
        unresolved += r["unresolved"]
        all_calls += r["calls"]
        all_texts += r["texts"]

    danger, unknown = check_globals(all_globals, whitelist)
    if danger:
        itens = tuple(danger.items())
        checks.append(_check(
            "Imports perigosos", REPROVADO, "chk_danger",
            (lambda itens: lambda lang: "\n".join(f"{n} - {t(r, lang)}" for n, r in itens))(itens)))
    else:
        checks.append(_check("Imports perigosos", OK, "chk_danger",
                             lambda lang: t("d_none", lang)))

    # 3b. Indireção: functools, operator, copyreg... Não executam nada por si,
    # mas são o truque habitual para esconder a chamada perigosa de um filtro.
    indirect = indirection_imports(all_globals)
    if indirect:
        lista = tuple(indirect[:20])
        extra = len(indirect) - len(lista)

        def _indirect(lang, lista=lista, extra=extra, estado=None):
            txt = "\n".join(lista)
            if extra:
                txt += "\n" + t("d_unknown_more", lang, count=extra)
            return (txt + "\n" + t("d_indirection_note", lang) + "\n"
                    + t("d_indirection_reason", lang,
                        reason=t("reason_indirection", lang)))

        checks.append(_check("Imports de indireção", REPROVADO if danger else AVISO,
                             "chk_indirection", _indirect))
    else:
        checks.append(_check("Imports de indireção", OK, "chk_indirection",
                             lambda lang: t("d_none", lang)))

    # 4. Evidência: o que cada chamada suspeita receberia (o payload em si)
    if all_calls:
        mostradas = tuple(all_calls[:MAX_EVIDENCE])
        restantes = len(all_calls) - len(mostradas)

        def _payload(lang, mostradas=mostradas, restantes=restantes):
            linhas = []
            for full, args in mostradas:
                linhas.append(full)
                if args:
                    linhas.append(t("d_payload_receives", lang,
                                    args=" | ".join(_texto_curto(a, 120) for a in args[:3])))
                linhas.append(t("d_payload_effect", lang,
                                reason=t(KNOWN_MALICIOUS.get(full, "reason_system"), lang)))
            if restantes:
                linhas.append(t("d_payload_more", lang, count=restantes))
            return "\n".join(linhas)

        checks.append(_check("Payload das chamadas suspeitas", REPROVADO, "chk_payload", _payload))
    else:
        checks.append(_check("Payload das chamadas suspeitas", OK, "chk_payload",
                             lambda lang: t("d_payload_none", lang)))

    # 5. Comandos, downloads, shells, credenciais e obfuscação nos textos
    hits = _payload_hits(all_texts)
    escondido = [x for x in all_texts if BASE64_BLOCK.search(x)][:3]
    if hits or escondido:
        dados = tuple((_texto_curto(txt), tuple(why)) for txt, why in hits)
        cifrados = tuple((len(x), _texto_curto(x, 60)) for x in escondido)
        estado = REPROVADO if danger else AVISO

        def _texto(lang, dados=dados, cifrados=cifrados):
            linhas = [t("d_text_line", lang,
                        reasons="; ".join(t(w, lang) for w in why), text=txt)
                      for txt, why in dados]
            linhas += [t("d_encoded_line", lang, count=n, text=txt) for n, txt in cifrados]
            return "\n".join(linhas) + "\n" + t("d_text_note", lang)

        checks.append(_check("Comandos, URLs ou ofuscação no conteúdo", estado, "chk_text", _texto))
    else:
        checks.append(_check("Comandos, URLs ou ofuscação no conteúdo", OK, "chk_text",
                             lambda lang: t("d_text_none", lang)))

    if unknown:
        lista = tuple(unknown[:40])
        extra = len(unknown) - len(lista)

        def _unknown(lang, lista=lista, extra=extra):
            txt = "\n".join(lista)
            if extra:
                txt += "\n" + t("d_unknown_more", lang, count=extra)
            return txt + "\n" + t("d_unknown_hint", lang)

        checks.append(_check("Imports fora da whitelist", AVISO, "chk_unknown", _unknown))
    else:
        checks.append(_check("Imports fora da whitelist", OK, "chk_unknown",
                             lambda lang: t("d_unknown_none", lang)))

    if unresolved:
        checks.append(_check("Referências não resolvidas", AVISO, "chk_unresolved",
                             (lambda n: lambda lang: t("d_unresolved", lang, count=n))(unresolved)))

    unique_imports = sorted({f"{m}.{a}" for m, a in all_globals})
    checks.append(_check(
        "Imports encontrados (informativo)", INFO, "chk_imports_info",
        (lambda n, lst: lambda lang: t("d_imports_info", lang, count=n,
                                       list="\n".join(lst)))(len(unique_imports),
                                                             tuple(unique_imports[:40]))))

    return checks


# ------------------------------------------------- safetensors e GGUF

# Bytes por elemento em safetensors. Um dtype fora desta lista não é erro:
# fica AMARELO porque o tamanho não pode ser validado.
DTYPE_SIZES = {
    "F64": 8, "F32": 4, "F16": 2, "BF16": 2, "I64": 8, "I32": 4, "I16": 2,
    "I8": 1, "U8": 1, "BOOL": 1, "F8_E4M3": 1, "F8_E5M2": 1,
}


def _numel(shape) -> int:
    """Número de elementos de um tensor, a partir da shape."""
    total = 1
    for lado in shape:
        total *= int(lado)
    return total


def check_safetensors(path: Path):
    size = path.stat().st_size
    with open(path, "rb") as f:
        raw = f.read(8)
        if len(raw) < 8:
            return REPROVADO, lambda lang: t("d_st_small", lang)
        n = struct.unpack("<Q", raw)[0]
        if n > 100 * 1024 * 1024 or 8 + n > size:
            return REPROVADO, lambda lang: t("d_st_header", lang)
        try:
            cab = json.loads(f.read(n).decode("utf-8"))
        except Exception as e:
            return REPROVADO, (lambda err: lambda lang: t("d_st_json", lang,
                                                          err=err))(str(e))
    limite = size - 8 - n
    count = 0
    intervalos = []
    problemas = []      # inconsistências: REPROVADO
    avisos = []         # não foi possível validar: AVISO
    for nome, info in cab.items():
        if nome == "__metadata__":
            continue
        try:
            ini, fim = info["data_offsets"]
        except Exception:
            return REPROVADO, (lambda n_: lambda lang: t("d_st_nooffs", lang, name=n_))(nome)
        if not (0 <= ini <= fim <= limite):
            return REPROVADO, (lambda n_: lambda lang: t("d_st_range", lang, name=n_))(nome)
        count += 1
        intervalos.append((ini, fim, nome))

        # O espaço reservado tem de bater certo com shape x dtype. Um ficheiro
        # truncado ou remontado à mão falha aqui.
        dtype = str(info.get("dtype", "")).upper()
        esperado = DTYPE_SIZES.get(dtype)
        shape = info.get("shape")
        if esperado is None:
            avisos.append(("d_st_dtype", {"name": nome, "dtype": info.get("dtype", "?")}))
            continue
        if not isinstance(shape, list) or not all(
                isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in shape):
            avisos.append(("d_st_shape", {"name": nome}))
            continue
        previsto = _numel(shape) * esperado
        if previsto != fim - ini:
            problemas.append(("d_st_size", {"name": nome, "expected": previsto,
                                            "found": fim - ini}))

    intervalos.sort()
    for (_i1, f1, n1), (i2, _f2, n2) in zip(intervalos, intervalos[1:]):
        if i2 < f1:
            problemas.append(("d_st_overlap", {"a": n1, "b": n2}))
            break

    if problemas:
        chave, valores = problemas[0]
        resto = len(problemas) - 1

        def _detalhe(lang, chave=chave, valores=valores, resto=resto):
            texto = t(chave, lang, **valores)
            return texto + (("\n" + t("d_st_more", lang, count=resto)) if resto else "")

        return REPROVADO, _detalhe
    if avisos:
        chave, valores = avisos[0]
        return AVISO, (lambda c, v: lambda lang: t(c, lang, **v))(chave, valores)
    return OK, (lambda c: lambda lang: t("d_safetensors_ok", lang, count=c))(count)


def check_gguf(path: Path):
    with open(path, "rb") as f:
        magic = f.read(4)
        ver = f.read(4)
    if magic != b"GGUF" or len(ver) < 4:
        return REPROVADO, lambda lang: t("d_gguf_magic", lang)
    v = struct.unpack("<I", ver)[0]
    if v not in (2, 3):
        return AVISO, (lambda v: lambda lang: t("d_gguf_ver", lang, v=v))(v)
    return OK, (lambda v: lambda lang: t("d_gguf_ok", lang, v=v))(v)


# ------------------------------------------------- metadados GGUF
#
# O cabeçalho GGUF traz pares chave/valor. Um deles, tokenizer.chat_template,
# é um texto Jinja que o motor de inferência renderiza: é a única parte de um
# GGUF que pode instruir o programa a fazer algo. Lemos apenas o cabeçalho e os
# metadados; os tensores nunca são lidos nem carregados para memória.

GGUF_STRING, GGUF_ARRAY = 8, 9
GGUF_SCALARS = {
    0: ("<B", 1), 1: ("<b", 1), 2: ("<H", 2), 3: ("<h", 2),
    4: ("<I", 4), 5: ("<i", 4), 6: ("<f", 4), 7: ("<B", 1),
    10: ("<Q", 8), 11: ("<q", 8), 12: ("<d", 8),
}
GGUF_MAX_STRING = 1024 * 1024   # 1 MB por texto
GGUF_MAX_KV = 100000            # pares chave/valor
GGUF_MAX_ARRAY = 5000000        # elementos por array (vocabulários reais são menores)
GGUF_TEMPLATE_KEY = "tokenizer.chat_template"

# Marcas de execução ou exfiltração dentro de um template Jinja.
TEMPLATE_MARKERS = re.compile(
    r"(?i)(\bimport\b|\bos\.|subprocess|__import__|\beval\b|\bexec\b|curl|wget|https?://)")
# Razões que, juntas às marcas acima, dão vermelho em vez de amarelo.
TEMPLATE_STRONG = {"why_download", "why_shell", "why_net", "why_code"}


class _GGUFProblem(Exception):
    """Leitura que não se pode concluir: o ficheiro fica AMARELO."""

    def __init__(self, chave: str, **kw):
        super().__init__(chave)
        self.chave, self.kw = chave, kw


class _GGUFReader:
    """Lê o cabeçalho e os metadados sem nunca sair dos limites do ficheiro."""

    def __init__(self, fh, size: int):
        self.fh = fh
        self.size = size

    def _bytes(self, n: int) -> bytes:
        posicao = self.fh.tell()
        if n < 0 or posicao + n > self.size:
            raise _GGUFProblem("d_gguf_incomplete")
        dados = self.fh.read(n)
        if len(dados) != n:
            raise _GGUFProblem("d_gguf_incomplete")
        return dados

    def saltar(self, n: int) -> None:
        posicao = self.fh.tell()
        if n < 0 or posicao + n > self.size:
            raise _GGUFProblem("d_gguf_incomplete")
        self.fh.seek(posicao + n)

    def u32(self) -> int:
        return struct.unpack("<I", self._bytes(4))[0]

    def u64(self) -> int:
        return struct.unpack("<Q", self._bytes(8))[0]

    def numero(self, fmt: str) -> int:
        return struct.unpack(fmt, self._bytes(struct.calcsize(fmt)))[0]

    def texto(self) -> str:
        n = self.u64()
        if n > GGUF_MAX_STRING:
            raise _GGUFProblem("d_gguf_bigstring")
        return self._bytes(n).decode("utf-8", "replace")

    def valor(self, tipo: int, guardar: bool = True):
        """Lê um valor. Com guardar=False só avança, sem materializar o conteúdo."""
        if tipo == GGUF_STRING:
            n = self.u64()
            if n > GGUF_MAX_STRING:
                raise _GGUFProblem("d_gguf_bigstring")
            if not guardar:
                self.saltar(n)
                return None
            return self._bytes(n).decode("utf-8", "replace")
        if tipo == GGUF_ARRAY:
            subtipo = self.u32()
            if subtipo == GGUF_ARRAY:
                raise _GGUFProblem("d_gguf_nested")
            n = self.u64()
            if n > GGUF_MAX_ARRAY:
                raise _GGUFProblem("d_gguf_bigarray", limit=GGUF_MAX_ARRAY)
            for _ in range(int(n)):
                self.valor(subtipo, guardar=False)
            return None
        if tipo not in GGUF_SCALARS:
            raise _GGUFProblem("d_gguf_type", tipo=tipo)
        fmt, tamanho = GGUF_SCALARS[tipo]
        dados = self._bytes(tamanho)
        return struct.unpack(fmt, dados)[0] if guardar else None


def read_gguf_metadata(path: Path):
    """Devolve (metadados, problema).

    `problema` é None quando a leitura terminou, ou (chave_de_traducao, valores).
    Para no fim dos pares chave/valor: os tensores ficam por ler.
    """
    metadados = {}
    tamanho = path.stat().st_size
    try:
        with open(path, "rb") as fh:
            if fh.read(4) != b"GGUF":
                return {}, ("d_gguf_magic", {})
            bruto = fh.read(4)
            if len(bruto) < 4:
                return {}, ("d_gguf_incomplete", {})
            versao = struct.unpack("<I", bruto)[0]
            if versao not in (2, 3):
                return {}, ("d_gguf_ver", {"v": versao})
            leitor = _GGUFReader(fh, tamanho)
            fmt = "<Q" if versao == 3 else "<I"
            leitor.saltar(struct.calcsize(fmt))         # tensor_count
            kv = leitor.numero(fmt)
            if kv > GGUF_MAX_KV:
                return {}, ("d_gguf_too_many", {"count": kv})
            for _ in range(int(kv)):
                chave = leitor.texto()
                tipo = leitor.u32()
                metadados[chave] = leitor.valor(tipo)
    except _GGUFProblem as ex:
        return metadados, (ex.chave, ex.kw)
    except (OSError, struct.error):
        return metadados, ("d_gguf_incomplete", {})
    return metadados, None


def _linhas_suspeitas(texto: str, limite: int = 3) -> list:
    """Linhas do template que contêm comandos ou marcas de execução."""
    linhas = []
    for linha in str(texto).splitlines():
        if TEMPLATE_MARKERS.search(linha) or any(p.search(linha) for p, _ in PAYLOAD_RULES):
            linhas.append(_texto_curto(linha, 160))
            if len(linhas) >= limite:
                break
    return linhas


def gguf_checks(path: Path) -> list:
    """Metadados e template de chat de um GGUF já validado."""
    checks = []
    metadados, problema = read_gguf_metadata(path)
    if problema:
        chave, valores = problema
        checks.append(_check("Metadados GGUF", AVISO, "chk_gguf_meta",
                             (lambda c, v: lambda lang: t(c, lang, **v))(chave, valores)))
    else:
        checks.append(_check("Metadados GGUF", OK, "chk_gguf_meta",
                             (lambda n: lambda lang: t("d_gguf_meta_ok", lang, count=n))(
                                 len(metadados))))

    template = metadados.get(GGUF_TEMPLATE_KEY)
    if not isinstance(template, str) or not template:
        checks.append(_check("Template de chat (GGUF)", OK, "chk_gguf_template",
                             lambda lang: t("d_gguf_tpl_none", lang)))
        return checks

    razoes = tuple(why for pattern, why in PAYLOAD_RULES if pattern.search(template))
    marcas = bool(TEMPLATE_MARKERS.search(template))
    fortes = [w for w in razoes if w in TEMPLATE_STRONG]
    cifrado = bool(BASE64_BLOCK.search(template))
    if marcas and (fortes or cifrado):
        estado = REPROVADO
    elif marcas or fortes or cifrado:
        estado = AVISO
    else:
        estado = OK
    tamanho, linhas = len(template), tuple(_linhas_suspeitas(template))

    def _detalhe(lang, razoes=razoes, linhas=linhas, tamanho=tamanho, estado=estado):
        if estado == OK:
            return t("d_gguf_tpl_ok", lang, count=tamanho)
        partes = [t("d_gguf_tpl_found", lang, count=tamanho)]
        if razoes:
            partes.append(t("d_gguf_tpl_reasons", lang,
                            reasons="; ".join(t(w, lang) for w in razoes)))
        partes += list(linhas)
        partes.append(t("d_gguf_tpl_note", lang))
        return "\n".join(partes)

    checks.append(_check("Template de chat (GGUF)", estado, "chk_gguf_template", _detalhe))
    return checks


# ------------------------------------------------------- orquestração

def verificar(path: Path, sha_ref, whitelist: set):
    checks = []
    size = path.stat().st_size
    checks.append(_check(
        "Ficheiro", INFO, "chk_file",
        (lambda n, s: lambda lang: t("d_file", lang, name=n, size=s))(path.name, fmt_size(size))))

    digest = sha256_of(path)
    checks.append(_check("SHA-256 calculado", INFO, "chk_sha",
                         (lambda d: lambda lang: d)(digest)))
    if sha_ref:
        if digest.lower() == sha_ref.strip().lower():
            checks.append(_check("Integridade (hash)", OK, "chk_integrity",
                                 lambda lang: t("d_integrity_ok", lang)))
        else:
            checks.append(_check("Integridade (hash)", REPROVADO, "chk_integrity",
                                 lambda lang: t("d_integrity_diff", lang)))
    else:
        checks.append(_check("Integridade (hash)", AVISO, "chk_integrity",
                             lambda lang: t("d_integrity_none", lang)))

    with open(path, "rb") as f:
        head = f.read(4)
    ext = path.suffix.lower()
    if head == b"GGUF":
        fmt = "gguf"
    elif ext in SAFETENSORS_EXT:
        fmt = "safetensors"
    elif ext in PICKLE_EXT or zipfile.is_zipfile(path) or head[:1] == b"\x80":
        fmt = "pickle"
    else:
        fmt = "desconhecido"
    checks.append(_check(
        "Formato detetado", INFO, "chk_format",
        (lambda f_: lambda lang: f_ if f_ != "desconhecido" else t("d_fmt_unknown", lang))(fmt)))

    if fmt == "pickle":
        checks += pickle_checks(path, whitelist)
    elif fmt == "safetensors":
        est, detalhe_fn = check_safetensors(path)
        checks.append(_check("Estrutura safetensors", est, "chk_safetensors", detalhe_fn))
    elif fmt == "gguf":
        est, detalhe_fn = check_gguf(path)
        checks.append(_check("Estrutura GGUF", est, "chk_gguf", detalhe_fn))
        if est == OK:
            # Só se o cabeçalho for de uma versão conhecida é que faz sentido
            # ler os metadados: noutra versão o layout pode ser diferente.
            checks += gguf_checks(path)
    else:
        checks.append(_check("Formato", AVISO, "chk_unknownfmt",
                             lambda lang: t("d_unknownfmt", lang)))
    return checks, digest


def veredicto(checks):
    estados = {c["estado"] for c in checks}
    if REPROVADO in estados:
        return "VERMELHO", "NÃO USAR", 2
    if AVISO in estados:
        return "AMARELO", "USAR SÓ DEPOIS DE REVISÃO MANUAL", 1
    return "VERDE", "APROVADO COM LIMITAÇÕES", 0


# ------------------------------------------------------------- relatório

CSS_CLASS = {OK: "ok", AVISO: "aviso", REPROVADO: "erro", INFO: "info"}
COR = {"VERDE": "#2e7d32", "AMARELO": "#b28704", "VERMELHO": "#c62828"}
# O estado interno ("ATENÇÃO") não é igual à chave de tradução ("AVISO").
STATE_KEY = {OK: "state_OK", AVISO: "state_AVISO", REPROVADO: "state_REPROVADO", INFO: "state_INFO"}


def gerar_relatorio(path: Path, digest: str, label: str, acao: str, checks: list,
                    lang: str = "pt") -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = REPORT_DIR / f"relatorio_{path.stem}_{stamp}.html"
    e = html.escape
    if label == "VERMELHO":
        itens = "".join(f"<li>{e(t(f'reco_{i}', lang))}</li>" for i in range(1, 6))
        reco = f"<div class='reco'><strong>{e(t('rep_todo', lang))}</strong><ol>{itens}</ol></div>"
    else:
        reco = ""
    linhas = []
    for c in checks:
        nome, detalhe = texto_check(c, lang)
        linhas.append(f"<tr><td>{e(nome)}</td>"
                      f"<td class='{CSS_CLASS[c['estado']]}'>{e(t(STATE_KEY[c['estado']], lang))}</td>"
                      f"<td><pre>{e(detalhe)}</pre></td></tr>")
    doc = f"""<!doctype html>
<html lang="{HTML_LANG.get(lang, 'pt-PT')}"><head><meta charset="utf-8">
<title>ALF_picklescan - {e(path.name)}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 980px; margin: 2rem auto; padding: 0 1rem; color: #222; }}
.veredicto {{ color: #fff; background: {COR[label]}; padding: 1rem 1.2rem; border-radius: 8px; font-size: 1.2rem; }}
.limites {{ background: #f4f4f4; padding: .8rem 1rem; border-radius: 8px; margin-top: 1rem; font-size: .92rem; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
td, th {{ border: 1px solid #ddd; padding: .5rem; vertical-align: top; text-align: left; }}
pre {{ white-space: pre-wrap; word-break: break-all; margin: 0; font-size: .85rem; }}
.ok {{ color: #2e7d32; font-weight: bold; }} .aviso {{ color: #b28704; font-weight: bold; }}
.erro {{ color: #c62828; font-weight: bold; }} .info {{ color: #555; }}
.reco {{ border: 2px solid {COR.get(label, '#c62828')}; padding: .8rem 1.2rem; border-radius: 8px; margin-top: 1rem; }}
.reco li {{ margin: .35rem 0; }}
</style></head><body>
<h1>{e(t('rep_title', lang))}</h1>
<p><strong>{e(t('rep_file', lang))}</strong> {e(path.name)}<br>
<strong>{e(t('rep_date', lang))}</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
<strong>SHA-256:</strong> <code>{e(digest)}</code></p>
<div class="veredicto">{e(t('verdict_' + label, lang))} - {e(t('action_' + label, lang))}</div>
{reco}
<div class="limites"><strong>{e(t('rep_limitations', lang))}</strong> {e(t('limitations', lang))}</div>
<table><tr><th>{e(t('rep_check', lang))}</th><th>{e(t('rep_state', lang))}</th><th>{e(t('rep_detail', lang))}</th></tr>{"".join(linhas)}</table>
<p style="color:#777;font-size:.8rem">ALF_picklescan v{VERSION}</p>
</body></html>"""
    out.write_text(doc, encoding="utf-8")
    return out


# --------------------------------------------------------------- consola

def mostrar(checks, label, acao, report, lang: str = "pt"):
    print()
    for c in checks:
        nome, detalhe = texto_check(c, lang)
        etiqueta = f"[{t(STATE_KEY[c['estado']], lang)}]"
        print(f"{etiqueta:<10} {nome}")
        for linha in detalhe.splitlines()[:6]:
            print(f"            {linha}")
    print()
    print("=" * 60)
    print(f" {t('verdict_' + label, lang)} - {t('action_' + label, lang)}")
    print("=" * 60)
    print(f" {report}")
    print()
    if label == "VERMELHO":
        print(t("rep_todo", lang).upper())
        for i in range(1, 6):
            print(f" {i}. {t(f'reco_{i}', lang)}")
        print()
    print(t("limitations", lang))


def pedir_entrada(lang: str = "pt"):
    print(f"ALF_picklescan v{VERSION}")
    print("-" * 40)
    ficheiro = input(t("cli_path", lang)).strip().strip('"').strip("'")
    sha = input(t("cli_sha", lang)).strip() or None
    return ficheiro, sha


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Verifica modelos de IA antes de os usar.")
    ap.add_argument("ficheiro", nargs="?", help="Caminho do modelo (.bin, .pt, .safetensors, .gguf, ...)")
    ap.add_argument("--sha256", default=None, help="SHA-256 publicado pelo autor do modelo")
    ap.add_argument("--lang", default="pt", choices=[code for code, _ in STRINGS.items()] or ["pt"],
                    help="Idioma do relatório (en, pt, fr, es, it, zh)")
    args = ap.parse_args()

    interativo = args.ficheiro is None
    if interativo:
        ficheiro, sha = pedir_entrada(args.lang)
    else:
        ficheiro, sha = args.ficheiro, args.sha256

    path = Path(ficheiro).expanduser()
    if not path.is_file():
        print(t("cli_notfound", args.lang, path=path))
        return 3

    print("\n" + t("cli_analysing", args.lang))
    try:
        whitelist = load_whitelist()
        checks, digest = verificar(path, sha, whitelist)
    except Exception as ex:
        print(t("cli_unexpected", args.lang, error=ex))
        return 3

    label, acao, code = veredicto(checks)
    report = gerar_relatorio(path, digest, label, acao, checks, args.lang)
    mostrar(checks, label, acao, report, args.lang)

    if interativo and sys.stdin.isatty():
        input("\n" + t("cli_close", args.lang))
    return code


if __name__ == "__main__":
    sys.exit(main())
