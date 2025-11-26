import os
import random
import glob
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
from pydub import AudioSegment
import warnings
from itertools import combinations

# Ignorar warnings específicos do Librosa
warnings.filterwarnings("ignore", category=UserWarning)

def criar_pares_com_overlap_e_espectrograma(pasta_labels, pasta_saida, pares_vocalizacoes, taxa_reducao=None, n=1000):
    """
    Cria pares de áudios com sobreposição baseados em tipos de vocalizações específicos
    
    Args:
        pasta_labels (str): Pasta com os áudios cortados das labels (cada label em sua pasta)
        pasta_saida (str): Pasta para salvar os áudios combinados e espectrogramas
        pares_vocalizacoes (list): Lista de pares de vocalizações ex: [["l", "l"],["p","p"],["k","p"]]
        taxa_reducao (dict): Dicionário com taxas de redução por label. 
                            Keys: labels (ex: "p", "l", "k")
                            Values: tuples (min, max) ou None para não aplicar redução
                            Exemplo: {"p": (0.15, 0.2), "l": (0.1, 0.15), "k": None}
        n (int): Número máximo de overlaps para cada tipo de vocalização (default: 1000)
    """
    # Inicializar taxa_reducao como dict vazio se None
    if taxa_reducao is None:
        taxa_reducao = {}
    # Garantir que a pasta de saída existe
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Coletar todos os arquivos por label
    arquivos_por_label = {}
    for label_pasta in os.listdir(pasta_labels):
        # Pule a pasta "u"
        if label_pasta == "u":
            continue
        caminho_label = os.path.join(pasta_labels, label_pasta)
        if os.path.isdir(caminho_label):
            arquivos = glob.glob(os.path.join(caminho_label, '*.wav'))
            if arquivos:
                arquivos_por_label[label_pasta] = arquivos
    
    # Processar cada par específico de vocalizações
    arquivos_usados = set()  # Para tracking dos arquivos já usados (não podem ser reutilizados)
    
    for par in pares_vocalizacoes:
        label1, label2 = par
        nome_pasta = f"{label1}{label2}"
        
        # Criar pasta para este tipo de overlap
        pasta_overlap = os.path.join(pasta_saida, nome_pasta)
        os.makedirs(pasta_overlap, exist_ok=True)
        
        # Verificar se as labels existem
        if label1 not in arquivos_por_label or label2 not in arquivos_por_label:
            print(f"Aviso: Labels {label1} ou {label2} não encontradas. Pulando par.")
            continue
        
        # Criar todos os pares possíveis sem repetição, excluindo arquivos já usados
        arquivos1 = [arq for arq in arquivos_por_label[label1] if arq not in arquivos_usados]
        arquivos2 = [arq for arq in arquivos_por_label[label2] if arq not in arquivos_usados]
        
        pares_possiveis = []
        
        if label1 == label2:
            # Mesmo label: usar combinações sem repetição
            pares_possiveis = list(combinations(arquivos1, 2))
        else:
            # Labels diferentes: produto cartesiano
            for arq1 in arquivos1:
                for arq2 in arquivos2:
                    pares_possiveis.append((arq1, arq2))
        
        # Processar cada par possível (limitado a n overlaps)
        if len(pares_possiveis) > n:
            pares_selecionados = random.sample(pares_possiveis, n)
        else:
            pares_selecionados = pares_possiveis
        
        print(f"Processando {len(pares_selecionados)} overlaps para {nome_pasta} (de {len(pares_possiveis)} possíveis)")
        
        for arq1, arq2 in pares_selecionados:
            # Marcar os arquivos como usados (não podem ser reutilizados)
            arquivos_usados.add(arq1)
            arquivos_usados.add(arq2)
            
            # Escolher aleatoriamente qual áudio começa primeiro
            if random.random() < 0.5:
                arq1, arq2 = arq2, arq1
            
            # Processar o overlap com taxa de redução específica
            processar_overlap(arq1, arq2, pasta_overlap, label1, label2, taxa_reducao)
    
    # Criar pasta 'w' com overlaps aleatórios não utilizados
    if n > 0:
        criar_overlaps_aleatorios(arquivos_por_label, pasta_saida, arquivos_usados, taxa_reducao, n)

def criar_overlaps_aleatorios(arquivos_por_label, pasta_saida, arquivos_usados, taxa_reducao, n):
    """
    Cria overlaps aleatórios usando apenas arquivos que não foram utilizados anteriormente
    """
    pasta_outros = os.path.join(pasta_saida, 'w')
    os.makedirs(pasta_outros, exist_ok=True)
    
    # Coletar todos os arquivos disponíveis que não foram usados
    arquivos_disponiveis = []
    arquivos_por_arquivo = {}  # Mapeia arquivo para sua label
    for label, arquivos in arquivos_por_label.items():
        for arquivo in arquivos:
            if arquivo not in arquivos_usados:
                arquivos_disponiveis.append(arquivo)
                arquivos_por_arquivo[arquivo] = label
    
    print(f"Arquivos disponíveis para overlaps aleatórios: {len(arquivos_disponiveis)}")
    
    # Verificar se temos arquivos suficientes para criar pares
    if len(arquivos_disponiveis) < 2:
        print("Não há arquivos suficientes disponíveis para criar overlaps aleatórios.")
        return
    
    # Criar lista de todos os pares possíveis com arquivos disponíveis
    pares_disponiveis = list(combinations(arquivos_disponiveis, 2))
    
    # Selecionar N pares aleatórios
    n_disponiveis = min(n, len(pares_disponiveis))
    pares_selecionados = random.sample(pares_disponiveis, n_disponiveis)
    
    print(f"Criando {n_disponiveis} overlaps aleatórios na pasta 'w'")
    
    # Processar cada par selecionado
    for arq1, arq2 in pares_selecionados:
        # Escolher aleatoriamente qual áudio começa primeiro
        if random.random() < 0.5:
            arq1, arq2 = arq2, arq1
        
        # Obter as labels dos arquivos
        label1 = arquivos_por_arquivo[arq1]
        label2 = arquivos_por_arquivo[arq2]
        processar_overlap(arq1, arq2, pasta_outros, label1, label2, taxa_reducao)

def processar_overlap(arq1, arq2, pasta_destino, label1, label2, taxa_reducao):
    """
    Processa um único overlap entre dois arquivos de áudio com taxa de redução baseada na label
    
    Args:
        arq1 (str): Caminho do primeiro arquivo de áudio
        arq2 (str): Caminho do segundo arquivo de áudio
        pasta_destino (str): Pasta de destino para salvar os arquivos
        label1 (str): Label do primeiro arquivo
        label2 (str): Label do segundo arquivo
        taxa_reducao (dict): Dicionário com taxas de redução por label
    """
    try:
        # Carregar os áudios
        audio1 = AudioSegment.from_wav(arq1)
        audio2 = AudioSegment.from_wav(arq2)
        
        duracao1 = len(audio1)
        duracao2 = len(audio2)
        
        # Determinar qual áudio será reduzido baseado nas regras específicas
        reduzir_audio1 = False
        reduzir_audio2 = False
        label_para_reducao = None
        
        if label1 == label2:
            # Mesmo label: aplicar regras específicas
            if label1 == "l":
                # Para "l", reduzir o de menor duração
                if duracao1 < duracao2:
                    reduzir_audio1 = True
                    label_para_reducao = label1
                else:
                    reduzir_audio2 = True
                    label_para_reducao = label2
            elif label1 == "p":
                # Para "p", reduzir o de maior duração
                if duracao1 > duracao2:
                    reduzir_audio1 = True
                    label_para_reducao = label1
                else:
                    reduzir_audio2 = True
                    label_para_reducao = label2
            else:
                # Para outros pares iguais, usar a lógica antiga (reduzir audio2)
                reduzir_audio2 = True
                label_para_reducao = label2
        else:
            # Labels diferentes: reduzir audio2 (lógica original)
            reduzir_audio2 = True
            label_para_reducao = label2
        
        # Aplicar redução ao áudio escolhido
        taxa_str = "noReduc"
        if label_para_reducao and label_para_reducao in taxa_reducao and taxa_reducao[label_para_reducao] is not None:
            taxa_reducao_min, taxa_reducao_max = taxa_reducao[label_para_reducao]
            # Gerar taxa de redução aleatória dentro da faixa especificada
            taxa_red = random.uniform(taxa_reducao_min, taxa_reducao_max)
            reducao_db = 20 * np.log10(taxa_red)  # Conversão linear para dB
            
            if reduzir_audio1:
                audio1 = audio1 + reducao_db
            elif reduzir_audio2:
                audio2 = audio2 + reducao_db
            
            taxa_str = f"{taxa_red:.3f}".replace('.', 'p')  # Usar a taxa específica com 3 casas decimais
        
        # Escolher ponto de início aleatório para sobreposição (dentro do primeiro áudio)
        max_inicio = duracao1 - 1  # Garante pelo menos 1ms de sobreposição
        inicio_overlap = random.randint(0, max_inicio) if max_inicio > 0 else 0
        
        # Calcular duração total necessária
        duracao_total = max(duracao1, inicio_overlap + duracao2)
        
        # Criar áudio base (silêncio) com a duração total
        base = AudioSegment.silent(duration=duracao_total, frame_rate=48000)
        
        # Adicionar o primeiro áudio no início
        base = base.overlay(audio1, position=0)
        
        # Adicionar o segundo áudio com redução na posição escolhida
        base = base.overlay(audio2, position=inicio_overlap)
        
        # Gerar nome do arquivo de saída
        nome1 = os.path.splitext(os.path.basename(arq1))[0]
        nome2 = os.path.splitext(os.path.basename(arq2))[0]
        nome_base = f"{nome1}_{nome2}_{taxa_str}"
        nome_audio = nome_base + ".wav"
        caminho_audio = os.path.join(pasta_destino, nome_audio)
        
        # Exportar áudio combinado
        base.export(caminho_audio, format="wav")
        
        # Gerar e salvar espectrograma
        gerar_espectrograma(caminho_audio, pasta_destino, nome_base)
        
    except Exception as e:
        print(f"Erro ao processar overlap entre {os.path.basename(arq1)} e {os.path.basename(arq2)}: {str(e)}")

def gerar_espectrograma(caminho_audio, pasta_saida, nome_base):
    """
    Gera e salva um espectrograma a partir de um arquivo de áudio
    
    Args:
        caminho_audio (str): Caminho completo para o arquivo de áudio
        pasta_saida (str): Pasta para salvar o espectrograma
        nome_base (str): Nome base para o arquivo de saída (sem extensão)
    """
    try:
        # Carregar o áudio com Librosa
        y, sr = librosa.load(caminho_audio, sr=None)
        
        # Criar figura para o espectrograma
        plt.figure(figsize=(10, 4))
        
        # Gerar espectrograma Mel
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=18000, n_fft=2048, hop_length=128, fmin=1000)
        S_dB = librosa.power_to_db(S, ref=np.max)
        
        # Plotar espectrograma
        librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', fmax=18000, fmin=1000)
        plt.colorbar(format='%+2.0f dB')
        plt.title(f'Espectrograma: {nome_base}')
        
        # Salvar e fechar a figura
        caminho_imagem = os.path.join(pasta_saida, f"{nome_base}.png")
        plt.savefig(caminho_imagem, bbox_inches='tight', dpi=150)
        plt.close()
        
    except Exception as e:
        print(f"Erro ao gerar espectrograma para {nome_base}: {str(e)}")

if __name__ == "__main__":
    # pares_desejados = [["l", "l"], ["p", "p"], ["k", "p"]]
    pares_desejados = [["p", "r_plus"]]
    
    # Definir taxas de redução por label
    taxas_reducao = {
        "p": (0.1, 0.2),
        "l": (0.6, 0.7),
        "k": (0.6, 0.7),
        "r_plus": (0.6, 0.7)
        # Labels não incluídas ou com valor None não terão redução aplicada
    }
    
    criar_pares_com_overlap_e_espectrograma(
        'J:\\croped_vocal_adult_baby', 
        'H:\\Users\\Firmino\\croped_vocal_overlap', 
        pares_desejados, 
        taxa_reducao=taxas_reducao,
        n=1500
    )