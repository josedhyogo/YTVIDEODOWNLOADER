import yt_dlp
import PySimpleGUI as sg
import threading
import os
import sys


def contarArquivos(values):
    url = values["URL"] #Recebe a url

    with yt_dlp.YoutubeDL({
        "quiet": True, # Reduz mensagens exibidas no terminal
        "extract_flat": True # Evita a extração detalhada de informações, trazendo apenas dados superficiais(titulo,id...)
    }) as ydl: # Cria um objeto chamado "ydl"

        info = ydl.extract_info(url, download=False) #Impede o download e realiza apenas a requisição das informações resumidas

    if "entries" in info: # Verifica se existe a lista "entries" no dicionário "info"
        return len(info["entries"]) # Retorna o numero de itens dessa lista
    else:
        return 1 # Considera que há apenas um vídeo informado na url


def mostrarBarraProgresso(num_arquivos, arquivos_baixados):

    sg.one_line_progress_meter( # Função do PySimpleGUI  que mostra o progresso do download
        "BAIXANDO...", # Título
        arquivos_baixados, # Progresso atual
        num_arquivos # Progresso máximo
    ) # Atenção: essa função não aumenta o progresso a partir tempo dos arquivos sendo baixados, mas sim pela quantidade contabilizada como baixada. 


def baixarURL(values):
    try:
        url = values["URL"] #Recebe a url
        pasta = values["PASTA"] #Aramazena o caminho da pasta

        num_arquivos = contarArquivos(values) # Recebe o numero de informações

        def progresso(d): 
            ids_contados = set()

            if d["status"] == "finished": # Verifica se o estado do progresso/download está completo/finalizado

                id_videos = d["info-dict"]["id"] # Itera +1 no contador de arquivos para a barra de progresso
                if id_videos not in ids_contados:
                    ids_contados.add(id_videos)

                    window.write_event_value( # Envia o evento -PROGRESSO- para a janela em loop com os dados nas variaveis de arquivos
                        "-PROGRESSO-",
                        (len(id_videos), num_arquivos)
                    )

        # Localiza o FFmpeg
        if getattr(sys, "frozen", False): # verifica se o sys tem o atributo frozen e se ele vale True (ou seja, se está rodando como executável)”
            pasta_base = sys._MEIPASS # Define a pasta base 
        else: # Caso o status retorne FALSE, define a pasta base o diretório onde o script está, para que assim possa encontrar o ffmpeg
            pasta_base = os.path.dirname(__file__)

        ffmpeg_path = os.path.join(pasta_base, "ffmpeg") # Junta o caminho da pasta base com o nome "ffmpeg"

        options = {
            "outtmpl": os.path.join(pasta, "%(title)s.%(ext)s"), # Define o titulo do arquivo "texto video/audio" + "extensao" = "Meu video.mp4"
            "progress_hooks": [progresso],
            "ignoreerrors": True, # ENquanto TRUE, o download continua mesmo com erro em algum video/audio
            "ffmpeg_location": ffmpeg_path # Diz ao yt-dlp onde está a pasta do ffmpeg
        }
    # Verifica se o status do sys é o atributo frozen 
        if values["AUDIO"] == True:

            options["format"] = "bestaudio" # Pede ao yt-dlp para baixar apenas a melhor faixa de áudio disponível, sem o vídeo.

            options["postprocessors"] = [ # Etapas executadas depois do download
                { 
                    "key": "FFmpegExtractAudio", # Usa o Ffmpeg para converter o audio baixado
                    "preferredcodec": "mp3", # Converte o audio para mp3
                    "preferredquality": "192" # Define um equilíbrio entre desempenho e qualidade
                }
            ]

        elif values["VIDEO"] == True:

            options["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" # tenta a primeira combinação mp4; se não der, tenta o melhor mp4 já pronto; se também não der, pega o melhor disponível
            options["merge_output_format"] = "mp4" # Arquivo final depois de juntar as duas faixas(aúdio e vídeo)

        with yt_dlp.YoutubeDL(options) as ydl: # Cria um objeto que faz o trabalho, já com todas as configurações definidas
            ydl.download([url]) #Inicia o processo de download
    except Exception as erro:
        window.write_event_value("-ERRO-", str(erro)) # Envia um envento de erro para janela principal 
    finally:
        window.write_event_value("-FIM-"), None
# INÍCIO APLICAÇÃO 
sg.theme("DarkGrey13") #Tema do layout

sg.set_options( # Cores dos elementos
    text_color="#FFFFFF",
    input_elements_background_color="#FFFFFF",
    input_text_color="#000000",
    button_color=("#FFFFFF", "#FF0000")
)


layout = [

    [
        sg.Text( # Seleção de formato
            "FORMATO:",
            justification="center",# Formatação do texto 
            expand_x=True
        )
    ],

    [
        sg.Push(), #Seleção de formato
        sg.Radio("Áudio", "FORMATO", key="AUDIO"),
        sg.Radio("Vídeo", "FORMATO", key="VIDEO"),
        sg.Push()
    ],

    [
        sg.Text("URL:", size=(4, 1)),
        sg.Input(key="URL") # Entrada URL
    ],

    [
        sg.Text("Pasta:", size=(4, 1)),
        sg.Input(key="PASTA"), # Entrada Pasta
        sg.FolderBrowse("Escolher") # Abre o explorador de arquivos para selecionar a pasta
    ],

    [
        sg.Push(),
        sg.Button("Baixar"), # Iniciar processo de download
        sg.Push()
    ]
]


window = sg.Window("YOUTUBE DOWNLOAD", layout) # Define a janela


while True: # Mantém a janela aberta em loop

    event, values = window.read() # Registra os eventos de interação com a janela

    if event == sg.WINDOW_CLOSED: # Fecha a aplicação ao clicar no botão "X"(Fechar)
        break

    if event == "Baixar": # Inicia a rotina de download  
            window["Baixar"].update(disable=True)
            thread = threading.Thread( # Cria uma thread para executar o código separadamente do loop da interface
                target=baixarURL, # Passa a referencia para a função de download, sem executa-la imediatamente
                args=(values,), # Args recebe os valores obtidos no layout(inseridos em um dicionário) e guarda em uma tupla
                daemon=True # Define a thread como secundaria
            )

            thread.start() # Inicia a thread(tarefa)
            
    if event == "-PROGRESSO-":

        arquivos_baixados, num_arquivos = values["-PROGRESSO-"] # Os valores obtidios na função progresso são recebidos pelas variaveis

        mostrarBarraProgresso( # Chama a função mostrarBarraProgresso com as variáveis preenchidas com os valores obitidos na função progresso
            num_arquivos,
            arquivos_baixados
        )
    if event == "-ERRO-":
        sg.popup_error_with_traceback(values["-ERRO-"]) # Mostra mensagem de erro caso ocorra algum problema
    if event == "-FIM-":
        window["Baixar"].upadte(disable=False)

window.close()
