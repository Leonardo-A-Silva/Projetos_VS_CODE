
editado para test de conexão
second alteration

import pygame
from pygame.locals import *
from sys import exit
#                                             Inicialização do pygame
pygame.init()

#                                             Criação da Tela do Jogo
largura = 640
altura = 480

tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("A Invasão do Império: O Despertar do Guardião - PBL")

#Definição de cores
PRETO = (0, 0, 0)
VERDE = (0, 255, 0)

#                                                Loop Principal do Jogo:
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
    pygame.display.update()

#       LOGICA DO JOGO ...
#       DESENHOS AQUI...
#       Desenha um Quadro verde (x, y, largura, altura)
#       Atualiza a tela
#       Encerra o pygame (pygame.quit())
