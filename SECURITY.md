# Política de segurança

## Reportar uma vulnerabilidade

Não abras uma issue pública para problemas de segurança.

Usa a **reporte privado de vulnerabilidades** do GitHub: separador **Security** do repositório, depois **Report a vulnerability**. Só os mantenedores veem o relato.

Inclui, se possível:
- versão da ferramenta (ver a release ou o cabeçalho do relatório);
- descrição do problema e o impacto esperado;
- passos para reproduzir, ou um ficheiro de teste mínimo (sem modelos reais com conteúdo malicioso publicados em público).

## Falsos positivos e falsos negativos

Um modelo legítimo marcado como perigoso, ou um modelo malicioso que passou sem alertas, não é necessariamente uma vulnerabilidade, mas queremos saber. Usa as [Issues](https://github.com/antonioferreira2/ALF_PickleScan/issues) para isto, indicando o modelo (nome e link público) e o detalhe da verificação. Não envies pesos de modelos privados.

## Âmbito da análise

O ALF_picklescan verifica o hash, a estrutura e os imports dos ficheiros, incluindo o chat template dos GGUF. Não analisa o comportamento dos modelos, nem deteta backdoors nos pesos. Um relatório verde não significa que o modelo é seguro. Ver a secção Limitações do README.

## Versões suportadas

Apenas a versão mais recente publicada em [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases) recebe correções.

## Verificar as releases

Cada executável publicado acompanha um ficheiro `.sha256`. Confirma o hash antes de usar:

```
certutil -hashfile ALF_picklescan-windows-x64.exe SHA256
```

```
sha256sum -c ALF_picklescan-linux-x86_64.sha256
```

## Verificar a atestação de origem

O hash diz que o ficheiro não foi alterado depois de publicado. A atestação diz quem o construiu. Os executáveis da v2.5.0 e das releases seguintes trazem uma atestação de proveniência (SLSA) assinada pelo GitHub Actions: liga o ficheiro ao workflow, à tag e ao commit que o geraram.

Precisa do GitHub CLI 2.49 ou superior, com sessão iniciada (`gh auth login`):

```
gh attestation verify ALF_picklescan-windows-x64.exe --repo antonioferreira2/ALF_PickleScan
```

```
gh attestation verify ALF_picklescan-linux-x86_64 --repo antonioferreira2/ALF_PickleScan
```

A verificação passa se o ficheiro corresponder ao que o workflow construiu. Se o alterares, ou se vier de outro sítio, falha. Usa as duas verificações, hash e atestação: a primeira é mais rápida e a segunda prova a origem.
