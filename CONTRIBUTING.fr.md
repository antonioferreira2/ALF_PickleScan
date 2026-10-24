# Contribuer

Merci de vouloir aider. Ce projet existe pour rendre la vérification des fichiers de modèles d'IA accessible à tous, c'est pourquoi nous tenons à la clarté, à la simplicité et à l'honnêteté sur ce que l'outil fait — et ne fait pas.

Disponible en : [English](CONTRIBUTING.md) · [Português (PT)](CONTRIBUTING.pt-PT.md) · **Français** · [Español](CONTRIBUTING.es.md) · [Italiano](CONTRIBUTING.it.md) · [中文](CONTRIBUTING.zh.md)

> ⚠️ **Cet outil ne garantit pas que le modèle est sûr.** Aucune contribution ne peut affaiblir ou masquer cet avertissement : il reste dans l'interface, dans les rapports et dans la documentation, dans toutes les langues.

## Avant de commencer

- **`good first issue`** : tâches courtes, avec assez de contexte pour démarrer. **`help wanted`** signale les plus importantes.
- Ouvrez une issue ou une discussion avant d'entamer quelque chose de gros, pour que l'approche soit validée d'abord.

## Exécuter le projet depuis les sources

```text
git clone https://github.com/antonioferreira2/ALF_PickleScan.git
cd ALF_PickleScan
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python ALF_picklescan_gui.py
```

Python **3.11 ou plus récent** est nécessaire pour compiler les exécutables ; les tests tournent sur 3.11 et 3.12, sous Windows et Linux. Sous Linux, l'interface a besoin de `python3-tk` (`sudo apt install python3-tk`).

`requirements.txt` est le seul endroit où la version de picklescan est écrite : les workflows et les scripts de compilation la lisent là, donc modifiez-la à cet endroit et nulle part ailleurs.

Pour ouvrir l'interface avec un modèle déjà chargé — l'équivalent de glisser un fichier sur l'exécutable :

```text
python ALF_picklescan_gui.py modele.gguf
```

## Vérifications avant d'ouvrir une pull request

```text
python -m py_compile ALF_picklescan.py ALF_picklescan_gui.py i18n.py
python -m unittest discover -s tests -v
```

Les tests génèrent leurs propres échantillons inoffensifs dans des dossiers temporaires, n'ont pas besoin de réseau et n'exécutent jamais ce qu'ils inspectent. GitHub les exécute aussi sous Windows et Linux à chaque push et pull request (`.github/workflows/tests.yml`).

## Ce qui est bienvenu

- **Faux positifs et faux négatifs.** Ouvrez une issue avec le lien public du modèle, la version utilisée et la vérification signalée.
- **Tests avec des fichiers d'exemple inoffensifs** qui reproduisent un bug ou couvrent une nouvelle détection.
- **Traductions**, y compris la relecture par un locuteur natif des README et de ce guide.
- **Améliorations de la liste blanche** pour les architectures populaires (Llama, Mistral, Qwen, …), toujours avec la source qui justifie l'import.
- **Documentation** : corrections et précisions.

## Ce qu'il ne faut pas envoyer

- **De vrais fichiers malveillants**, même comme test. Un test peut seulement *référencer* une fonction dangereuse, jamais l'appeler.
- **Des poids de modèles** privés, ou de tiers sans autorisation de partage.
- **Des exécutables** : leur place est dans les [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases).
- **Des fichiers générés** : `ALF_relatorios/`, `build/`, `dist/`, `*.spec` et le `ALF_whitelist.txt` local.

## Sécurité

Les vulnérabilités passent par le **signalement privé de vulnérabilités** de GitHub : onglet **Security** du dépôt, puis **Report a vulnerability**. Jamais une issue publique. Voir [SECURITY.md](SECURITY.md).

Un modèle légitime signalé comme dangereux, ou un modèle hostile qui a passé tous les tests, n'est pas une vulnérabilité : c'est une issue normale, avec le détail de la vérification.

## Contributions assistées par IA

- Une partie du code et de la documentation de ce projet a été écrite avec l'aide d'outils d'IA, dont l'agent Codebuff. Le mainteneur relit chaque changement avant qu'il n'arrive sur `main`, et l'historique Git conserve la paternité de chaque commit.
- **Vous êtes responsable de ce que vous soumettez.** Si vous utilisez l'IA pour écrire du code, comprenez-le et sachez l'expliquer.
- **Les changements non testés ne sont pas acceptés.** Lancez les commandes ci-dessus et indiquez dans la pull request ce que vous avez lancé.
- Les pull requests qui semblent générées sans relecture peuvent être refusées : code qui ignore le style du projet, tests qui ne vérifient rien, commentaires génériques qui ne correspondent pas au code.
- Les mises à jour de **Dependabot** passent par la même relecture. Rien n'entre dans `main` sans les tests au vert.

## Relecture et fusion

- Le mainteneur relit les pull requests. Aucun délai n'est garanti.
- Les changements touchant la logique de vérification (couches d'analyse, verdicts, parseurs GGUF et safetensors) exigent de nouveaux tests et une explication dans la pull request.
- Les changements qui rendent la vérification **moins stricte** sont les plus examinés : en cas de doute, le verdict doit être jaune, pas vert.
- Une pull request par sujet, avec le problème et la solution en une ou deux phrases.

## Règles de code

1. **Ne chargez jamais un modèle malveillant pour tester.** Créez un pickle qui ne fait que *référencer* une fonction dangereuse, comme le font déjà les tests.
2. **Ne supprimez pas les avertissements de limite.** L'outil ne garantit pas la sécurité et la documentation doit continuer à le dire.
3. Le texte affiché à l'utilisateur vit dans `i18n.py`, dans les six langues (`en`, `pt`, `fr`, `es`, `it`, `zh`). Une clé manquante retombe sur l'anglais, mais les tests vérifient qu'aucune langue n'est incomplète.
4. Les modifications de la liste blanche doivent venir avec la source de l'import (le modèle ou sa documentation).
5. Préférez la bibliothèque standard de Python aux nouvelles dépendances. picklescan est la seule externe.
6. Gardez le code simple et lisible : fonctions courtes, le style `_check()` et `veredicto()` déjà utilisé dans le projet.
7. Si vous touchez à l'interface ou au moteur, testez au moins en anglais, en portugais et en chinois : trois alphabets différents (latin, latin accentué et CJK).

## Code de conduite

Soyez respectueux. Critiquez les idées, pas les personnes. Les questions des nouveaux venus sont bienvenues et méritent une réponse.
