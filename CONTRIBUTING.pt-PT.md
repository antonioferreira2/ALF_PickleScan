# Como contribuir

Obrigado por quereres ajudar. Este projeto existe para tornar a verificação de ficheiros de modelos de IA acessível a qualquer pessoa, por isso valorizamos clareza, simplicidade e honestidade sobre o que a ferramenta faz e não faz.

Disponível em: [English](CONTRIBUTING.md) · **Português (PT)** · [Français](CONTRIBUTING.fr.md) · [Español](CONTRIBUTING.es.md) · [Italiano](CONTRIBUTING.it.md) · [中文](CONTRIBUTING.zh.md)

> ⚠️ **Esta ferramenta não garante que o modelo é seguro.** Nenhuma contribuição pode enfraquecer ou esconder este aviso: fica na interface, nos relatórios e na documentação, em todos os idiomas.

## Antes de começar

- **`good first issue`**: tarefas pequenas, com contexto suficiente para começar. **`help wanted`** marca as maiores.
- Abre uma issue ou uma discussão antes de começar algo grande, para a abordagem ser combinada primeiro.

## Correr o projeto a partir do código

```text
git clone https://github.com/antonioferreira2/ALF_PickleScan.git
cd ALF_PickleScan
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ALF_picklescan_gui.py
```

É preciso Python **3.11 ou mais recente** para compilar os executáveis; os testes correm em 3.11 e 3.12, no Windows e no Linux. No Linux a interface precisa de `python3-tk` (`sudo apt install python3-tk`).

O `requirements.txt` é o único sítio onde a versão do picklescan está escrita: os workflows e os scripts de build leem-na de lá, por isso muda-a aí e em mais lado nenhum.

Para abrir a interface já com um modelo carregado — o mesmo que arrastar um ficheiro para cima do executável:

```text
python ALF_picklescan_gui.py modelo.gguf
```

## Verificações antes de abrir um pull request

```text
python -m py_compile ALF_picklescan.py ALF_picklescan_gui.py i18n.py
python -m unittest discover -s tests -v
```

Os testes geram as suas próprias amostras inofensivas em pastas temporárias, não precisam de rede e nunca executam o que inspecionam. O GitHub corre-os também em Windows e Linux a cada push e pull request (`.github/workflows/tests.yml`).

## O que é bem-vindo

- **Falsos positivos e falsos negativos.** Abre uma issue com o link público do modelo, a versão que usaste e a verificação assinalada.
- **Testes com ficheiros de exemplo inofensivos** que reproduzam um erro ou cubram uma deteção nova.
- **Traduções**, incluindo a revisão por um falante nativo dos README e deste guia.
- **Melhorias na whitelist** para arquiteturas populares (Llama, Mistral, Qwen, …), sempre com a fonte que justifica o import.
- **Documentação**: correções e clarificações.

## O que não enviar

- **Ficheiros maliciosos reais**, nem como teste. Um teste só pode *referenciar* uma função perigosa, nunca chamá-la.
- **Pesos de modelos** privados, ou de terceiros sem autorização para partilhar.
- **Executáveis**: o lugar deles é nas [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases).
- **Ficheiros gerados**: `ALF_relatorios/`, `build/`, `dist/`, `*.spec` e o `ALF_whitelist.txt` local.

## Segurança

As vulnerabilidades seguem o **reporte privado de vulnerabilidades** do GitHub: separador **Security** do repositório, depois **Report a vulnerability**. Nunca uma issue pública. Vê o [SECURITY.md](SECURITY.md).

Um modelo legítimo marcado como perigoso, ou um modelo hostil que passou em todos os testes, não é uma vulnerabilidade: é uma issue normal, com o detalhe da verificação.

## Contribuições assistidas por IA

- Parte do código e da documentação deste projeto foi escrita com ajuda de ferramentas de IA, incluindo o agente Codebuff. O mantenedor revê cada alteração antes de chegar à `main`, e o histórico do Git guarda a autoria de cada commit.
- **És responsável pelo que submetes.** Se usares IA para escrever código, percebe-o e consegue explicá-lo.
- **Alterações não testadas não são aceites.** Corre os comandos acima e diz no pull request o que correste.
- Pull requests que pareçam gerados sem revisão podem ser recusados: código que ignora o estilo do projeto, testes que não verificam nada, comentários genéricos que não correspondem ao código.
- As atualizações do **Dependabot** passam pela mesma revisão. Nada entra na `main` sem os testes a passar.

## Revisão e merge

- O mantenedor revê os pull requests. Não há prazo garantido.
- Alterações à lógica de verificação (camadas de análise, veredictos, parsers de GGUF e safetensors) exigem testes novos e uma explicação no pull request.
- As alterações que tornam a verificação **menos rigorosa** são as mais escrutinadas: na dúvida, o veredicto tem de ser amarelo, não verde.
- Um pull request por tema, com o problema e a solução numa frase ou duas.

## Regras de código

1. **Nunca carregues um modelo malicioso para testar.** Cria um pickle que apenas *referencia* uma função perigosa, como os testes já fazem.
2. **Não removas os avisos de limitação.** A ferramenta não garante segurança e a documentação tem de continuar a dizê-lo.
3. O texto mostrado ao utilizador vive no `i18n.py`, nos seis idiomas (`en`, `pt`, `fr`, `es`, `it`, `zh`). Uma chave em falta cai para inglês, mas os testes verificam que nenhum idioma fica incompleto.
4. As mudanças na whitelist têm de vir com a fonte do import (o modelo ou a sua documentação).
5. Prefere a biblioteca padrão de Python a dependências novas. O picklescan é a única externa.
6. Mantém o código simples e legível: funções curtas, o estilo `_check()` e `veredicto()` já usado no projeto.
7. Se mexeres na interface ou no motor, testa pelo menos em inglês, português e chinês: três alfabetos diferentes (latino, latino com acentos e CJK).

## Código de conduta

Sê respeitoso. Critica ideias, não pessoas. As perguntas de quem chega agora são bem-vindas e merecem resposta.
