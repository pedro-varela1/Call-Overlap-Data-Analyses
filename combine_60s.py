import os
import random
import glob
import numpy as np
from pydub import AudioSegment
import warnings
import csv

# Ignorar warnings específicos do Librosa
warnings.filterwarnings("ignore", category=UserWarning)

def criar_audios_60s(pasta_overlaps, pasta_background, pasta_saida, n_vocalizacoes=500):
    """
    Cria áudios de 60 segundos combinando sobreposições com intervalos de background aleatórios
    
    Args:
        pasta_overlaps (str): Pasta com as sobreposições organizadas (J:\\overlap_especificos)
        pasta_background (str): Pasta com áudios de background (J:\\croped_vocal\\u)
        pasta_saida (str): Pasta para salvar os áudios finais de 60s
        n_vocalizacoes (int): Número de vocalizações de cada tipo a serem utilizadas (default: 500)
    """
    # Garantir que a pasta de saída existe
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Coletar todas as vocalizações por tipo
    vocalizacoes_por_tipo = {}
    
    print("Coletando vocalizações...")
    for pasta in os.listdir(pasta_overlaps):
        caminho_pasta = os.path.join(pasta_overlaps, pasta)
        if os.path.isdir(caminho_pasta):
            arquivos_wav = glob.glob(os.path.join(caminho_pasta, '*.wav'))
            if arquivos_wav:
                # Limitar ao número especificado de vocalizações
                if len(arquivos_wav) > n_vocalizacoes:
                    arquivos_wav = random.sample(arquivos_wav, n_vocalizacoes)
                vocalizacoes_por_tipo[pasta] = arquivos_wav
                print(f"Tipo {pasta}: {len(arquivos_wav)} vocalizações")
    
    # Coletar áudios de background
    print("Coletando áudios de background...")
    arquivos_background = glob.glob(os.path.join(pasta_background, '*.wav'))
    if not arquivos_background:
        print("Erro: Nenhum arquivo de background encontrado!")
        return
    
    print(f"Encontrados {len(arquivos_background)} arquivos de background")
    
    # Criar lista única com todas as vocalizações
    todas_vocalizacoes = []
    for tipo, arquivos in vocalizacoes_por_tipo.items():
        todas_vocalizacoes.extend(arquivos)
    
    print(f"Total de vocalizações: {len(todas_vocalizacoes)}")
    
    # Embaralhar as vocalizações para distribuição aleatória
    random.shuffle(todas_vocalizacoes)
    
    # Calcular quantas vocalizações cabem em 60s e quantos áudios precisamos
    duracao_alvo_ms = 60 * 1000  # 60 segundos em ms
    intervalo_min_ms = 500  # 500 ms
    intervalo_max_ms = 2000  # 2 segundos

    # Estimar duração média das vocalizações (vamos assumir ~1.2s como estimativa)
    duracao_media_vocalizacao_ms = 1200
    intervalo_medio_ms = (intervalo_min_ms + intervalo_max_ms) / 2
    
    # Calcular quantas vocalizações cabem aproximadamente em 60s
    vocalizacoes_por_audio = int(duracao_alvo_ms / (duracao_media_vocalizacao_ms + intervalo_medio_ms))
    
    # Calcular quantos áudios de 60s precisamos
    num_audios_necessarios = int(np.ceil(len(todas_vocalizacoes) / vocalizacoes_por_audio))
    
    print(f"Estimativa: ~{vocalizacoes_por_audio} vocalizações por áudio")
    print(f"Criando {num_audios_necessarios} áudios de 60s")
    
    # Criar os áudios de 60s
    for i in range(num_audios_necessarios):
        print(f"\nCriando áudio {i+1}/{num_audios_necessarios}...")
        
        # Pegar o próximo lote de vocalizações
        inicio_idx = i * vocalizacoes_por_audio
        fim_idx = min((i + 1) * vocalizacoes_por_audio, len(todas_vocalizacoes))
        vocalizacoes_lote = todas_vocalizacoes[inicio_idx:fim_idx]
        
        if not vocalizacoes_lote:
            break
            
        print(f"Processando {len(vocalizacoes_lote)} vocalizações...")
        
        # Criar áudio de 60s
        audio_60s, anotacoes = criar_audio_individual(vocalizacoes_lote, arquivos_background, duracao_alvo_ms)
        
        if audio_60s and anotacoes:
            # Salvar o áudio
            nome_arquivo = f"audio_60s_{i+1:03d}.wav"
            caminho_saida = os.path.join(pasta_saida, nome_arquivo)
            audio_60s.export(caminho_saida, format="wav")
            
            # Salvar o CSV de anotações
            nome_csv = f"audio_60s_{i+1:03d}.wav.csv"
            caminho_csv = os.path.join(pasta_saida, nome_csv)
            salvar_anotacoes_csv(anotacoes, caminho_csv)
            
            print(f"Áudio salvo: {nome_arquivo} (duração: {len(audio_60s)/1000:.1f}s)")
            print(f"Anotações salvas: {nome_csv} ({len(anotacoes)} vocalizações)")
        else:
            print(f"Erro ao criar áudio {i+1}")

def salvar_anotacoes_csv(anotacoes, caminho_csv):
    """
    Salva as anotações em um arquivo CSV
    
    Args:
        anotacoes (list): Lista de dicionários com onset_s, offset_s e label
        caminho_csv (str): Caminho para salvar o arquivo CSV
    """
    try:
        with open(caminho_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['onset_s', 'offset_s', 'label']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for anotacao in anotacoes:
                writer.writerow(anotacao)
                
    except Exception as e:
        print(f"Erro ao salvar CSV de anotações: {str(e)}")

def obter_label_do_caminho(caminho_vocalizacao):
    """
    Extrai o label baseado no nome da pasta da vocalização
    
    Args:
        caminho_vocalizacao (str): Caminho completo do arquivo de vocalização
    
    Returns:
        str: Label correspondente (m, v, n)
    """
    # Extrair o nome da pasta pai (tipo de vocalização)
    pasta_pai = os.path.basename(os.path.dirname(caminho_vocalizacao))
    
    # Mapear tipos para labels
    mapeamento_labels = {
        'pp': 'm',  # pp -> m
        'll': 'v',  # ll -> v
        'kp': 'n',  # kp -> n
        'pk': 'n',  # pk -> n
        'pr': 'w',  # pr -> w
        'rp': 'w'   # rp -> w
    }
    
    return mapeamento_labels.get(pasta_pai, 'u')  # 'u' como fallback

def criar_audio_individual(vocalizacoes, arquivos_background, duracao_alvo_ms):
    """
    Cria um único áudio de 60s com as vocalizações e intervalos de background
    
    Args:
        vocalizacoes (list): Lista de caminhos das vocalizações para este áudio
        arquivos_background (list): Lista de arquivos de background disponíveis
        duracao_alvo_ms (int): Duração alvo em milissegundos (60000 para 60s)
    
    Returns:
        tuple: (AudioSegment, list) - Áudio final de 60s e lista de anotações, ou (None, None) se houver erro
    """
    try:
        # Criar áudio base vazio
        audio_final = AudioSegment.silent(duration=0, frame_rate=48000)
        anotacoes = []  # Lista para armazenar as anotações
        
        # Carregar um áudio de background base para usar como template
        background_base = AudioSegment.from_wav(random.choice(arquivos_background))
        if background_base.frame_rate != 48000:
            background_base = background_base.set_frame_rate(48000)
        
        for i, caminho_vocalizacao in enumerate(vocalizacoes):
            try:
                # Carregar a vocalização
                vocalizacao = AudioSegment.from_wav(caminho_vocalizacao)
                if vocalizacao.frame_rate != 48000:
                    vocalizacao = vocalizacao.set_frame_rate(48000)
                
                # Registrar posição inicial da vocalização (em segundos)
                onset_s = len(audio_final) / 1000.0
                
                # Adicionar a vocalização
                audio_final += vocalizacao
                
                # Registrar posição final da vocalização (em segundos)
                offset_s = len(audio_final) / 1000.0
                
                # Obter label baseado no caminho
                label = obter_label_do_caminho(caminho_vocalizacao)
                
                # Adicionar anotação
                anotacoes.append({
                    'onset_s': round(onset_s, 3),
                    'offset_s': round(offset_s, 3),
                    'label': label
                })
                
                # Verificar se já atingimos a duração alvo
                if len(audio_final) >= duracao_alvo_ms:
                    break
                
                # Adicionar intervalo de background (exceto na última vocalização)
                if i < len(vocalizacoes) - 1:
                    # Gerar duração aleatória do intervalo (1-2s)
                    duracao_intervalo = random.randint(1000, 2000)
                    
                    # Verificar se o intervalo não vai ultrapassar o tempo limite
                    tempo_restante = duracao_alvo_ms - len(audio_final)
                    if tempo_restante <= 0:
                        break
                    
                    # Ajustar duração do intervalo se necessário
                    if duracao_intervalo > tempo_restante:
                        duracao_intervalo = tempo_restante
                    
                    # Pegar um segmento aleatório do background
                    background_segmento = obter_segmento_background_aleatorio(
                        arquivos_background, duracao_intervalo
                    )
                    
                    if background_segmento:
                        audio_final += background_segmento
                
            except Exception as e:
                print(f"Erro ao processar vocalização {os.path.basename(caminho_vocalizacao)}: {str(e)}")
                continue
        
        # Ajustar para exatamente 60s
        if len(audio_final) > duracao_alvo_ms:
            # Cortar se passou do tempo
            audio_final = audio_final[:duracao_alvo_ms]
            
            # Ajustar anotações que podem ter sido cortadas
            duracao_final_s = duracao_alvo_ms / 1000.0
            anotacoes_ajustadas = []
            for anotacao in anotacoes:
                if anotacao['onset_s'] < duracao_final_s:
                    # Se a vocalização começou antes do corte
                    if anotacao['offset_s'] > duracao_final_s:
                        # Se terminou depois do corte, ajustar o offset
                        anotacao['offset_s'] = duracao_final_s
                    anotacoes_ajustadas.append(anotacao)
            anotacoes = anotacoes_ajustadas
            
        elif len(audio_final) < duracao_alvo_ms:
            # Completar com background se necessário
            tempo_restante = duracao_alvo_ms - len(audio_final)
            background_final = obter_segmento_background_aleatorio(
                arquivos_background, tempo_restante
            )
            if background_final:
                audio_final += background_final
            
            # Se ainda não chegou a 60s, completar com silêncio
            if len(audio_final) < duracao_alvo_ms:
                silencio_restante = duracao_alvo_ms - len(audio_final)
                audio_final += AudioSegment.silent(duration=silencio_restante, frame_rate=48000)
        
        return audio_final, anotacoes
        
    except Exception as e:
        print(f"Erro ao criar áudio individual: {str(e)}")
        return None, None

def obter_segmento_background_aleatorio(arquivos_background, duracao_ms):
    """
    Obtém um segmento aleatório de background com a duração especificada
    
    Args:
        arquivos_background (list): Lista de arquivos de background
        duracao_ms (int): Duração desejada em milissegundos
    
    Returns:
        AudioSegment: Segmento de background ou None se houver erro
    """
    try:
        # Escolher arquivo de background aleatório
        arquivo_bg = random.choice(arquivos_background)
        background = AudioSegment.from_wav(arquivo_bg)
        
        if background.frame_rate != 48000:
            background = background.set_frame_rate(48000)
        
        # Se o background é menor que a duração desejada, repetir
        if len(background) < duracao_ms:
            repeticoes_necessarias = int(np.ceil(duracao_ms / len(background)))
            background = background * repeticoes_necessarias
        
        # Escolher ponto de início aleatório
        if len(background) > duracao_ms:
            inicio_max = len(background) - duracao_ms
            inicio = random.randint(0, inicio_max)
            segmento = background[inicio:inicio + duracao_ms]
        else:
            segmento = background
        
        return segmento
        
    except Exception as e:
        print(f"Erro ao obter segmento de background: {str(e)}")
        return None

if __name__ == "__main__":
    criar_audios_60s(
        pasta_overlaps='H:\\Users\\Firmino\\croped_vocal_overlap',
        pasta_background='H:\\Users\\Firmino\\croped_vocal_aves\\u',
        pasta_saida='H:\\Users\\Firmino\\croped_audios_60s',
        n_vocalizacoes=1500
    )
