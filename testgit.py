
""""
#                                   função
def soma10(numero):
    numero = int(numero)
    numero = numero + 10
    return numero

#                                   programa principal
n = input("Digite um numero: ")
n = soma10(n)
print('Numero acrescido de 10: %d.' %n)

n = int()
def fatorial(n):
    fat = 1
    for i in range (2, n+1):
        fat = fat * i
    return fat

x = int(input("Numero : "))
print("fatorial : %d" % fatorial (x))
print(n)
"""
# bibliotecas 
import os    #busca altomatizada nas pastas e arquivos
import shutil #fazer transferencia de arquivos
import lasio    #importação de arquivos .las
    # !pip install lasio 
import numpy as np #estrutura
import pandas as pd #estrutura
import seaborn as sns   #graficos
import matplotlib.pyplot as plt #graficos

import warnings
warnings.filterwarnings ("ignore")

#from google.colab import drive
#drive.mount('/content/drive')

#caminho da pasta principal
caminho = r"C:\users\....."
#caminho do drive
#caminho = '/content/drive/....' 

# pasta de destino
destino = r"C:\users\....."
#destino = '/content/drive .....