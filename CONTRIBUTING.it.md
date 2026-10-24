# Contribuire

Grazie per voler aiutare. Questo progetto esiste per rendere la verifica dei file di modelli di IA accessibile a chiunque, perciò teniamo alla chiarezza, alla semplicità e all'onestà su ciò che lo strumento fa e non fa.

Disponibile in: [English](CONTRIBUTING.md) · [Português (PT)](CONTRIBUTING.pt-PT.md) · [Français](CONTRIBUTING.fr.md) · [Español](CONTRIBUTING.es.md) · **Italiano** · [中文](CONTRIBUTING.zh.md)

> ⚠️ **Questo strumento non garantisce che il modello sia sicuro.** Nessun contributo può indebolire o nascondere questo avviso: resta nell'interfaccia, nei rapporti e nella documentazione, in tutte le lingue.

## Prima di iniziare

- **`good first issue`**: attività piccole, con abbastanza contesto per iniziare. **`help wanted`** segnala quelle più grandi.
- Apri una issue o una discussione prima di iniziare qualcosa di grosso, così l'approccio si concorda prima.

## Eseguire il progetto dai sorgenti

```text
git clone https://github.com/antonioferreira2/ALF_PickleScan.git
cd ALF_PickleScan
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ALF_picklescan_gui.py
```

Serve Python **3.11 o successivo** per compilare gli eseguibili; i test girano su 3.11 e 3.12, su Windows e Linux. Su Linux l'interfaccia richiede `python3-tk` (`sudo apt install python3-tk`).

`requirements.txt` è l'unico posto in cui è scritta la versione di picklescan: i workflow e gli script di build la leggono da lì, quindi modificala lì e in nessun altro posto.

Per aprire l'interfaccia con un modello già caricato — lo stesso che trascinare un file sull'eseguibile:

```text
python ALF_picklescan_gui.py modello.gguf
```

## Controlli prima di aprire una pull request

```text
python -m py_compile ALF_picklescan.py ALF_picklescan_gui.py i18n.py
python -m unittest discover -s tests -v
```

I test generano i propri campioni innocui in cartelle temporanee, non richiedono rete e non eseguono mai ciò che ispezionano. GitHub li esegue anche su Windows e Linux a ogni push e pull request (`.github/workflows/tests.yml`).

## Cosa è benvenuto

- **Falsi positivi e falsi negativi.** Apri una issue con il link pubblico del modello, la versione usata e il controllo segnalato.
- **Test con file di esempio innocui** che riproducono un errore o coprono una nuova rilevazione.
- **Traduzioni**, inclusa la revisione da parte di un madrelingua dei README e di questa guida.
- **Miglioramenti alla whitelist** per le architetture diffuse (Llama, Mistral, Qwen, …), sempre con la fonte che giustifica l'import.
- **Documentazione**: correzioni e chiarimenti.

## Cosa non inviare

- **File realmente malevoli**, nemmeno come test. Un test può solo *referenziare* una funzione pericolosa, mai chiamarla.
- **Pesi di modelli** privati, o di terzi senza autorizzazione a condividerli.
- **Eseguibili**: il loro posto è nelle [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases).
- **File generati**: `ALF_relatorios/`, `build/`, `dist/`, `*.spec` e il `ALF_whitelist.txt` locale.

## Sicurezza

Le vulnerabilità passano dalla **segnalazione privata di vulnerabilità** di GitHub: scheda **Security** del repository, poi **Report a vulnerability**. Mai una issue pubblica. Vedi [SECURITY.md](SECURITY.md).

Un modello legittimo segnalato come pericoloso, o un modello ostile che ha superato tutti i test, non è una vulnerabilità: è una issue normale, con il dettaglio del controllo.

## Contributi assistiti dall'IA

- Parte del codice e della documentazione di questo progetto è stata scritta con l'aiuto di strumenti di IA, incluso l'agente Codebuff. Il manutentore rivede ogni modifica prima che arrivi su `main`, e la cronologia di Git conserva la paternità di ogni commit.
- **Sei responsabile di ciò che invii.** Se usi l'IA per scrivere codice, comprendilo e saprai spiegarlo.
- **Le modifiche non testate non sono accettate.** Esegui i comandi qui sopra e indica nella pull request cosa hai eseguito.
- Le pull request che sembrano generate senza revisione possono essere rifiutate: codice che ignora lo stile del progetto, test che non verificano nulla, commenti generici che non corrispondono al codice.
- Gli aggiornamenti di **Dependabot** passano dalla stessa revisione. Nulla entra in `main` senza i test verdi.

## Revisione e merge

- Il manutentore rivede le pull request. Non c'è una scadenza garantita.
- Le modifiche alla logica di verifica (livelli di analisi, verdetti, parser GGUF e safetensors) richiedono test nuovi e una spiegazione nella pull request.
- Le modifiche che rendono la verifica **meno rigorosa** sono le più esaminate: nel dubbio, il verdetto deve essere giallo, non verde.
- Una pull request per argomento, con il problema e la soluzione in una o due frasi.

## Regole di codice

1. **Non caricare mai un modello malevolo per testare.** Crea un pickle che solo *referenzia* una funzione pericolosa, come già fanno i test.
2. **Non rimuovere gli avvisi sui limiti.** Lo strumento non garantisce sicurezza e la documentazione deve continuare a dirlo.
3. Il testo mostrato all'utente vive in `i18n.py`, nelle sei lingue (`en`, `pt`, `fr`, `es`, `it`, `zh`). Una chiave mancante ricade sull'inglese, ma i test verificano che nessuna lingua resti incompleta.
4. Le modifiche alla whitelist devono arrivare con la fonte dell'import (il modello o la sua documentazione).
5. Preferisci la libreria standard di Python a dipendenze nuove. picklescan è l'unica esterna.
6. Mantieni il codice semplice e leggibile: funzioni brevi, lo stile `_check()` e `veredicto()` già usato nel progetto.
7. Se tocchi l'interfaccia o il motore, prova almeno in inglese, portoghese e cinese: tre alfabeti diversi (latino, latino con accenti e CJK).

## Codice di condotta

Sii rispettoso. Critica le idee, non le persone. Le domande di chi arriva ora sono benvenute e meritano risposta.
