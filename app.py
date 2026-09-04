import yt_dlp
import PySimpleGUI as sg
import threading
import os
import sys


def contarArquivos(values):
    url = values["URL"]

    with yt_dlp.YoutubeDL({
        "quiet": True,
        "extract_flat": True
    }) as ydl:

        info = ydl.extract_info(url, download=False)

    if "entries" in info:
        return len(info["entries"])
    else:
        return 1


def mostrarBarraProgresso(num_arquivos, arquivos_baixados):

    sg.one_line_progress_meter(
        "BAIXANDO...",
        arquivos_baixados,
        num_arquivos
    )


def baixarURL(values):

    url = values["URL"]
    pasta = values["PASTA"]

    num_arquivos = contarArquivos(values)

    arquivos_baixados = 0

    def progresso(d):
        nonlocal arquivos_baixados

        if d["status"] == "finished":

            arquivos_baixados += 1

            window.write_event_value(
                "-PROGRESSO-",
                (arquivos_baixados, num_arquivos)
            )

    # Localiza o FFmpeg
    if getattr(sys, "frozen", False):
        pasta_base = sys._MEIPASS
    else:
        pasta_base = os.path.dirname(__file__)

    ffmpeg_path = os.path.join(pasta_base, "ffmpeg")

    options = {
        "outtmpl": os.path.join(pasta, "%(title)s.%(ext)s"),
        "progress_hooks": [progresso],
        "ignoreerrors": True,
        "ffmpeg_location": ffmpeg_path
    }

    if values["AUDIO"] == True:

        options["format"] = "bestaudio"

        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ]

    elif values["VIDEO"] == True:

        options["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
        options["merge_output_format"] = "mp4"

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])


sg.theme("DarkGrey13")

sg.set_options(
    text_color="#FFFFFF",
    input_elements_background_color="#FFFFFF",
    input_text_color="#000000",
    button_color=("#FFFFFF", "#FF0000")
)


layout = [

    [
        sg.Text(
            "FORMATO:",
            justification="center",
            expand_x=True
        )
    ],

    [
        sg.Push(),
        sg.Radio("Áudio", "FORMATO", key="AUDIO"),
        sg.Radio("Vídeo", "FORMATO", key="VIDEO"),
        sg.Push()
    ],

    [
        sg.Text("URL:", size=(4, 1)),
        sg.Input(key="URL")
    ],

    [
        sg.Text("Pasta:", size=(4, 1)),
        sg.Input(key="PASTA"),
        sg.FolderBrowse("Escolher")
    ],

    [
        sg.Push(),
        sg.Button("Baixar"),
        sg.Push()
    ]
]


window = sg.Window("YOUTUBE DOWNLOAD", layout)


while True:

    event, values = window.read()

    if event == sg.WINDOW_CLOSED:
        break

    if event == "Baixar":

        thread = threading.Thread(
            target=baixarURL,
            args=(values,),
            daemon=True
        )

        thread.start()

    if event == "-PROGRESSO-":

        arquivos_baixados, num_arquivos = values["-PROGRESSO-"]

        mostrarBarraProgresso(
            num_arquivos,
            arquivos_baixados
        )


window.close()