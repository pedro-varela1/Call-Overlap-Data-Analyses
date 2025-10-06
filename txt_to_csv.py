import os
import glob

def txt_to_csv(input_folder="."):
    # Encontra todos os arquivos .txt no diretório
    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    
    for txt_file in txt_files:
        # Define o nome do arquivo CSV
        csv_file = txt_file.replace(".txt", ".wav.csv")
        
        with open(txt_file, 'r', encoding='utf-8') as infile:
            with open(csv_file, 'w', encoding='utf-8') as outfile:
                # Escreve o cabeçalho
                outfile.write("onset_s,offset_s,label\n")
                
                # Processa cada linha
                for line in infile:
                    line = line.strip()
                    if line:  # Ignora linhas vazias
                        # Substitui tabs e espaços por vírgulas
                        csv_line = line.replace('\t', ',').replace(' ', ',')
                        outfile.write(csv_line + '\n')
        
        print(f"Convertido: {txt_file} -> {csv_file}")

if __name__ == "__main__":
    txt_to_csv(r"C:\Users\EthogenesisLab\Downloads\Feitos_Feitos-20251005T222933Z-1-001\Feitos_Feitos")