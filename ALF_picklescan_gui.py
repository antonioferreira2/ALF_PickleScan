#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALF_picklescan - interface gráfica v2.2 (multilingue)
Usa a lógica de verificação de ALF_picklescan.py e as traduções de i18n.py.
"""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import ALF_picklescan as core
from i18n import DEFAULT_LANG, LANGUAGES, t

BG = "#f4f5f7"
NAVY = "#1f2a44"
MUTED = "#5b6474"
NEUTRAL = "#8a93a3"

VERDICT_COLORS = {"VERDE": "#2e7d32", "AMARELO": "#b28704", "VERMELHO": "#c62828"}
TAG_FOR_STATE = {core.OK: "ok", core.AVISO: "aviso", core.REPROVADO: "erro", core.INFO: "info"}
STATE_KEY = {
    core.OK: "state_OK",
    core.AVISO: "state_AVISO",
    core.REPROVADO: "state_REPROVADO",
    core.INFO: "state_INFO",
}


def font(lang, size, bold=False):
    if sys.platform == "win32":
        family = "Microsoft YaHei UI" if lang == "zh" else "Segoe UI"
    else:
        family = "Noto Sans CJK SC" if lang == "zh" else "DejaVu Sans"
    return (family, size, "bold") if bold else (family, size)


def mono_font(size=9):
    family = "Consolas" if sys.platform == "win32" else "DejaVu Sans Mono"
    return (family, size)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = DEFAULT_LANG
        self.geometry("820x760")
        self.minsize(720, 640)
        self.configure(bg=BG)
        try:
            ttk.Style(self).theme_use("vista")
        except tk.TclError:
            pass

        # Variáveis que sobrevivem à reconstrução da janela ao mudar de idioma
        self.path_var = tk.StringVar()
        self.hash_var = tk.StringVar()
        self.queue = queue.Queue()
        self.result = None
        self.report_path = None
        self.busy = False

        self._build()

    # ----------------------------------------------------------- utilitários

    def T(self, key):
        return t(key, self.lang)

    def F(self, size, bold=False):
        return font(self.lang, size, bold)

    # ------------------------------------------------------------- layout

    def _build(self):
        for w in self.winfo_children():
            w.destroy()
        self.title(f"ALF_picklescan {core.VERSION}")

        header = tk.Frame(self, bg=NAVY, padx=24, pady=14)
        header.pack(fill="x")

        self.lang_box = ttk.Combobox(header, state="disabled" if self.busy else "readonly",
                                     width=16, values=[name for _, name in LANGUAGES])
        self.lang_box.current([code for code, _ in LANGUAGES].index(self.lang))
        self.lang_box.bind("<<ComboboxSelected>>", self.on_language)
        self.lang_box.pack(side="right")
        tk.Label(header, text=self.T("language") + ":", font=self.F(9), fg="#c9d2e3",
                 bg=NAVY).pack(side="right", padx=(0, 6))

        title_box = tk.Frame(header, bg=NAVY)
        title_box.pack(side="left", fill="x")
        tk.Label(title_box, text="ALF_picklescan", font=self.F(17, True), fg="white",
                 bg=NAVY).pack(anchor="w")
        tk.Label(title_box, text=self.T("subtitle"), font=self.F(10), fg="#c9d2e3",
                 bg=NAVY).pack(anchor="w")

        body = tk.Frame(self, bg=BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # 1. Ficheiro
        self._section_title(body, self.T("section_model"))
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(4, 14))
        ttk.Entry(row, textvariable=self.path_var).pack(side="left", fill="x", expand=True)
        self.pick_btn = ttk.Button(row, text=self.T("choose_file"), command=self.pick_file,
                                   state="disabled" if self.busy else "normal")
        self.pick_btn.pack(side="left", padx=(8, 0))

        # 2. Hash
        self._section_title(body, self.T("section_hash"))
        ttk.Entry(body, textvariable=self.hash_var).pack(fill="x", pady=(4, 2))
        tk.Label(body, text=self.T("hash_hint"), font=self.F(9), fg=MUTED,
                 bg=BG, wraplength=740, justify="left").pack(anchor="w", pady=(0, 12))

        # Ações
        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x", pady=(0, 10))
        self.verify_btn = ttk.Button(actions, text=self.T("verify"), command=self.start,
                                     state="disabled" if self.busy else "normal")
        self.verify_btn.pack(side="left")
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=220)
        self.progress.pack(side="left", padx=12)
        self.status = tk.Label(actions, text=self.T("analyzing") if self.busy else "",
                               font=self.F(9), fg=MUTED, bg=BG)
        self.status.pack(side="left")
        if self.busy:
            self.progress.start(12)

        # Resultado
        self.result_frame = tk.Frame(body, bg=NEUTRAL, padx=18, pady=14)
        self.result_frame.pack(fill="x", pady=(6, 0))
        self.verdict_lbl = tk.Label(self.result_frame, text=self.T("verdict_none"),
                                    font=self.F(16, True), fg="white", bg=NEUTRAL)
        self.verdict_lbl.pack(anchor="w")
        self.action_lbl = tk.Label(self.result_frame, text="", font=self.F(10),
                                   fg="white", bg=NEUTRAL)
        self.action_lbl.pack(anchor="w")
        self.integrity_lbl = tk.Label(self.result_frame, text="", font=self.F(10, True),
                                      fg="white", bg=NEUTRAL)
        self.integrity_lbl.pack(anchor="w", pady=(6, 0))

        # Detalhes
        self._section_title(body, self.T("details")).pack_configure(pady=(14, 4))
        text_frame = tk.Frame(body, bg=BG)
        text_frame.pack(fill="both", expand=True)
        self.out = tk.Text(text_frame, wrap="word", height=12, font=mono_font(9),
                           bg="white", relief="flat", padx=10, pady=8, borderwidth=1,
                           highlightthickness=1, highlightbackground="#d0d4db")
        scroll = ttk.Scrollbar(text_frame, command=self.out.yview)
        self.out.configure(yscrollcommand=scroll.set, state="disabled")
        self.out.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        bold_mono = mono_font(9)
        self.out.tag_config("ok", foreground="#2e7d32", font=(bold_mono[0], 9, "bold"))
        self.out.tag_config("aviso", foreground="#b28704", font=(bold_mono[0], 9, "bold"))
        self.out.tag_config("erro", foreground="#c62828", font=(bold_mono[0], 9, "bold"))
        self.out.tag_config("info", foreground="#5b6474", font=(bold_mono[0], 9, "bold"))
        self.out.tag_config("detalhe", foreground="#333333", lmargin1=24, lmargin2=24)

        # Rodapé
        footer = tk.Frame(body, bg=BG)
        footer.pack(fill="x", pady=(14, 0))
        self.open_report_btn = ttk.Button(footer, text=self.T("open_report"),
                                          command=self.open_report, state="disabled")
        self.open_report_btn.pack(side="left")
        ttk.Button(footer, text=self.T("reports_folder"),
                   command=self.open_reports_folder).pack(side="left", padx=8)
        tk.Label(body, text=self.T("disclaimer"), wraplength=740, justify="left",
                 font=self.F(8), fg=MUTED, bg=BG).pack(anchor="w", pady=(10, 0))

        if self.result is not None:
            self._render_result(self.result)

    def _section_title(self, parent, text):
        lbl = tk.Label(parent, text=text, font=self.F(10, True), fg=NAVY, bg=BG)
        lbl.pack(anchor="w")
        return lbl

    # ------------------------------------------------------------- ações

    def on_language(self, _event=None):
        if self.busy:
            self.lang_box.current([code for code, _ in LANGUAGES].index(self.lang))
            return
        self.lang = LANGUAGES[self.lang_box.current()][0]
        self._build()

    def pick_file(self):
        path = filedialog.askopenfilename(
            title=self.T("choose_file"),
            filetypes=[(self.T("filetypes"), "*.gguf *.safetensors *.bin *.pt *.pth *.pkl"),
                       (self.T("all_files"), "*.*")],
        )
        if path:
            self.path_var.set(path)

    def start(self):
        raw = self.path_var.get().strip().strip('"')
        if not raw or not Path(raw).is_file():
            messagebox.showwarning(self.T("missing_model_title"), self.T("missing_model"))
            return
        sha = self.hash_var.get().strip() or None
        self._set_busy(True)
        threading.Thread(target=self._worker, args=(Path(raw), sha, self.lang),
                         daemon=True).start()
        self.after(100, self._poll)

    def _worker(self, path, sha, lang):
        try:
            whitelist = core.load_whitelist()
            checks, digest = core.verificar(path, sha, whitelist)
            label, acao, _code = core.veredicto(checks)
            report = core.gerar_relatorio(path, digest, label, acao, checks, lang)
            self.queue.put(("ok", dict(path=path, sha=sha, checks=checks, label=label,
                                       acao=acao, report=report)))
        except Exception as ex:
            self.queue.put(("erro", str(ex)))

    def _poll(self):
        try:
            kind, data = self.queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll)
            return
        self._set_busy(False)
        if kind == "erro":
            messagebox.showerror(self.T("error_title"), data)
        else:
            self.result = data
            self._render_result(data)

    def _set_busy(self, busy):
        self.busy = busy
        if busy:
            self.verify_btn.configure(state="disabled")
            self.pick_btn.configure(state="disabled")
            self.lang_box.configure(state="disabled")
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
            self.status.configure(text=self.T("analyzing"))
        else:
            self.verify_btn.configure(state="normal")
            self.pick_btn.configure(state="normal")
            self.lang_box.configure(state="readonly")
            self.progress.stop()
            # Em modo indeterminado a barra fica desenhada a meio depois de parar;
            # voltar a determinista com valor 0 limpa-a.
            self.progress.configure(mode="determinate", value=0, maximum=1)
            self.status.configure(text="")

    def _render_result(self, data):
        checks, label = data["checks"], data["label"]
        self.report_path = data["report"]
        self._paint(VERDICT_COLORS[label])
        self.verdict_lbl.configure(text=self.T(f"verdict_{label}"))
        self.action_lbl.configure(text=self.T(f"action_{label}"))

        integrity = next((c for c in checks if c["nome"] == "Integridade (hash)"), None)
        if integrity is None or data["sha"] is None:
            msg = self.T("integrity_no_hash")
        elif integrity["estado"] == core.OK:
            msg = self.T("integrity_ok")
        else:
            msg = self.T("integrity_diff")
        self.integrity_lbl.configure(text=msg)

        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        for c in checks:
            nome, detalhe = core.texto_check(c, self.lang)
            tag_label = self.T(STATE_KEY[c["estado"]])
            self.out.insert("end", f"[{tag_label}]".ljust(14), TAG_FOR_STATE[c["estado"]])
            self.out.insert("end", f"{nome}\n")
            for linha in detalhe.splitlines()[:12]:
                self.out.insert("end", f"{linha}\n", "detalhe")
        self.out.configure(state="disabled")
        self.open_report_btn.configure(state="normal")

    def _paint(self, color):
        for w in (self.result_frame, self.verdict_lbl, self.action_lbl, self.integrity_lbl):
            w.configure(bg=color)

    def open_report(self):
        if self.report_path and Path(self.report_path).exists():
            self._open(self.report_path)

    def open_reports_folder(self):
        core.REPORT_DIR.mkdir(exist_ok=True)
        self._open(core.REPORT_DIR)

    @staticmethod
    def _open(path):
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as ex:
            messagebox.showerror("ALF_picklescan", str(ex))


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
