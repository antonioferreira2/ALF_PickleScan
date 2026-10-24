# Contribuir

Gracias por querer ayudar. Este proyecto existe para que verificar archivos de modelos de IA sea accesible para cualquiera, por eso valoramos la claridad, la simplicidad y la honestidad sobre lo que la herramienta hace y no hace.

Disponible en: [English](CONTRIBUTING.md) · [Português (PT)](CONTRIBUTING.pt-PT.md) · [Français](CONTRIBUTING.fr.md) · **Español** · [Italiano](CONTRIBUTING.it.md) · [中文](CONTRIBUTING.zh.md)

> ⚠️ **Esta herramienta no garantiza que el modelo sea seguro.** Ninguna contribución puede debilitar u ocultar este aviso: se mantiene en la interfaz, en los informes y en la documentación, en todos los idiomas.

## Antes de empezar

- **`good first issue`**: tareas pequeñas, con contexto suficiente para empezar. **`help wanted`** marca las más grandes.
- Abre una issue o una discusión antes de empezar algo grande, para acordar primero el enfoque.

## Ejecutar el proyecto desde el código

```text
git clone https://github.com/antonioferreira2/ALF_PickleScan.git
cd ALF_PickleScan
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ALF_picklescan_gui.py
```

Se necesita Python **3.11 o posterior** para compilar los ejecutables; los tests se ejecutan en 3.11 y 3.12, en Windows y Linux. En Linux la interfaz necesita `python3-tk` (`sudo apt install python3-tk`).

`requirements.txt` es el único lugar donde está escrita la versión de picklescan: los workflows y los scripts de compilación la leen de ahí, así que cámbiala allí y en ningún otro sitio.

Para abrir la interfaz con un modelo ya cargado — lo mismo que arrastrar un archivo sobre el ejecutable:

```text
python ALF_picklescan_gui.py modelo.gguf
```

## Comprobaciones antes de abrir un pull request

```text
python -m py_compile ALF_picklescan.py ALF_picklescan_gui.py i18n.py
python -m unittest discover -s tests -v
```

Los tests generan sus propias muestras inofensivas en carpetas temporales, no necesitan red y nunca ejecutan lo que inspeccionan. GitHub también los ejecuta en Windows y Linux en cada push y pull request (`.github/workflows/tests.yml`).

## Lo que es bienvenido

- **Falsos positivos y falsos negativos.** Abre una issue con el enlace público del modelo, la versión que usaste y la comprobación señalada.
- **Tests con archivos de ejemplo inofensivos** que reproduzcan un error o cubran una detección nueva.
- **Traducciones**, incluida la revisión por un hablante nativo de los README y de esta guía.
- **Mejoras en la lista blanca** para arquitecturas populares (Llama, Mistral, Qwen, …), siempre con la fuente que justifica el import.
- **Documentación**: correcciones y aclaraciones.

## Lo que no enviar

- **Archivos maliciosos reales**, ni siquiera como prueba. Un test solo puede *referenciar* una función peligrosa, nunca llamarla.
- **Pesos de modelos** privados, o de terceros sin permiso para compartirlos.
- **Ejecutables**: su sitio está en las [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases).
- **Archivos generados**: `ALF_relatorios/`, `build/`, `dist/`, `*.spec` y el `ALF_whitelist.txt` local.

## Seguridad

Las vulnerabilidades pasan por el **reporte privado de vulnerabilidades** de GitHub: pestaña **Security** del repositorio y luego **Report a vulnerability**. Nunca una issue pública. Consulta [SECURITY.md](SECURITY.md).

Un modelo legítimo marcado como peligroso, o un modelo hostil que pasó todos los tests, no es una vulnerabilidad: es una issue normal, con el detalle de la comprobación.

## Contribuciones asistidas por IA

- Parte del código y de la documentación de este proyecto se escribió con ayuda de herramientas de IA, incluido el agente Codebuff. El mantenedor revisa cada cambio antes de que llegue a `main`, y el historial de Git conserva la autoría de cada commit.
- **Eres responsable de lo que envías.** Si usas IA para escribir código, entiéndelo y sé capaz de explicarlo.
- **Los cambios sin probar no se aceptan.** Ejecuta los comandos de arriba y di en el pull request qué ejecutaste.
- Los pull requests que parezcan generados sin revisión pueden rechazarse: código que ignora el estilo del proyecto, tests que no comprueban nada, comentarios genéricos que no corresponden al código.
- Las actualizaciones de **Dependabot** pasan por la misma revisión. Nada entra en `main` sin los tests en verde.

## Revisión y fusión

- El mantenedor revisa los pull requests. No hay plazo garantizado.
- Los cambios en la lógica de verificación (capas de análisis, veredictos, parsers de GGUF y safetensors) exigen tests nuevos y una explicación en el pull request.
- Los cambios que hacen la verificación **menos estricta** son los más examinados: en caso de duda, el veredicto debe ser amarillo, no verde.
- Un pull request por tema, con el problema y la solución en una frase o dos.

## Reglas de código

1. **Nunca cargues un modelo malicioso para probar.** Crea un pickle que solo *referencie* una función peligrosa, como ya hacen los tests.
2. **No elimines los avisos de limitación.** La herramienta no garantiza seguridad y la documentación debe seguir diciéndolo.
3. El texto que ve el usuario vive en `i18n.py`, en los seis idiomas (`en`, `pt`, `fr`, `es`, `it`, `zh`). Una clave que falte cae al inglés, pero los tests comprueban que ningún idioma queda incompleto.
4. Los cambios en la lista blanca deben venir con la fuente del import (el modelo o su documentación).
5. Prefiere la biblioteca estándar de Python a dependencias nuevas. picklescan es la única externa.
6. Mantén el código simple y legible: funciones cortas, el estilo `_check()` y `veredicto()` que ya usa el proyecto.
7. Si tocas la interfaz o el motor, prueba al menos en inglés, portugués y chino: tres alfabetos distintos (latino, latino con acentos y CJK).

## Código de conducta

Sé respetuoso. Critica ideas, no personas. Las preguntas de quien llega ahora son bienvenidas y merecen respuesta.
