# -*- coding: utf-8 -*-
"""
Workers (QThread) responsáveis pelas conversões pesadas, mantendo a
interface responsiva durante o processamento.
"""

import os
import sys
import json
import shutil
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def resource_path(relative_path: str) -> str:
    """Resolve o caminho de um recurso, funcionando tanto em modo script
    quanto empacotado pelo PyInstaller (--onefile)."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def _no_window_kwargs():
    """Evita abrir janela de console preta no Windows ao chamar subprocess."""
    kwargs = {}
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def find_executable(name: str, bundled_subdir: str = "ffmpeg") -> str:
    """Procura primeiro um executável empacotado junto ao app (pasta
    ffmpeg/), depois cai para o PATH do sistema."""
    exe_name = name + (".exe" if os.name == "nt" else "")
    bundled = resource_path(os.path.join(bundled_subdir, exe_name))
    if os.path.isfile(bundled):
        return bundled
    found = shutil.which(name)
    if found:
        return found
    return exe_name  # deixa o subprocess tentar e falhar com erro claro


def find_soffice() -> str:
    """Localiza o LibreOffice (soffice) em locais comuns do Windows/Linux."""
    candidates = [
        shutil.which("soffice"),
        shutil.which("soffice.exe"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
        if c and shutil.which(c or ""):
            return c
    return ""


def get_media_duration_seconds(ffprobe_path: str, filepath: str) -> float:
    """Retorna a duração (em segundos) de um arquivo de vídeo via ffprobe."""
    try:
        cmd = [
            ffprobe_path, "-v", "error", "-show_entries", "format=duration",
            "-of", "json", filepath,
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, **_no_window_kwargs())
        data = json.loads(out.decode("utf-8", errors="ignore"))
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


# --------------------------------------------------------------------------
# Vídeo
# --------------------------------------------------------------------------

COMPRESSION_PRESETS = {
    # nível: (crf, preset ffmpeg)
    "Baixa (qualidade máxima)": (18, "slow"),
    "Média (equilibrado)": (23, "medium"),
    "Alta (arquivo menor)": (28, "fast"),
}


class VideoConvertWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_ok = pyqtSignal(str)      # caminho de saída
    finished_error = pyqtSignal(str)   # mensagem de erro

    def __init__(self, input_path, output_path, output_format,
                 compress_enabled, compression_level, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format
        self.compress_enabled = compress_enabled
        self.compression_level = compression_level
        self._process = None
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
            except Exception:
                pass

    def run(self):
        ffmpeg = find_executable("ffmpeg")
        ffprobe = find_executable("ffprobe")

        if not os.path.isfile(self.input_path):
            self.finished_error.emit("Arquivo de entrada não encontrado.")
            return

        duration = get_media_duration_seconds(ffprobe, self.input_path)

        cmd = [ffmpeg, "-y", "-i", self.input_path]

        if self.compress_enabled:
            crf, preset = COMPRESSION_PRESETS.get(
                self.compression_level, (23, "medium")
            )
            # libx264 mantém a resolução original, reduzindo o tamanho via CRF
            cmd += [
                "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
                "-c:a", "aac", "-b:a", "128k",
            ]
        else:
            # conversão de formato "pura", sem recomprimir vídeo quando possível
            cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k"]

        cmd += ["-progress", "pipe:1", "-nostats", self.output_path]

        try:
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, **_no_window_kwargs()
            )
        except FileNotFoundError:
            self.finished_error.emit(
                "FFmpeg não encontrado. Verifique se ffmpeg.exe está na "
                "pasta 'ffmpeg/' junto ao programa ou instalado no PATH."
            )
            return
        except Exception as e:
            self.finished_error.emit(f"Erro ao iniciar o FFmpeg: {e}")
            return

        last_percent = 0
        for line in self._process.stdout:
            if self._cancelled:
                break
            line = line.strip()
            if line.startswith("out_time_ms="):
                try:
                    out_time_ms = int(line.split("=")[1])
                    if duration > 0:
                        percent = min(99, int((out_time_ms / 1_000_000) / duration * 100))
                        if percent > last_percent:
                            last_percent = percent
                            self.progress.emit(percent)
                except (ValueError, IndexError):
                    pass
            elif line.startswith("progress=") and "end" in line:
                self.progress.emit(100)

        self._process.wait()

        if self._cancelled:
            if os.path.isfile(self.output_path):
                try:
                    os.remove(self.output_path)
                except Exception:
                    pass
            self.finished_error.emit("Conversão cancelada pelo usuário.")
            return

        if self._process.returncode != 0:
            self.finished_error.emit(
                "O FFmpeg retornou um erro durante a conversão. "
                "Verifique se o arquivo de entrada não está corrompido."
            )
            return

        self.progress.emit(100)
        self.finished_ok.emit(self.output_path)


# --------------------------------------------------------------------------
# Fotos
# --------------------------------------------------------------------------

class PhotoConvertWorker(QThread):
    progress = pyqtSignal(int)
    file_done = pyqtSignal(str)
    finished_ok = pyqtSignal(int, int)   # sucesso, total
    finished_error = pyqtSignal(str)

    def __init__(self, input_paths, output_dir, output_format,
                 resize_percent, quality, parent=None):
        super().__init__(parent)
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.output_format = output_format.upper()
        self.resize_percent = resize_percent  # 100 = tamanho original
        self.quality = quality                # 1-100
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            from PIL import Image
        except ImportError:
            self.finished_error.emit(
                "A biblioteca Pillow não está instalada. Rode: "
                "pip install Pillow"
            )
            return

        total = len(self.input_paths)
        if total == 0:
            self.finished_error.emit("Nenhuma foto selecionada.")
            return

        success = 0
        ext_map = {"JPG": "JPEG", "JPEG": "JPEG", "PNG": "PNG",
                   "WEBP": "WEBP", "BMP": "BMP", "TIFF": "TIFF"}
        pillow_format = ext_map.get(self.output_format, self.output_format)
        out_ext = ".jpg" if pillow_format == "JPEG" else f".{self.output_format.lower()}"

        for i, path in enumerate(self.input_paths):
            if self._cancelled:
                break
            try:
                img = Image.open(path)

                if self.resize_percent != 100:
                    w, h = img.size
                    new_w = max(1, int(w * self.resize_percent / 100))
                    new_h = max(1, int(h * self.resize_percent / 100))
                    img = img.resize((new_w, new_h), Image.LANCZOS)

                if pillow_format == "JPEG" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                base_name = os.path.splitext(os.path.basename(path))[0]
                out_path = os.path.join(self.output_dir, base_name + out_ext)

                save_kwargs = {}
                if pillow_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = self.quality
                    save_kwargs["optimize"] = True

                img.save(out_path, pillow_format, **save_kwargs)
                success += 1
                self.file_done.emit(os.path.basename(out_path))
            except Exception as e:
                self.file_done.emit(f"Erro em {os.path.basename(path)}: {e}")

            percent = int(((i + 1) / total) * 100)
            self.progress.emit(percent)

        self.finished_ok.emit(success, total)


# --------------------------------------------------------------------------
# Documentos
# --------------------------------------------------------------------------

class DocConvertWorker(QThread):
    progress = pyqtSignal(int)
    finished_ok = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, input_path, output_dir, output_format, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_dir = output_dir
        self.output_format = output_format.lower()

    def run(self):
        soffice = find_soffice()
        if not soffice:
            self.finished_error.emit(
                "LibreOffice (soffice) não foi encontrado no sistema. "
                "Para converter documentos, instale o LibreOffice "
                "(gratuito, libreoffice.org) e tente novamente."
            )
            return

        if not os.path.isfile(self.input_path):
            self.finished_error.emit("Arquivo de entrada não encontrado.")
            return

        self.progress.emit(15)

        cmd = [
            soffice, "--headless", "--norestore", "--convert-to",
            self.output_format, "--outdir", self.output_dir, self.input_path,
        ]

        try:
            self.progress.emit(35)
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=300, **_no_window_kwargs()
            )
        except FileNotFoundError:
            self.finished_error.emit("Não foi possível executar o LibreOffice.")
            return
        except subprocess.TimeoutExpired:
            self.finished_error.emit("A conversão excedeu o tempo limite (5 min).")
            return
        except Exception as e:
            self.finished_error.emit(f"Erro inesperado: {e}")
            return

        self.progress.emit(90)

        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        expected_out = os.path.join(self.output_dir, f"{base_name}.{self.output_format}")

        if result.returncode == 0 and os.path.isfile(expected_out):
            self.progress.emit(100)
            self.finished_ok.emit(expected_out)
        else:
            self.finished_error.emit(
                "A conversão falhou. Verifique se o formato de saída é "
                "compatível com o arquivo de entrada."
            )
