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
        
        # Processa o arquivo CSV - primeiro lê todas as linhas
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            linhas = list(reader)
        
        # Agrupa "r" consecutivos (até 5)
        grupos_r = []
        i = 0
        while i < len(linhas):
            linha = linhas[i]
            label = linha.get('label', '').strip() if linha.get('label') else ''
            
            # Se não for uma label desejada, pula
            if not label or label not in labels:
                i += 1
                continue
            
            # Inicia um grupo de "r" consecutivos
            grupo = [linha]
            j = i + 1
            
            # Verifica as próximas linhas para adicionar ao grupo (máximo 5)
            while j < len(linhas) and len(grupo) < 5:
                proxima_label = linhas[j].get('label', '').strip() if linhas[j].get('label') else ''
                if proxima_label in labels:
                    # Verifica a distância entre o offset da última linha do grupo e o onset da próxima
                    try:
                        offset_anterior = float(grupo[-1]['offset_s'])
                        onset_proximo = float(linhas[j]['onset_s'])
                        distancia = onset_proximo - offset_anterior
                        
                        # Se a distância for maior que 1 segundo, não adiciona ao grupo
                        if distancia > 1.0:
                            break
                        
                        grupo.append(linhas[j])
                        j += 1
                    except (ValueError, KeyError):
                        break
                else:
                    break
            
            grupos_r.append(grupo)
            i = j
        
        # Processa cada grupo
        for grupo in grupos_r:
            try:
                # Pega o onset do primeiro e offset do último
                onset = round(float(grupo[0]['onset_s']), 3)
                offset = round(float(grupo[-1]['offset_s']), 3)
                
                # Calcula durações em milissegundos
                inicio_ms = int(onset * 1000)
                fim_ms = int(offset * 1000)
                
                # Corta o áudio
                corte = audio[inicio_ms:fim_ms]
                
                # Define sample rate para 48kHz
                if corte.frame_rate != 48000:
                    corte = corte.set_frame_rate(48000)
                
                # Gera nome do arquivo de saída incluindo número de "r"s no grupo
                num_rs = len(grupo)
                nome_saida = f"{base_nome}_{onset:.3f}_{offset:.3f}_n{num_rs}.wav"
                
                # Define pasta específica para a label
                pasta_label = os.path.join(pasta_saida, labels[0])  # Usa a primeira label da lista
                caminho_saida = os.path.join(pasta_label, nome_saida)
                
                # Exporta o áudio
                corte.export(caminho_saida, format='wav')
                
            except (ValueError, KeyError) as e:
                print(f"Erro no arquivo {base_nome}: {str(e)}")
                continue

if __name__ == "__main__":
    cortar_audios(r"J:\ALL_DATA",
                  r"H:\Users\Firmino\croped_vocal_aves_r",
                  ['r'])