# Conversor Multi-Formato (Vídeos / Fotos / Documentos)

Aplicativo desktop em **Python + PyQt5**, dark mode, com gradiente roxo-azul,
para converter vídeos (com compressão inteligente via FFmpeg), fotos (via
Pillow) e documentos (via LibreOffice headless).

⚠️ **Importante:** este pacote contém o **código-fonte completo e testado
sintaticamente**, pronto para virar `.exe`. O `.exe` em si precisa ser
compilado numa máquina Windows (o PyInstaller gera binários específicos do
sistema operacional em que roda — não é possível gerar um `.exe` Windows a
partir de Linux/Mac de forma confiável).

---

## 1. Estrutura do projeto

```
conversor_app/
├── main.py           # Interface (janela principal + 3 abas)
├── workers.py         # Threads de conversão (vídeo, foto, documento)
├── styles.py           # Tema dark + gradiente roxo-azul (QSS)
├── requirements.txt
├── ffmpeg/              # (você cria) ffmpeg.exe + ffprobe.exe
└── README.md
```

## 2. Pré-requisitos (na máquina Windows onde for gerar o .exe)

1. **Python 3.10+** instalado ([python.org](https://python.org))
2. **FFmpeg** (build estático para Windows):
   - Baixe em https://www.gyan.dev/ffmpeg/builds/ (versão "release essentials")
   - Extraia `ffmpeg.exe` e `ffprobe.exe` para a pasta `ffmpeg/` dentro do projeto
3. **LibreOffice** (apenas necessário para a aba Documentos funcionar):
   - Baixe em https://www.libreoffice.org/download/
   - Instale normalmente — o app detecta o `soffice.exe` automaticamente
   - *(Este é o único requisito externo que não pode ser embutido no `.exe`
     sem tornar o instalador muito pesado — LibreOffice completo tem ~300 MB)*

## 3. Instalar dependências Python

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Testar antes de compilar

```powershell
python main.py
```

Teste as 3 abas com arquivos reais antes de gerar o `.exe`.

## 5. Gerar o .exe com PyInstaller

Com `ffmpeg.exe` e `ffprobe.exe` já dentro da pasta `ffmpeg/`, rode:

```powershell
pyinstaller --noconfirm --onefile --windowed ^
  --name "ConversorMultiFormato" ^
  --add-binary "ffmpeg\ffmpeg.exe;ffmpeg" ^
  --add-binary "ffmpeg\ffprobe.exe;ffmpeg" ^
  main.py
```

O executável final aparece em `dist\ConversorMultiFormato.exe`.

- `--onefile`: gera um único `.exe` (mais fácil de distribuir, inicia um
  pouco mais devagar pois extrai temporariamente).
- `--windowed`: não abre console junto com a interface.
- `--add-binary`: embute o FFmpeg dentro do `.exe`, então o usuário final
  **não precisa instalar FFmpeg** — só LibreOffice, e só se for usar a aba
  Documentos.

Se quiser um ícone personalizado, adicione `--icon=icon.ico` ao comando.

## 6. Distribuição

- O `.exe` gerado roda offline para as abas **Vídeos** e **Fotos** sem
  nenhuma instalação adicional (FFmpeg já embutido).
- Para a aba **Documentos**, o LibreOffice precisa estar instalado na
  máquina do usuário final (não há forma leve de embutir esse motor).
  Se isso for inviável para o seu caso de uso, uma alternativa é remover a
  aba Documentos ou trocá-la por uma biblioteca 100% Python mais limitada
  (ex.: `python-docx` + `reportlab`, que cobre menos formatos, mas dispensa
  instalação externa).

## 7. Notas técnicas sobre as funcionalidades

### Vídeos
- Compressão inteligente usa `libx264` com CRF (Constant Rate Factor):
  - Baixa compressão → CRF 18 (qualidade máxima, arquivo maior)
  - Média → CRF 23
  - Alta compressão → CRF 28 (arquivo bem menor, ainda mantém a resolução)
- A **resolução do vídeo nunca é alterada** — apenas a taxa de bits/qualidade,
  conforme pedido ("mínima perda de resolução").
- Progresso em tempo real via `ffmpeg -progress pipe:1`, comparado com a
  duração total obtida via `ffprobe`.
- Cancelamento de conversão em andamento é suportado (botão "Cancelar").

### Fotos
- Suporta lote (múltiplos arquivos de uma vez).
- Redimensionamento por porcentagem (10%–100% do tamanho original).
- Qualidade ajustável (JPG/WEBP) via slider.
- Conversão automática de modo de cor (RGBA→RGB) ao salvar em JPG.

### Documentos
- Usa LibreOffice em modo headless (`soffice --headless --convert-to`).
- Formatos de saída disponíveis mudam dinamicamente conforme o formato de
  entrada selecionado.
- Timeout de 5 minutos por conversão para evitar travamentos com arquivos
  corrompidos.

## 8. Tratamento de erros implementado

- FFmpeg/FFprobe não encontrado → mensagem clara pedindo para verificar a
  pasta `ffmpeg/` ou o PATH.
- LibreOffice não encontrado → mensagem com link de download.
- Arquivo de entrada inexistente/corrompido → mensagem específica.
- Timeout em conversões de documento.
- Todas as exceções de conversão de foto são reportadas por arquivo,
  sem interromper o lote inteiro.

## 9. Limitações conhecidas

- A aba Documentos depende do LibreOffice estar instalado (ver seção 6).
- PDFs escaneados (imagem) na conversão PDF→DOCX podem perder formatação —
  isso é uma limitação do próprio motor do LibreOffice, não do app.
- Vídeos muito grandes (dezenas de GB) podem demorar de acordo com o
  hardware — isso é esperado, já que a compressão é feita localmente.
