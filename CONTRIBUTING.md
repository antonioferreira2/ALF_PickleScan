# Como contribuir

Obrigado por querer ajudar. Este projeto existe para tornar a verificação de modelos de IA acessível a qualquer pessoa, por isso valorizamos clareza, simplicidade e honestidade sobre o que a ferramenta faz e não faz.

## Por onde começar

- **`good first issue`**: tarefas pequenas, com contexto suficiente para começar. Estão na secção Issues.
- **`help wanted`**: tarefas maiores para quem já conhece o projeto.
- Antes de começar uma tarefa grande, abre uma issue ou uma discussão para alinhar a abordagem.

## Preparar o ambiente

```
git clone https://github.com/antonioferreira2/ALF_PickleScan.git
cd ALF_PickleScan
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ALF_picklescan_gui.py
```

A versão do picklescan vem do `requirements.txt`, para não haver duas cópias do número. Também podes abrir a interface já com um modelo, o mesmo que arrastar o ficheiro para cima do executável:

```
python ALF_picklescan_gui.py modelo.gguf
```

No Linux, a interface precisa de `python3-tk` (`sudo apt install python3-tk`). Precisa de Python 3.11 ou mais recente para compilar os executáveis.

## Correr os testes

```
python -m unittest discover -s tests -v
```

Os testes geram as suas próprias amostras inofensivas e não precisam de rede. Também correm automaticamente em Windows e Linux a cada push (`.github/workflows/tests.yml`).

## Regras

1. **Nunca carregues modelos maliciosos para testar.** Os testes devem usar ficheiros inofensivos. Para testar a deteção de pickle, cria um pickle que apenas *referencia* uma função perigosa sem a chamar, como nos exemplos da pasta `tests/` quando existir.
2. **Não removas avisos de limitação.** A ferramenta não garante segurança e a documentação deve continuar a dizê-lo.
3. **Mudanças nas traduções:** a interface e as verificações vivem em `i18n.py` (`STRINGS` e `CHECK_STRINGS`). Se alteras um texto, atualiza os seis idiomas. As chaves em falta caem para inglês, mas é melhor evitá-lo — e os testes verificam que nenhum idioma fica incompleto.
4. **Mudanças na whitelist:** inclui sempre a origem do import (o modelo ou a documentação) no pull request.
5. **Código simples e legível.** Preferimos bibliotecas padrão de Python a dependências novas.

## Pull requests

- Um pull request por tema.
- Explica o problema e a solução numa frase ou duas.
- Confirma que `python -m py_compile ALF_picklescan.py ALF_picklescan_gui.py i18n.py` e `python -m unittest discover -s tests` passam.
- Se mexeste na interface ou no motor, testa pelo menos em inglês, português e chinês: são os três alfabetos diferentes (latino, latino com acentos e CJK).

## Código de conduta

Sê respeitoso. Critica ideias, não pessoas. Respostas a perguntas básicas são bem-vindas.
