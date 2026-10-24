# ALF_picklescan

**Verificatore gratuito e open source di file di modelli di IA.** Prima di caricare un modello che hai scaricato, controlla l'integrità, la struttura e se nasconde codice pericoloso. Funziona con file **GGUF**, **safetensors** e **pickle/PyTorch** (`.bin`, `.pt`, `.pth`, `.pkl`). Windows e Linux. Nessuna installazione, nessuna conoscenza di programmazione necessaria.

> ⚠️ **Questo strumento non garantisce che il modello sia sicuro.** Esegue solo test sul file: integrità (SHA-256), struttura e import nei file pickle. Non analizza il comportamento del modello, e un modello addestrato per un trigger nascosto può superare tutti i test. È un primo filtro, mai una garanzia di sicurezza. Vedi le [Limitazioni](#limitazioni).

Disponibile in: [English](README.md) · [Português (PT)](README.pt-PT.md) · [Français](README.fr.md) · [Español](README.es.md) · **Italiano** · [中文](README.zh.md) — l'interfaccia dell'applicazione è disponibile in tutte e sei le lingue.

![ALF_picklescan che verifica un file di modello con risultato verde](screenshots/gui-en.png)

---

## Perché esiste questo progetto

Chiunque può pubblicare un modello su una piattaforma pubblica, e chiunque può scaricarlo. I file dei modelli non sono dati inerti: un **pickle** (usato dalla maggior parte dei checkpoint PyTorch, `.bin`, `.pt`, `.pth`) può eseguire codice nel momento in cui lo carichi. Un file corretto al momento della pubblicazione può essere sostituito in seguito, e un download può arrivare corrotto o manomesso.

Chi esegue modelli in locale non ha, in pratica, modo di rispondere a una domanda semplice: *questo file è quello pubblicato dall'autore e contiene qualcosa di chiaramente ostile?* Installa il modello e spera che vada bene.

Gli scanner privati e le piattaforme a pagamento rispondono a questa domanda per le aziende. Questo progetto risponde per tutti gli altri: studenti, ricercatori, piccoli team, curiosi con un portatile. **La sicurezza di base non dovrebbe essere un servizio a pagamento.** ALF_picklescan è gratuito, con licenza MIT, senza account, senza telemetria, senza server e senza limiti. È fatto per essere copiato, migliorato e regalato di nuovo.

L'autore non vende nulla, non raccoglie dati e non chiede donazioni. L'obiettivo è che più persone controllino ciò che scaricano, e che meno macchine vengano compromesse da un file che nessuno ha guardato.

## Cosa fa

- Calcola lo **SHA-256** del file e lo confronta con l'hash pubblicato dall'autore del modello.
- Valida la **struttura** dei file GGUF, safetensors e ZIP di PyTorch — compresi i metadati GGUF e il loro **template di chat**, che il motore di inferenza renderizza, e se ogni tensore safetensors ha davvero la dimensione richiesta da forma e dtype.
- Legge gli **import** dei file pickle **senza eseguirli** (con la stessa tecnica di [picklescan](https://github.com/mmaitre314/picklescan)) e segnala funzioni pericolose note, come `os.system`, `subprocess`, `eval` o `exec`.
- Mostra **cosa eseguirebbe la chiamata sospetta**: il comando, l'URL o il blocco codificato contenuto nel pickle, presentato come prova, insieme a pattern di shell, download, furto di credenziali, persistenza e offuscamento. Nulla viene eseguito.
- Segnala **file eseguibili** nascosti dentro un pacchetto di modello.
- Mostra un **semaforo** e crea un **report HTML** che puoi conservare o condividere.
- Mostra il **nome e il dettaglio di ogni controllo nella lingua scelta** (inglese, portoghese, francese, spagnolo, italiano o cinese), rapporto compreso.

L'analisi è di sola lettura. Lo strumento non carica, importa né esegue mai il modello.

## Download

Vai alla pagina [**Releases**](https://github.com/antonioferreira2/ALF_PickleScan/releases) e scegli il file per il tuo sistema. Le versioni Windows e Linux sono pubblicate separatamente.

| Sistema | File | Requisiti |
|---|---|---|
| **Windows 10 / 11** (64 bit) | `ALF_picklescan-windows-x64.exe` | Nessuno. Doppio clic. Compilato con Python 3.11 su Windows Server 2022. |
| **Linux** (x86-64) | `ALF_picklescan-linux-x86_64` | glibc **2.35** o successiva — Ubuntu 22.04+, Debian 12+, Fedora 36+, Linux Mint 21+. Compilato su Ubuntu 22.04. |

Ogni file ha un `.sha256` accanto. **Verificalo prima di eseguire il file.**

**Windows** (Prompt dei comandi o PowerShell):
```
certutil -hashfile ALF_picklescan-windows-x64.exe SHA256
```

**Linux:**
```
sha256sum -c ALF_picklescan-linux-x86_64.sha256
chmod +x ALF_picklescan-linux-x86_64
./ALF_picklescan-linux-x86_64
```

### Verificare l'origine dell'eseguibile

Ogni nuova release include anche un'**attestazione di build** di GitHub (*Artifact Attestations*), che collega il file al workflow che lo ha compilato e al commit esatto. Con il [GitHub CLI](https://cli.github.com/) installato:

```
gh attestation verify ALF_picklescan-windows-x64.exe --repo antonioferreira2/ALF_PickleScan
gh attestation verify ALF_picklescan-linux-x86_64 --repo antonioferreira2/ALF_PickleScan
```

Un'attestazione valida dimostra **chi ha compilato** il file e da quale codice — non che il codice sia sicuro. La release v2.1.0 è precedente e ha solo il `.sha256`.

Se Windows SmartScreen dice che l'app non è riconosciuta, clicca **Ulteriori informazioni → Esegui comunque**. Quell'avviso appare perché l'eseguibile non è firmato digitalmente; un certificato di firma costa denaro ogni anno e questo progetto è gratuito. Verifica sempre l'hash e confrontalo con quello pubblicato nella pagina della release.

Altre piattaforme: il codice sorgente funziona ovunque siano disponibili Python e Tk (macOS incluso). Vedi [CONTRIBUTING.md](CONTRIBUTING.md) per eseguirlo dai sorgenti.

## Come si usa

1. Apri l'applicazione e scegli la lingua nell'angolo in alto a destra.
2. Clicca **Choose file** (Scegli file) e seleziona il modello.
3. Incolla lo **SHA-256 pubblicato dall'autore** (fortemente consigliato — cercalo nella pagina ufficiale del modello).
4. Clicca **Verify model** (Verifica modello).
5. Leggi il risultato. Clicca **Open report** (Apri rapporto) per tutti i dettagli.

Il rapporto viene salvato accanto al programma, in `ALF_relatorios/`.

Riga di comando (Linux o Windows, con Python installato):

```
python ALF_picklescan.py model.gguf --sha256 <hash>
```

I codici di uscita facilitano l'uso in script e pipeline CI: `0` verde, `1` giallo, `2` rosso, `3` errore.

## Risultati

| Colore | Significato | Cosa fare |
|---|---|---|
| 🟢 **VERDE** — approvato con limitazioni | Hash confermato, nessun avviso | Puoi usarlo, rispettando le limitazioni |
| 🟡 **GIALLO** — revisione manuale | Nessun hash di riferimento, import fuori dalla lista bianca, testo sospetto o analisi incompleta | Esamina i dettagli prima di usarlo |
| 🔴 **ROSSO** — non usare | Hash diverso, malware rilevato, import pericolosi o struttura non valida | Non usare questo file |

Un risultato verde non viene **mai** mostrato senza un hash di riferimento confermato.

![ALF_picklescan con risultato rosso, che mostra il comando di download ed esecuzione trovato nel file](screenshots/gui-red.png)

Un file può superare il controllo dell'hash e restare ostile. Qui l'hash è confermato e il risultato è rosso, perché il file contiene un comando di download ed esecuzione. Il campione è stato generato per questa cattura: si limita a *referenziare* la funzione, senza mai eseguirla.
## Limitazioni

- **Non è una garanzia di sicurezza.** Un modello malevolo addestrato a comportarsi male solo con un trigger specifico può superare tutti i test.
- **Nessuna analisi del comportamento.** Lo strumento controlla il file, non ciò che fa il modello quando viene eseguito.
- **L'analisi dei pickle usa un elenco di funzioni pericolose note.** Un payload nuovo, fuori dall'elenco, può passare. Le chiamate senza import identificabili sono segnate in giallo per questo motivo.
- **Fidarsi dell'hash.** L'hash dimostra che il file corrisponde a ciò che è stato pubblicato, non che chi lo ha pubblicato sia affidabile.
- **GGUF e safetensors sono validati solo strutturalmente.** Questo conferma che il file è ben formato, non che i pesi siano buoni o onesti.

Per i modelli usati con strumenti o con accesso ai dati (agenti, assistenti locali con accesso ai file), **eseguili isolati**: un container o una macchina virtuale senza rete e senza credenziali.

## Lista bianca degli import

Al primo avvio l'applicazione crea `ALF_whitelist.txt` accanto al programma. Contiene gli import considerati normali nei checkpoint PyTorch e NumPy. Se un modello legittimo viene segnato in giallo solo per un import normale, puoi aggiungerlo dopo aver verificato che sia previsto per quel modello. I contributi che migliorano la lista predefinita per altre architetture sono molto benvenuti.

Se la cartella è di sola lettura, l'applicazione usa la lista incorporata e non si blocca.

## Cosa contiene questo repository

Qui è pubblicato solo il necessario per usare, compilare e migliorare lo strumento:

| Percorso | A cosa serve |
|---|---|
| `ALF_picklescan.py` | Motore di verifica e interfaccia a riga di comando |
| `ALF_picklescan_gui.py` | Interfaccia grafica (Tk) |
| `i18n.py` | Traduzioni dell'interfaccia (EN, PT, FR, ES, IT, ZH) |
| `requirements.txt` | Versione fissata di picklescan, l'unica dipendenza esterna |
| `build_exe.bat`, `build_linux.sh` | Compilazioni riproducibili per Windows e Linux |
| `tests/test_smoke.py` | Test automatici con campioni innocui generati al momento |
| `screenshots/` | Immagini usate nella documentazione |
| `README*.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` | Documentazione e licenza |
| `.github/workflows/` | Test automatici e build della release per entrambe le piattaforme |

**Non** sono nel repository, di proposito:

- gli **eseguibili** — sono nelle [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases), così un clone nuovo resta leggero e la cronologia non si riempie di binari;
- i risultati di compilazione (`build/`, `dist/`, `*.spec`), i rapporti generati (`ALF_relatorios/`) e il file locale `ALF_whitelist.txt`;
- **file di modelli** di qualsiasi tipo, e qualsiasi campione di test che potrebbe essere usato per attaccare qualcuno;
- i documenti interni di pianificazione del lancio.

Per compilare dai sorgenti, esegui `build_exe.bat` su Windows o `./build_linux.sh` su Linux. Entrambi richiedono Python 3.11 o successivo e producono un eseguibile unico che include già picklescan.

## Roadmap

Piano pubblico. Gli elementi possono cambiare; i progressi sono nelle [Issues](https://github.com/antonioferreira2/ALF_PickleScan/issues) e nelle [Discussions](https://github.com/antonioferreira2/ALF_PickleScan/discussions).

1. **v2.1: interfaccia multilingue e build Linux.** ✅ Inglese, portoghese, francese, spagnolo, italiano e cinese nell'app; build per Windows e Linux; picklescan incluso negli eseguibili.
2. **v2.2: prova del payload.** ✅ Quando viene referenziata una funzione pericolosa, il rapporto mostra gli argomenti che riceverebbe — il comando, l'URL, il blocco codificato — e segnala pattern di shell, download, furto di credenziali, persistenza e offuscamento.
3. **v2.3: messaggi di verifica tradotti.** ✅ Nomi, dettagli e rapporto seguono la lingua scelta, in tutte e sei le lingue.
4. **v3.0: più formati e automazione.** Supporto per ONNX, esportazione dei rapporti in JSON e modalità di output per pipeline CI.

## Contribuire

Sei nuovo? Inizia da una **`good first issue`**: attività piccole e ben descritte per le prime contribuzioni.

- Traduci i messaggi di verifica del motore (`ALF_picklescan.py`) così che i rapporti si possano leggere in altre lingue.
- Migliora la lista bianca degli import per le architetture più diffuse (Llama, Mistral, Qwen, ecc.), con esempi verificati.
- Aggiungi test automatici con file di esempio innocui.
- Rileggi una delle traduzioni del README se sei madrelingua.

Per segnalare un falso positivo, apri una issue con il link pubblico del modello, la versione usata e il controllo segnalato. Non inviare file di modelli privati. Per il processo completo, vedi [CONTRIBUTING.md](CONTRIBUTING.md).

## Sicurezza

Per segnalare una vulnerabilità, segui [SECURITY.md](SECURITY.md). Non aprire una issue pubblica per problemi di sicurezza.

## Autore

Creato da **António Ferreira** (ALF), per aiutare la comunità a usare i modelli di IA con un po' più di sicurezza. Non è una verifica dei fatti su alcun modello e non certifica nulla: è solo un test di base, e può sbagliare.

Miglioramenti, fork e strumenti migliori sono benvenuti. Se puoi fare qualcosa di meglio per la società, fallo.

## Licenza

MIT. Vedi [LICENSE](LICENSE). Anche picklescan è con licenza MIT.
