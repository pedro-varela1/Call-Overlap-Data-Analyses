# Sobreposition - Pipeline de Geração de Dados para Classificação de Sobreposições Vocais

Este repositório implementa um pipeline completo para gerar dados de treinamento para redes neurais que classificam sobreposições de vocalizações. O objetivo é criar variabilidade artificial de sobreposições vocais a partir de dados originais anotados.

## 📋 Visão Geral

O pipeline processa áudios originais com anotações temporais e cria datasets sintéticos com sobreposições controladas para treinamento de modelos de classificação. Todo o processo é projetado para maximizar a variabilidade dos dados mantendo a qualidade e precisão das anotações.

## 🚀 Pipeline de Execução

Execute os scripts na seguinte ordem:

```bash
1. python crop.py          # Extração de segmentos
2. python overlap.py       # Criação de sobreposições
3. python combine_60s.py   # Montagem de áudios longos
4. python analyze_annotations.py  # Análise dos resultados
```

---

## 📁 Estrutura de Dados

### Entrada Inicial
```
J:\ALL_DATA\
├── audio1.wav
├── audio1.wav.csv
├── audio2.wav
├── audio2.wav.csv
└── ...
```

### Dados Processados
```
J:\croped_vocal\
├── p\          # Vocalizações tipo 'p'
├── l\          # Vocalizações tipo 'l'
├── k\          # Vocalizações tipo 'k'
├── g\          # Vocalizações tipo 'g'
├── r\          # Vocalizações tipo 'r'
├── e\          # Vocalizações tipo 'e'
├── s\          # Vocalizações tipo 's'
└── u\          # Áudios de background (sem vocalizações)
```

### Sobreposições Geradas
```
J:\overlap_especificos\
├── ll\         # Sobreposições l+l
├── pp\         # Sobreposições p+p
├── kp\         # Sobreposições k+p
└── w\          # Sobreposições aleatórias
```

### Dataset Final
```
J:\audios_60s\
├── audio_60s_001.wav
├── audio_60s_001.wav.csv
├── audio_60s_002.wav
├── audio_60s_002.wav.csv
└── ...
```

---

## 🔧 Etapas Detalhadas

### 1️⃣ **crop.py** - Extração de Segmentos Vocais

**Objetivo**: Extrai segmentos individuais de vocalizações e background dos áudios originais.

**Funcionalidades**:
- **`cortar_audios()`**: Extrai vocalizações específicas (p, l, k, g, r, e, s) baseadas nas anotações CSV
- **`cortar_background()`**: Cria áudios de background removendo todas as vocalizações

**Parâmetros importantes**:
- `pasta_entrada`: Diretório com áudios originais e CSVs
- `pasta_saida`: Diretório para salvar segmentos extraídos
- `labels`: Lista de tipos de vocalizações a extrair

**Exemplo de uso**:
```python
# Extrair vocalizações
cortar_audios('J:\\ALL_DATA', 'J:\\croped_vocal', ['p', 'l', 'k', 'g', 'r', 'e', 's'])

# Extrair background
cortar_background('J:\\ALL_DATA', 'J:\\croped_vocal')
```

**Output**: Segmentos de áudio organizados por tipo de vocalização, todos em 48kHz.

---

### 2️⃣ **overlap.py** - Criação de Sobreposições

**Objetivo**: Gera sobreposições artificiais entre pares específicos de vocalizações com variabilidade controlada.

**Funcionalidades**:
- Cria sobreposições para pares específicos (ll, pp, kp)
- Gera sobreposições aleatórias com vocalizações não utilizadas
- Aplica redução de amplitude variável (0.1-0.2) aleatoriamente
- Produz espectrogramas para cada sobreposição

**Características técnicas**:
- **Taxa de redução variável**: Entre 0.1 e 0.2 (aleatória para cada par)
- **Posicionamento aleatório**: Sobreposições em pontos temporais aleatórios
- **Sem reutilização**: Cada arquivo é usado apenas uma vez
- **Limitação por tipo**: Máximo de N sobreposições por tipo (default: 1000)

**Parâmetros importantes**:
- `pasta_labels`: Diretório com vocalizações extraídas
- `pasta_saida`: Diretório para salvar sobreposições
- `pares_vocalizacoes`: Lista de pares desejados (ex: [["l","l"], ["p","p"], ["k","p"]])
- `taxa_reducao_min/max`: Faixa de redução de amplitude
- `n`: Número máximo de sobreposições por tipo

**Exemplo de uso**:
```python
pares_desejados = [["l", "l"], ["p", "p"], ["k", "p"]]
criar_pares_com_overlap_e_espectrograma(
    'J:\\croped_vocal', 
    'J:\\overlap_especificos', 
    pares_desejados, 
    taxa_reducao_min=0.1,
    taxa_reducao_max=0.2,
    n=1000
)
```

**Output**: Sobreposições organizadas por tipo + espectrogramas correspondentes.

---

### 3️⃣ **combine_60s.py** - Montagem de Áudios Longos

**Objetivo**: Combina sobreposições em áudios contínuos de 60 segundos com intervalos de background naturais.

**Funcionalidades**:
- Distribui sobreposições aleatoriamente em áudios de 60s
- Insere intervalos de background (1-2s) entre vocalizações
- Gera CSVs de anotação com timestamps precisos
- Mapeia tipos para labels específicos (pp→m, ll→v, kp/pk→n)

**Características técnicas**:
- **Duração fixa**: Exatamente 60 segundos por áudio
- **Intervalos aleatórios**: 1-2 segundos de background entre vocalizações
- **Distribuição equilibrada**: Todas as sobreposições são utilizadas
- **Anotações precisas**: Timestamps com precisão de milissegundos

**Mapeamento de labels**:
```python
pp → m  # Sobreposições p+p
ll → v  # Sobreposições l+l
kp → n  # Sobreposições k+p ou p+k
pk → n  # Sobreposições p+k ou k+p
w  → w  # Sobreposições aleatórias
```

**Parâmetros importantes**:
- `pasta_overlaps`: Diretório com sobreposições geradas
- `pasta_background`: Diretório com áudios de background
- `pasta_saida`: Diretório para áudios finais de 60s
- `n_vocalizacoes`: Número máximo de vocalizações por tipo a usar

**Exemplo de uso**:
```python
criar_audios_60s(
    pasta_overlaps='J:\\overlap_especificos',
    pasta_background='J:\\croped_vocal\\u',
    pasta_saida='J:\\audios_60s',
    n_vocalizacoes=500
)
```

**Output**: Áudios de 60s + CSVs de anotação correspondentes.

---

### 4️⃣ **analyze_annotations.py** - Análise dos Resultados

**Objetivo**: Analisa estatisticamente o dataset final gerado e produz visualizações.

**Funcionalidades**:
- Conta vocalizações por tipo de label
- Calcula durações médias e distribuições
- Computa duração total do dataset
- Gera gráficos de análise (barras, boxplots, pizza)

**Métricas calculadas**:
- Contagem total de vocalizações por label
- Duração média por tipo de vocalização
- Distribuição estatística de durações
- Taxa de vocalizações por minuto
- Duração total do dataset

**Visualizações geradas**:
1. **Gráfico de barras**: Contagem por label
2. **Gráfico de barras**: Duração média por label
3. **Boxplot**: Distribuição de durações
4. **Gráfico pizza**: Proporção de vocalizações

**Exemplo de uso**:
```python
analisar_audios_anotados('J:\\audios_60s')
```

**Output**: Estatísticas no console + gráfico salvo como 'analise_vocalizacoes.png'.

---

## 📊 Formato dos CSVs de Anotação

Todos os CSVs seguem o formato padrão:

```csv
onset_s,offset_s,label
0.000,1.234,m
2.456,3.789,v
5.123,6.456,n
```

**Colunas**:
- `onset_s`: Início da vocalização em segundos
- `offset_s`: Fim da vocalização em segundos  
- `label`: Tipo da vocalização (m, v, n, w)

---

## ⚙️ Configurações e Parâmetros

### Parâmetros Globais
- **Sample Rate**: 48kHz (todos os áudios)
- **Duração alvo**: 60 segundos (áudios finais)
- **Intervalos background**: 1-2 segundos (aleatório)

### Parâmetros Ajustáveis

**crop.py**:
- Labels a extrair: `['p', 'l', 'k', 'g', 'r', 'e', 's']`

**overlap.py**:
- Pares de sobreposição: `[["l", "l"], ["p", "p"], ["k", "p"]]`
- Taxa de redução: `0.1` a `0.2` (aleatória)
- Máximo por tipo: `n=1000`

**combine_60s.py**:
- Vocalizações por tipo: `n_vocalizacoes=500`
- Duração dos áudios: `60s` (fixo)

---

## 🎯 Uso para Treinamento de IA

### Dataset Gerado
- **Áudios**: Arquivos WAV de 60s com sobreposições variadas
- **Anotações**: CSVs com timestamps precisos para supervisão
- **Variabilidade**: Amplitudes, posições e combinações aleatórias
- **Balanceamento**: Distribuição controlada entre tipos

### Aplicações
1. **Classificação de sobreposições**: Treinar modelos para identificar tipos de sobreposição
2. **Detecção temporal**: Identificar início/fim de vocalizações sobrepostas
3. **Segmentação**: Separar componentes individuais de sobreposições
4. **Análise de padrões**: Estudar características de diferentes tipos de overlap

---

## 📝 Notas Importantes

- **Ordem obrigatória**: Execute sempre na sequência crop.py → overlap.py → combine_60s.py
- **Paths configuráveis**: Ajuste os caminhos nos scripts conforme sua estrutura
- **Recursos**: Pipeline pode ser intensivo em CPU/disco para grandes datasets
- **Qualidade**: Todos os áudios mantêm qualidade de 48kHz throughout the pipeline

---

## 🔍 Exemplo Completo de Execução

```python
# 1. Extrair segmentos dos áudios originais
from crop import cortar_audios, cortar_background

cortar_audios('J:\\ALL_DATA', 'J:\\croped_vocal', ['p', 'l', 'k', 'g', 'r', 'e', 's'])
cortar_background('J:\\ALL_DATA', 'J:\\croped_vocal')

# 2. Criar sobreposições variadas
from overlap import criar_pares_com_overlap_e_espectrograma

pares_desejados = [["l", "l"], ["p", "p"], ["k", "p"]]
criar_pares_com_overlap_e_espectrograma(
    'J:\\croped_vocal', 
    'J:\\overlap_especificos', 
    pares_desejados, 
    taxa_reducao_min=0.1,
    taxa_reducao_max=0.2,
    n=1000
)

# 3. Combinar em áudios de 60s
from combine_60s import criar_audios_60s

criar_audios_60s(
    pasta_overlaps='J:\\overlap_especificos',
    pasta_background='J:\\croped_vocal\\u',
    pasta_saida='J:\\audios_60s',
    n_vocalizacoes=500
)

# 4. Analisar resultados
from analyze_annotations import analisar_audios_anotados

analisar_audios_anotados('J:\\audios_60s')
```

---

## 🏗️ Arquitetura do Sistema

```mermaid
graph LR
    A[Áudios Originais + CSVs] --> B[crop.py]
    B --> C[Segmentos por Tipo]
    C --> D[overlap.py] 
    D --> E[Sobreposições Variadas]
    E --> F[combine_60s.py]
    F --> G[Dataset 60s Anotado]
    G --> H[analyze_annotations.py]
    H --> I[Estatísticas + Gráficos]
```

Este pipeline garante a criação de um dataset robusto e variado para treinamento efetivo de modelos de classificação de sobreposições vocais.
