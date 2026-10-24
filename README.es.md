<p align="center"><img src="assets/logo.png" alt="ALF_picklescan" width="150"></p>

# ALF_picklescan

**Verificador gratuito y de código abierto de archivos de modelos de IA.** Antes de cargar un modelo que has descargado, comprueba su integridad, su estructura y si esconde código peligroso. Compatible con archivos **GGUF**, **safetensors** y **pickle/PyTorch** (`.bin`, `.pt`, `.pth`, `.pkl`). Windows y Linux. Sin instalación y sin necesidad de saber programar.

> ⚠️ **Esta herramienta no garantiza que el modelo sea seguro.** Solo realiza pruebas sobre el archivo: integridad (SHA-256), estructura e importaciones de los archivos pickle. No analiza el comportamiento del modelo, y un modelo entrenado para un disparador oculto puede pasar todas las pruebas. Es un primer filtro, nunca una garantía de seguridad. Consulta las [Limitaciones](#limitaciones).

Disponible en: [English](README.md) · [Português (PT)](README.pt-PT.md) · [Français](README.fr.md) · **Español** · [Italiano](README.it.md) · [中文](README.zh.md) — la interfaz de la aplicación está disponible en los seis idiomas.

![ALF_picklescan verificando un archivo de modelo con resultado verde](screenshots/gui-en.png)

---

## Por qué existe este proyecto

Cualquiera puede publicar un modelo en una plataforma pública, y cualquiera puede descargarlo. Los archivos de modelos no son datos inertes: un **pickle** (usado por la mayoría de los checkpoints de PyTorch, `.bin`, `.pt`, `.pth`) puede ejecutar código en el momento en que lo cargas. Un archivo correcto cuando se publicó puede ser reemplazado más tarde, y una descarga puede llegar corrupta o manipulada.

Quien ejecuta modelos en local no tiene, en la práctica, forma de responder a una pregunta sencilla: *¿este archivo es el que publicó el autor y contiene algo claramente hostil?* Instala el modelo y espera que salga bien.

Los escáneres privados y las plataformas de pago responden a eso para las empresas. Este proyecto responde para todos los demás: estudiantes, investigadores, equipos pequeños, curiosos con un portátil. **La seguridad básica no debería ser un servicio de pago.** ALF_picklescan es gratuito, con licencia MIT, sin cuenta, sin telemetría, sin servidor y sin límites. Está hecho para ser copiado, mejorado y compartido de nuevo.

El autor no vende nada, no recoge datos y no pide donaciones. El objetivo es que más personas comprueben lo que descargan y que menos máquinas queden comprometidas por un archivo que nadie miró.

## Qué hace

- Calcula el **SHA-256** del archivo y lo compara con el hash publicado por el autor del modelo.
- Valida la **estructura** de archivos GGUF, safetensors y ZIP de PyTorch — incluidos los metadatos GGUF y su **plantilla de chat**, que renderiza el motor de inferencia, y si cada tensor safetensors tiene realmente el tamaño que exigen su forma y su dtype.
- Lee las **importaciones** de los archivos pickle **sin ejecutarlas** (con la misma técnica que [picklescan](https://github.com/mmaitre314/picklescan)) y señala funciones peligrosas conocidas, como `os.system`, `subprocess`, `eval` o `exec`.
- Muestra **lo que ejecutaría la llamada sospechosa**: el comando, la URL o el bloque codificado que viaja dentro del pickle, presentado como prueba, junto con patrones de shell, descarga, robo de credenciales, persistencia y ofuscación. No se ejecuta nada.
- Señala **archivos ejecutables** escondidos dentro de un paquete de modelo.
- Muestra un **semáforo** y crea un **informe HTML** que puedes guardar o compartir.
- Muestra el **nombre y el detalle de cada comprobación en el idioma que elijas** (inglés, portugués, francés, español, italiano o chino), incluido el informe.

El análisis es de solo lectura. La herramienta nunca carga, importa ni ejecuta el modelo.

## Descargar

Ve a la página de [**Releases**](https://github.com/antonioferreira2/ALF_PickleScan/releases) y elige el archivo para tu sistema. Las versiones de Windows y Linux se publican por separado.

| Sistema | Archivo | Requisitos |
|---|---|---|
| **Windows 10 / 11** (64 bits) | `ALF_picklescan-windows-x64.exe` | Ninguno. Doble clic. Compilado con Python 3.11 en Windows Server 2022. |
| **Linux** (x86-64) | `ALF_picklescan-linux-x86_64` | glibc **2.35** o posterior — Ubuntu 22.04+, Debian 12+, Fedora 36+, Linux Mint 21+. Compilado en Ubuntu 22.04. |

Cada archivo tiene un `.sha256` junto a él. **Compruébalo antes de ejecutar el archivo.**

**Windows** (Símbolo del sistema o PowerShell):
```
certutil -hashfile ALF_picklescan-windows-x64.exe SHA256
```

**Linux:**
```
sha256sum -c ALF_picklescan-linux-x86_64.sha256
chmod +x ALF_picklescan-linux-x86_64
./ALF_picklescan-linux-x86_64
```

### Verificar el origen del ejecutable

Cada versión nueva incluye también una **atestación de compilación** de GitHub (*Artifact Attestations*), que vincula el archivo con el flujo de trabajo que lo compiló y con el commit exacto. Con el [GitHub CLI](https://cli.github.com/) instalado:

```
gh attestation verify ALF_picklescan-windows-x64.exe --repo antonioferreira2/ALF_PickleScan
gh attestation verify ALF_picklescan-linux-x86_64 --repo antonioferreira2/ALF_PickleScan
```

Una atestación válida demuestra **quién compiló** el archivo y a partir de qué código — no demuestra que el código sea seguro. La versión v2.1.0 es anterior y solo tiene el `.sha256`.

Si Windows SmartScreen dice que la aplicación no se reconoce, haz clic en **Más información → Ejecutar de todos modos**. Ese aviso aparece porque el ejecutable no está firmado digitalmente; un certificado de firma cuesta dinero cada año y este proyecto es gratuito. Comprueba siempre el hash y compáralo con el publicado en la página de la versión.

Otras plataformas: el código fuente funciona en cualquier sistema con Python y Tk (macOS incluido). Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para ejecutarlo desde el código.

## Cómo usarlo

1. Abre la aplicación y elige tu idioma en la esquina superior derecha.
2. Haz clic en **Choose file** (Elegir archivo) y selecciona el modelo.
3. Pega el **SHA-256 publicado por el autor** (muy recomendable — búscalo en la página oficial del modelo).
4. Haz clic en **Verify model** (Verificar modelo).
5. Lee el resultado. Haz clic en **Open report** (Abrir informe) para ver todos los detalles.

También puedes **arrastrar el archivo del modelo sobre el ejecutable**: la ventana se abre analizando ya ese archivo. En Linux, pasa la ruta como argumento — `./ALF_picklescan modelo.gguf`.

El informe se guarda junto al programa, en `ALF_relatorios/`.

Línea de comandos (Linux o Windows, con Python instalado):

```
python ALF_picklescan.py model.gguf --sha256 <hash>
```

Los códigos de salida facilitan su uso en scripts y pipelines de CI: `0` verde, `1` amarillo, `2` rojo, `3` error.

Con `--json`, el mismo resultado se imprime como un documento JSON (comprobaciones, veredicto y código de salida) y no se escribe informe HTML — práctico para pipelines y scripts.

## Resultados

| Color | Significado | Qué hacer |
|---|---|---|
| 🟢 **VERDE** — aprobado con limitaciones | Hash confirmado, sin alertas | Puedes usarlo, respetando las limitaciones |
| 🟡 **AMARILLO** — revisión manual | Sin hash de referencia, importaciones fuera de la lista blanca, texto sospechoso o análisis incompleto | Revisa los detalles antes de usarlo |
| 🔴 **ROJO** — no usar | Hash distinto, malware detectado, importaciones peligrosas o estructura inválida | No uses este archivo |

Un resultado verde **nunca** aparece sin un hash de referencia confirmado.

![ALF_picklescan con resultado rojo, mostrando el comando de descarga y ejecución encontrado en el archivo](screenshots/gui-red.png)

Un archivo puede superar la comprobación del hash y seguir siendo hostil. Aquí el hash coincide y el resultado es rojo, porque el archivo lleva un comando de descarga y ejecución. La muestra se generó para esta captura: solo *referencia* la función, nunca la ejecuta.
## Limitaciones

- **No es una garantía de seguridad.** Un modelo malicioso entrenado para comportarse mal solo con un disparador concreto puede pasar todas las pruebas.
- **Sin análisis de comportamiento.** La herramienta comprueba el archivo, no lo que hace el modelo cuando se ejecuta.
- **El análisis de pickle usa una lista de funciones peligrosas conocidas.** Una carga útil nueva, fuera de la lista, puede pasar. Las llamadas sin importaciones identificables se marcan en amarillo por ese motivo.
- **Confiar en el hash.** El hash demuestra que el archivo coincide con lo publicado, no que quien lo publicó sea de fiar.
- **GGUF y safetensors solo se validan estructuralmente.** Eso confirma que el archivo está bien formado, no que los pesos sean buenos u honestos.

Para modelos que uses con herramientas o con acceso a datos (agentes, asistentes locales con acceso a archivos), **ejecútalos aislados**: un contenedor o una máquina virtual sin red y sin credenciales.

## Lista blanca de importaciones

En la primera ejecución, la aplicación crea `ALF_whitelist.txt` junto al programa. Contiene las importaciones consideradas normales en checkpoints de PyTorch y NumPy. Si un modelo legítimo se marca en amarillo solo por una importación normal, puedes añadirla después de comprobar que es esperada en ese modelo. Las contribuciones que mejoren la lista predeterminada para otras arquitecturas son muy bienvenidas.

Si la carpeta es de solo lectura, la aplicación usa la lista integrada y no falla.

## Qué contiene este repositorio

Aquí solo se publica lo necesario para usar, compilar y mejorar la herramienta:

| Ruta | Para qué sirve |
|---|---|
| `ALF_picklescan.py` | Motor de verificación e interfaz de línea de comandos |
| `ALF_picklescan_gui.py` | Interfaz gráfica (Tk) |
| `i18n.py` | Traducciones de la interfaz (EN, PT, FR, ES, IT, ZH) |
| `requirements.txt` | Versión fijada de picklescan, la única dependencia externa |
| `assets/logo.png` | Logotipo del proyecto, usado al principio de los README |
| `build_exe.bat`, `build_linux.sh` | Compilaciones reproducibles para Windows y Linux |
| `tests/test_smoke.py` | Pruebas automáticas con muestras inofensivas generadas al momento |
| `screenshots/` | Imágenes usadas en la documentación |
| `README*.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` | Documentación y licencia |
| `.github/workflows/` | Pruebas automáticas y compilación de la versión para ambas plataformas |

**No** están en el repositorio, a propósito:

- los **ejecutables** — están en las [Releases](https://github.com/antonioferreira2/ALF_PickleScan/releases), para que un clon nuevo siga siendo pequeño y el historial no se llene de binarios;
- resultados de compilación (`build/`, `dist/`, `*.spec`), informes generados (`ALF_relatorios/`) y el `ALF_whitelist.txt` local;
- **archivos de modelos** de cualquier tipo, y cualquier muestra de prueba que pudiera usarse para atacar a alguien;
- documentos internos de planificación del lanzamiento.

Para compilar desde el código, ejecuta `build_exe.bat` en Windows o `./build_linux.sh` en Linux. Ambos necesitan Python 3.11 o posterior y producen un ejecutable único que ya incluye picklescan.

## Hoja de ruta

Plan público. Los elementos pueden cambiar; el avance se sigue en las [Issues](https://github.com/antonioferreira2/ALF_PickleScan/issues) y las [Discussions](https://github.com/antonioferreira2/ALF_PickleScan/discussions).

1. **v2.1: interfaz multilingüe y versión Linux.** ✅ Inglés, portugués, francés, español, italiano y chino en la aplicación; versiones de Windows y Linux; picklescan incluido en los ejecutables.
2. **v2.2: pruebas de la carga útil.** ✅ Cuando se referencia una función peligrosa, el informe muestra los argumentos que recibiría — el comando, la URL, el bloque codificado — y señala patrones de shell, descarga, robo de credenciales, persistencia y ofuscación.
3. **v2.3: mensajes de verificación traducidos.** ✅ Nombres, detalles e informe siguen el idioma elegido, en los seis idiomas.
4. **v2.4: más detecciones y automatización.** ✅ Detección propia de `pydoc`, `timeit` y `pip`, más importaciones de indirección; plantilla de chat de los GGUF; tamaños de los tensores en safetensors; atestaciones de compilación firmadas; salida `--json` para CI.
5. **v3.0: más formatos.** Soporte de ONNX y otros formatos de modelo.

## Contribuir

¿Eres nuevo? Empieza por una **`good first issue`**: tareas pequeñas y bien descritas para primeras contribuciones.

- Traduce los mensajes de verificación del motor (`ALF_picklescan.py`) para que los informes se lean en otros idiomas.
- Mejora la lista blanca de importaciones para arquitecturas populares (Llama, Mistral, Qwen, etc.), con ejemplos revisados.
- Añade pruebas automáticas con archivos de ejemplo inofensivos.
- Revisa una de las traducciones del README si eres hablante nativo.

Para reportar un falso positivo, abre una issue con el enlace público del modelo, la versión que usaste y la comprobación señalada. No envíes archivos de modelos privados. Para el proceso completo, consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Seguridad

Para reportar una vulnerabilidad, sigue [SECURITY.md](SECURITY.md). No abras una issue pública para problemas de seguridad.

## Autor

Creado por **António Ferreira** (ALF), para ayudar a la comunidad a usar modelos de IA con un poco más de seguridad. No es una verificación de hechos sobre ningún modelo y no certifica nada: es solo una prueba básica, y puede equivocarse.

Las mejoras, los forks y las herramientas mejores son bienvenidos. Si puedes hacer algo mejor para la sociedad, adelante.

## Licencia

MIT. Consulta [LICENSE](LICENSE). picklescan también tiene licencia MIT.
