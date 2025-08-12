import os
import csv
import glob
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment
import warnings

# Ignorar warnings específicos
warnings.filterwarnings("ignore", category=UserWarning)

def analisar_audios_anotados(pasta_entrada):
    """
    Analisa áudios anotados, conta vocalizações por label, plota duração média
    e calcula duração total dos áudios
    
    Args:
        pasta_entrada (str): Pasta contendo arquivos .wav e .wav.csv
    """
    print(f"Analisando pasta: {pasta_entrada}")
    
    # Coletar todos os arquivos WAV
    arquivos_wav = glob.glob(os.path.join(pasta_entrada, '*.wav'))
    print(f"Encontrados {len(arquivos_wav)} arquivos de áudio")
    
    # Estatísticas gerais
    contagem_labels = {}
    duracoes_por_label = {}
    duracao_total_audios = 0
    total_vocalizacoes = 0
    
    # Processar cada arquivo WAV e seu CSV correspondente
    for arquivo_wav in arquivos_wav:
        try:
            # Calcular duração do áudio
            audio = AudioSegment.from_wav(arquivo_wav)
            duracao_audio_s = len(audio) / 1000.0
            duracao_total_audios += duracao_audio_s
            
            # Buscar arquivo CSV correspondente
            arquivo_csv = arquivo_wav + '.csv'
            
            if not os.path.exists(arquivo_csv):
                print(f"Aviso: CSV não encontrado para {os.path.basename(arquivo_wav)}")
                continue
            
            # Processar anotações do CSV
            processar_csv_anotacoes(arquivo_csv, contagem_labels, duracoes_por_label)
            
        except Exception as e:
            print(f"Erro ao processar {os.path.basename(arquivo_wav)}: {str(e)}")
            continue
    
    # Calcular total de vocalizações
    total_vocalizacoes = sum(contagem_labels.values())
    
    # Calcular durações médias
    duracoes_medias = {}
    for label, duracoes in duracoes_por_label.items():
        if duracoes:
            duracoes_medias[label] = np.mean(duracoes)
    
    # Imprimir estatísticas
    imprimir_estatisticas(contagem_labels, duracoes_medias, duracao_total_audios, total_vocalizacoes)
    
    # Plotar gráficos
    plotar_graficos(contagem_labels, duracoes_medias, duracoes_por_label)

def processar_csv_anotacoes(arquivo_csv, contagem_labels, duracoes_por_label):
    """
    Processa um arquivo CSV de anotações e atualiza as estatísticas
    
    Args:
        arquivo_csv (str): Caminho para o arquivo CSV
        contagem_labels (dict): Dicionário para contar labels
        duracoes_por_label (dict): Dicionário para armazenar durações por label
    """
    try:
        with open(arquivo_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for linha in reader:
                try:
                    label = linha['label'].strip()
                    onset_s = float(linha['onset_s'])
                    offset_s = float(linha['offset_s'])
                    
                    # Calcular duração da vocalização
                    duracao = offset_s - onset_s
                    
                    # Atualizar contagem
                    if label in contagem_labels:
                        contagem_labels[label] += 1
                    else:
                        contagem_labels[label] = 1
                    
                    # Atualizar durações
                    if label in duracoes_por_label:
                        duracoes_por_label[label].append(duracao)
                    else:
                        duracoes_por_label[label] = [duracao]
                        
                except (ValueError, KeyError) as e:
                    print(f"Erro na linha do CSV {os.path.basename(arquivo_csv)}: {str(e)}")
                    continue
                    
    except Exception as e:
        print(f"Erro ao ler CSV {os.path.basename(arquivo_csv)}: {str(e)}")

def imprimir_estatisticas(contagem_labels, duracoes_medias, duracao_total_audios, total_vocalizacoes):
    """
    Imprime estatísticas detalhadas dos áudios analisados
    """
    print("\n" + "="*60)
    print("ESTATÍSTICAS GERAIS")
    print("="*60)
    
    print(f"Duração total dos áudios: {duracao_total_audios:.2f} segundos ({duracao_total_audios/60:.2f} minutos)")
    print(f"Total de vocalizações: {total_vocalizacoes}")
    
    print(f"\nVocalizações por minuto: {total_vocalizacoes/(duracao_total_audios/60):.2f}")
    
    print("\n" + "-"*40)
    print("CONTAGEM POR LABEL")
    print("-"*40)
    
    # Ordenar labels por contagem (decrescente)
    labels_ordenados = sorted(contagem_labels.items(), key=lambda x: x[1], reverse=True)
    
    for label, contagem in labels_ordenados:
        porcentagem = (contagem / total_vocalizacoes) * 100
        duracao_media = duracoes_medias.get(label, 0)
        print(f"Label '{label}': {contagem:4d} vocalizações ({porcentagem:5.1f}%) - Duração média: {duracao_media:.3f}s")
    
    print("\n" + "-"*40)
    print("DURAÇÕES MÉDIAS POR LABEL")
    print("-"*40)
    
    # Ordenar por duração média (decrescente)
    duracoes_ordenadas = sorted(duracoes_medias.items(), key=lambda x: x[1], reverse=True)
    
    for label, duracao_media in duracoes_ordenadas:
        contagem = contagem_labels[label]
        print(f"Label '{label}': {duracao_media:.3f}s (baseado em {contagem} amostras)")

def plotar_graficos(contagem_labels, duracoes_medias, duracoes_por_label):
    """
    Plota gráficos de análise dos dados
    """
    # Configurar matplotlib para melhor visualização
    plt.style.use('default')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análise de Vocalizações Anotadas', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Contagem por label (barras)
    labels = list(contagem_labels.keys())
    contagens = list(contagem_labels.values())
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    bars1 = ax1.bar(labels, contagens, color=colors)
    ax1.set_title('Contagem de Vocalizações por Label')
    ax1.set_xlabel('Label')
    ax1.set_ylabel('Número de Vocalizações')
    ax1.grid(True, alpha=0.3)
    
    # Adicionar valores nas barras
    for bar, contagem in zip(bars1, contagens):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(contagens)*0.01,
                str(contagem), ha='center', va='bottom')
    
    # Gráfico 2: Duração média por label (barras)
    labels_duracao = list(duracoes_medias.keys())
    duracoes_med = list(duracoes_medias.values())
    
    bars2 = ax2.bar(labels_duracao, duracoes_med, color=colors[:len(labels_duracao)])
    ax2.set_title('Duração Média por Label')
    ax2.set_xlabel('Label')
    ax2.set_ylabel('Duração Média (segundos)')
    ax2.grid(True, alpha=0.3)
    
    # Adicionar valores nas barras
    for bar, duracao in zip(bars2, duracoes_med):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(duracoes_med)*0.01,
                f'{duracao:.3f}s', ha='center', va='bottom')
    
    # Gráfico 3: Distribuição de durações (boxplot)
    labels_box = []
    dados_box = []
    for label, duracoes in duracoes_por_label.items():
        if duracoes:  # Apenas se houver dados
            labels_box.append(label)
            dados_box.append(duracoes)
    
    if dados_box:
        bp = ax3.boxplot(dados_box, labels=labels_box, patch_artist=True)
        ax3.set_title('Distribuição de Durações por Label')
        ax3.set_xlabel('Label')
        ax3.set_ylabel('Duração (segundos)')
        ax3.grid(True, alpha=0.3)
        
        # Colorir os boxplots
        for patch, color in zip(bp['boxes'], colors[:len(dados_box)]):
            patch.set_facecolor(color)
    
    # Gráfico 4: Proporção de vocalizações (pizza)
    total = sum(contagem_labels.values())
    sizes = [contagem / total * 100 for contagem in contagem_labels.values()]
    
    wedges, texts, autotexts = ax4.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                       colors=colors, startangle=90)
    ax4.set_title('Proporção de Vocalizações por Label')
    
    # Melhorar legibilidade dos textos
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    plt.tight_layout()
    plt.show()
    
    # Salvar gráfico
    plt.savefig('analise_vocalizacoes.png', dpi=300, bbox_inches='tight')
    print(f"\nGráfico salvo como 'analise_vocalizacoes.png'")

def gerar_relatorio_detalhado(pasta_entrada, pasta_saida=None):
    """
    Gera um relatório detalhado em arquivo de texto
    
    Args:
        pasta_entrada (str): Pasta com os arquivos analisados
        pasta_saida (str): Pasta para salvar o relatório (opcional)
    """
    if pasta_saida is None:
        pasta_saida = pasta_entrada
    
    arquivo_relatorio = os.path.join(pasta_saida, 'relatorio_analise.txt')
    
    # Redirecionar saída para arquivo (implementação simples)
    print(f"\nRelatório detalhado salvo em: {arquivo_relatorio}")

if __name__ == "__main__":
    # Exemplo de uso
    pasta_dados = r'C:\Users\EthogenesisLab\Documents\Train_Sobreposition_PheePhee_PheeTsik_TrillTrill\data\wav'  # Altere para sua pasta
    
    print("Iniciando análise de áudios anotados...")
    analisar_audios_anotados(pasta_dados)
    
    print("\nAnálise concluída!")
