import os
from pydub import AudioSegment
import csv

def cortar_audios(pasta_entrada, pasta_saida, labels):
    """
    Corta trechos de áudio baseados em um CSV de referência e exporta para 48kHz.
    Cada label é salva em uma pasta separada.
    
    Args:
        pasta_entrada (str): Caminho da pasta com arquivos .wav e .csv
        pasta_saida (str): Caminho da pasta para salvar os áudios cortados
        labels (list): Lista de labels a serem extraídas (ex: ['p', 'l'])
    """
    
    # Garante que a pasta de saída existe
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Cria uma pasta para cada label
    for label in labels:
        pasta_label = os.path.join(pasta_saida, label)
        os.makedirs(pasta_label, exist_ok=True)
    
    # Processa cada arquivo WAV na pasta de entrada
    for arquivo in os.listdir(pasta_entrada):
        if not arquivo.lower().endswith('.wav'):
            continue
            
        base_nome = os.path.splitext(arquivo)[0]
        caminho_wav = os.path.join(pasta_entrada, arquivo)
        caminho_csv = os.path.join(pasta_entrada, f"{base_nome}.wav.csv")
        
        # Verifica se o CSV correspondente existe
        if not os.path.exists(caminho_csv):
            continue
            
        # Carrega o áudio original
        audio = AudioSegment.from_wav(caminho_wav)
        
        # Processa o arquivo CSV
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for linha in reader:
                label = linha.get('label', '').strip() if linha.get('label') else ''
                
                # Verifica se a label está na lista desejada
                if not label or label not in labels:
                    continue
                    
                try:
                    # Converte tempos para float e arredonda
                    onset = round(float(linha['onset_s']), 3)
                    offset = round(float(linha['offset_s']), 3)
                    
                    # Calcula durações em milissegundos
                    inicio_ms = int(onset * 1000)
                    fim_ms = int(offset * 1000)
                    
                    # Corta o áudio
                    corte = audio[inicio_ms:fim_ms]
                    
                    # Define sample rate para 48kHz
                    if corte.frame_rate != 48000:
                        corte = corte.set_frame_rate(48000)
                    
                    # Gera nome do arquivo de saída
                    nome_saida = f"{base_nome}_{onset:.3f}_{offset:.3f}.wav"
                    
                    # Define pasta específica para a label
                    pasta_label = os.path.join(pasta_saida, label)
                    caminho_saida = os.path.join(pasta_label, nome_saida)
                    
                    # Exporta o áudio
                    corte.export(caminho_saida, format='wav')
                    
                except (ValueError, KeyError) as e:
                    print(f"Erro no arquivo {base_nome}: {str(e)}")
                    continue

def cortar_background(pasta_entrada, pasta_saida):
    """
    Corta trechos de áudio sem vocalização (background) e exporta para 48kHz.
    Para cada áudio, cria apenas um arquivo de background removendo todas as vocalizações.
    Os arquivos são salvos na pasta 'u' dentro da pasta de saída.
    
    Args:
        pasta_entrada (str): Caminho da pasta com arquivos .wav e .csv
        pasta_saida (str): Caminho da pasta para salvar os áudios de background
    """
    
    # Garante que a pasta de saída existe
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Cria pasta para background audio
    pasta_background = os.path.join(pasta_saida, 'u')
    os.makedirs(pasta_background, exist_ok=True)
    
    # Processa cada arquivo WAV na pasta de entrada
    for arquivo in os.listdir(pasta_entrada):
        if not arquivo.lower().endswith('.wav'):
            continue
            
        base_nome = os.path.splitext(arquivo)[0]
        caminho_wav = os.path.join(pasta_entrada, arquivo)
        caminho_csv = os.path.join(pasta_entrada, f"{base_nome}.wav.csv")
        
        # Verifica se o CSV correspondente existe
        if not os.path.exists(caminho_csv):
            continue
            
        # Carrega o áudio original
        audio = AudioSegment.from_wav(caminho_wav)
        audio_background = audio  # Copia o áudio original
        
        # Coleta todos os intervalos vocalizados
        intervalos_vocalizados = []
        
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for linha in reader:
                try:
                    onset = round(float(linha['onset_s']), 3)
                    offset = round(float(linha['offset_s']), 3)
                    
                    inicio_ms = int(onset * 1000)
                    fim_ms = int(offset * 1000)
                    
                    intervalos_vocalizados.append((inicio_ms, fim_ms))
                    
                except (ValueError, KeyError):
                    continue
        
        # Ordena intervalos por tempo de início (do maior para o menor para remoção)
        intervalos_vocalizados.sort(key=lambda x: x[0], reverse=True)
        
        # Remove cada intervalo vocalizado do áudio (do fim para o início)
        for inicio_ms, fim_ms in intervalos_vocalizados:
            try:
                # Remove o segmento vocalizado
                audio_background = audio_background[:inicio_ms] + audio_background[fim_ms:]
            except Exception as e:
                print(f"Erro ao remover segmento {inicio_ms}-{fim_ms} do arquivo {base_nome}: {str(e)}")
                continue
        
        # Verifica se ainda há áudio restante
        if len(audio_background) < 100:  # Menos de 100ms
            print(f"Arquivo {base_nome} não tem background suficiente após remoção das vocalizações")
            continue
        
        try:
            # Define sample rate para 48kHz
            if audio_background.frame_rate != 48000:
                audio_background = audio_background.set_frame_rate(48000)
            
            # Gera nome do arquivo de saída
            nome_saida = f"{base_nome}_background.wav"
            caminho_saida = os.path.join(pasta_background, nome_saida)
            
            # Exporta o áudio
            audio_background.export(caminho_saida, format='wav')
            print(f"Background salvo: {nome_saida}")
            
        except Exception as e:
            print(f"Erro ao salvar background do arquivo {base_nome}: {str(e)}")
            continue

if __name__ == "__main__":
    # cortar_audios(r"J:\ALL_DATA",
    #               r"H:\Users\Firmino\croped_vocal_aves",
    #               ['a', 'c', 'e', 'g', 'h', 'k', 'l', 'o', 'p', 'r', 's', 'y', 'z'])
    cortar_background(r"J:\ALL_DATA",
                      r"H:\Users\Firmino\croped_vocal_aves")
    
    # a, c, e, g, h, k, l, o, p, r, s, y, z 