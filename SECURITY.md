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
