"""
Com base no PBL (A Invasão do Império: O Despertar do Guardião), no Barema de avaliação e nos 6 Guias de Estudo de Pygame que você enviou, desenvolvi um código base completo e altamente modularizado.

Para garantir que você possa rodar o jogo imediatamente assim que copiar o código, eu utilizei blocos de cores (Surfaces) para representar os personagens. No entanto, deixei comentários explícitos e bem didáticos mostrando exatamente onde e como você deve substituir essas formas por imagens (.png) e como adicionar sons (.wav/.ogg), conforme ensinado nos seus Guias 2 e 6.

Estrutura do Código
O código está dividido em:

Configurações e Constantes: Cores, tamanhos, frames.

Sistema de Arquivos: Função pronta para salvar e ler Ranking em JSON (Guia 05).

Classes (Orientação a Objetos): Player, Enemy, Boss, Laser, Bacta (Item de cura). Tudo usando Grupos de Sprites (Guia 04).

Gerenciador do Jogo: Funções para os Menus e o Loop Principal (HUD, cronômetro e dificuldades).

Código Python (main.py)

"""

import pygame
import random
import json
import os

# ==========================================
# 1. CONFIGURAÇÕES INICIAIS (GUIA 1)
# ==========================================
pygame.init()

# Dimensões da tela
WIDTH = 800
HEIGHT = 600
FPS = 60

# Cores (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("A Invasão do Império: O Despertar do Guardião")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24, bold=True)
title_font = pygame.font.SysFont("arial", 48, bold=True)

# ==========================================
# 2. PERSISTÊNCIA DE DADOS (GUIA 5)
# ==========================================
RANKING_FILE = "ranking.json"

def load_ranking():
    if os.path.exists(RANKING_FILE):
        with open(RANKING_FILE, "r") as file:
            return json.load(file)
    return []

def save_ranking(score):
    ranking = load_ranking()
    ranking.append({"pontos": score})
    ranking = sorted(ranking, key=lambda x: x["pontos"], reverse=True)[:5] # Top 5
    with open(RANKING_FILE, "w") as file:
        json.dump(ranking, file, indent=4)

# ==========================================
# 3. CLASSES (SPRITES) (GUIAS 2 E 4)
# ==========================================

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # EXEMPLO DE EDIÇÃO: Para usar uma imagem real, comente a linha da Surface/fill e descomente a linha abaixo:
        # self.image = pygame.image.load("nave_guardiao.png").convert_alpha()
        self.image = pygame.Surface((40, 40))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 20
        self.speed = 5
        self.health = 3
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = 250 # Milissegundos entre tiros

    def update(self):
        # Movimentação em todas as direções (Guia 3 e Barema)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

        # Limites da tela
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WIDTH: self.rect.right = WIDTH
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT

    def shoot(self, all_sprites, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Laser(self.rect.centerx, self.rect.top, -10, YELLOW) # Tiro sobe (-y)
            all_sprites.add(bullet)
            bullets.add(bullet)
            # EXEMPLO: Para som de tiro (Guia 6):
            # som_tiro.play()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, difficulty_speed):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED) # Stormtrooper genérico
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(1, 3) + difficulty_speed
        self.health = 1

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT + 10: # Saiu da tela, recria lá em cima
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 4)

    def shoot(self, all_sprites, enemy_bullets):
        # Chance aleatória do inimigo atirar
        if random.random() > 0.99: 
            bullet = Laser(self.rect.centerx, self.rect.bottom, 5, RED) # Tiro desce (+y)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((80, 80))
        self.image.fill(PURPLE) # Darth Vader
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.y = -100
        self.speedx = 3
        self.health = 5 # Vader precisa de 5 acertos (Barema)
        self.damage = 2 # Dano duplo no jogador (Barema)

    def update(self):
        # Desce até o topo da tela, depois fica movendo para os lados
        if self.rect.y < 50:
            self.rect.y += 2
        else:
            self.rect.x += self.speedx
            if self.rect.right > WIDTH or self.rect.left < 0:
                self.speedx *= -1 # Inverte direção bate e volta

    def shoot(self, all_sprites, enemy_bullets):
        if random.random() > 0.96: # Chefe atira mais rápido
            bullet1 = Laser(self.rect.left + 20, self.rect.bottom, 7, RED)
            bullet2 = Laser(self.rect.right - 20, self.rect.bottom, 7, RED)
            all_sprites.add(bullet1, bullet2)
            enemy_bullets.add(bullet1, bullet2)

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, color):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = speed

    def update(self):
        self.rect.y += self.speedy
        # Mata o tiro se sair da tela
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

class Bacta(pygame.sprite.Sprite): # Item de Vida (Barema)
    def __init__(self, center):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 3

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

# ==========================================
# 4. INTERFACE E TELAS (HUD E MENUS)
# ==========================================

def draw_text(surf, text, size, x, y, color=WHITE):
    msg = font.render(text, True, color)
    rect = msg.get_rect()
    rect.midtop = (x, y)
    surf.blit(msg, rect)

def draw_health_bar(surf, x, y, pct):
    if pct < 0: pct = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 15
    fill = (pct / 3) * BAR_LENGTH # 3 vidas é o máximo/inicial
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)

# ==========================================
# 5. LOOP PRINCIPAL (MÁQUINA DE ESTADOS)
# ==========================================
def main():
    game_state = "MENU"
    difficulty = 0 # 0=Fácil, 1=Médio, 2=Difícil
    score = 0
    boss_spawned = False
    start_ticks = 0

    # Grupos de Sprites
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group() # Tiros do player
    enemy_bullets = pygame.sprite.Group() # Tiros dos inimigos
    items = pygame.sprite.Group()
    
    player = Player()

    def reset_game():
        nonlocal score, boss_spawned, start_ticks
        all_sprites.empty()
        enemies.empty()
        bullets.empty()
        enemy_bullets.empty()
        items.empty()
        player.rect.centerx = WIDTH // 2
        player.rect.bottom = HEIGHT - 20
        player.health = 3
        score = 0
        boss_spawned = False
        all_sprites.add(player)
        start_ticks = pygame.time.get_ticks()

        # Cria inimigos iniciais
        for i in range(8):
            e = Enemy(difficulty)
            all_sprites.add(e)
            enemies.add(e)

    running = True
    while running:
        clock.tick(FPS)
        
        # 1. CAPTURA DE EVENTOS GERAIS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Controles de Menu
            if game_state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: # Start Fácil
                        difficulty = 0
                        reset_game()
                        game_state = "PLAYING"
                    if event.key == pygame.K_2: # Start Difícil
                        difficulty = 2
                        reset_game()
                        game_state = "PLAYING"
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            elif game_state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        player.shoot(all_sprites, bullets)
                    if event.key == pygame.K_ESCAPE:
                        game_state = "PAUSE"
            
            elif game_state == "PAUSE":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c: # Continuar
                        game_state = "PLAYING"
                    if event.key == pygame.K_m: # Voltar ao menu
                        game_state = "MENU"

            elif game_state in ["GAMEOVER", "VICTORY"]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        game_state = "MENU"

        # 2. LÓGICA DO JOGO (UPDATE)
        if game_state == "PLAYING":
            all_sprites.update()
            for e in enemies:
                e.shoot(all_sprites, enemy_bullets)

            # Spawn do Boss (Darth Vader) ao atingir 200 pontos
            if score >= 200 and not boss_spawned:
                boss_spawned = True
                for e in enemies: e.kill() # Limpa os stormtroopers
                boss = Boss()
                all_sprites.add(boss)
                enemies.add(boss)

            # COLISÕES (Guia 4)
            # A) Tiro do Player acerta Inimigo
            hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
            for enemy, bullet_list in hits.items():
                enemy.health -= 1
                if enemy.health <= 0:
                    enemy.kill()
                    # Verifica se era o Boss
                    if isinstance(enemy, Boss):
                        score += 200
                        save_ranking(score)
                        game_state = "VICTORY"
                    else:
                        score += 10
                        # Chance de dropar item de vida
                        if random.random() > 0.85:
                            item = Bacta(enemy.rect.center)
                            all_sprites.add(item)
                            items.add(item)
                        # Repõe inimigo normal se boss não spawnou
                        if not boss_spawned:
                            e = Enemy(difficulty)
                            all_sprites.add(e)
                            enemies.add(e)

            # B) Inimigos ou tiros inimigos acertam o Player
            damage_hits = pygame.sprite.spritecollide(player, enemies, True)
            bullet_hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
            
            for hit in damage_hits + bullet_hits:
                if isinstance(hit, Boss):
                    player.health -= 2 # Dano do Vader (Barema)
                else:
                    player.health -= 1
                
                if player.health <= 0:
                    save_ranking(score)
                    game_state = "GAMEOVER"

            # C) Player pega item de cura
            item_hits = pygame.sprite.spritecollide(player, items, True)
            for hit in item_hits:
                if player.health < 3: # Limita a vida em 3
                    player.health += 1

        # 3. RENDERIZAÇÃO (DRAW)
        screen.fill(BLACK) # Fundo do espaço

        if game_state == "MENU":
            draw_text(screen, "A Invasão do Império", 48, WIDTH//2, HEIGHT//4, YELLOW)
            draw_text(screen, "Aperte [1] para Nível Fácil", 24, WIDTH//2, HEIGHT//2)
            draw_text(screen, "Aperte [2] para Nível Difícil", 24, WIDTH//2, HEIGHT//2 + 40)
            draw_text(screen, "Aperte [ESC] para Sair", 24, WIDTH//2, HEIGHT//2 + 80)
            
            # Exibir Ranking simples
            top = load_ranking()
            if top:
                draw_text(screen, f"Recorde Atual: {top[0]['pontos']} pts", 24, WIDTH//2, HEIGHT - 50, GREEN)

        elif game_state == "PLAYING":
            all_sprites.draw(screen)
            
            # HUD (Barema)
            draw_text(screen, f"Score: {score}", 24, 60, 10)
            draw_text(screen, "Vida:", 24, WIDTH - 160, 10)
            draw_health_bar(screen, WIDTH - 110, 15, player.health)
            
            # Cronômetro (mm:ss)
            seconds = (pygame.time.get_ticks() - start_ticks) // 1000
            mins = seconds // 60
            secs = seconds % 60
            draw_text(screen, f"Tempo: {mins:02}:{secs:02}", 24, WIDTH // 2, 10)

        elif game_state == "PAUSE":
            draw_text(screen, "PAUSADO", 48, WIDTH//2, HEIGHT//3, YELLOW)
            draw_text(screen, "Aperte [C] para Continuar", 24, WIDTH//2, HEIGHT//2)
            draw_text(screen, "Aperte [M] para Voltar ao Menu", 24, WIDTH//2, HEIGHT//2 + 40)

        elif game_state == "GAMEOVER":
            draw_text(screen, "GAME OVER", 48, WIDTH//2, HEIGHT//3, RED)
            draw_text(screen, f"Pontuação Final: {score}", 24, WIDTH//2, HEIGHT//2)
            draw_text(screen, "Aperte [ENTER] para Menu Principal", 24, WIDTH//2, HEIGHT//2 + 60)

        elif game_state == "VICTORY":
            draw_text(screen, "VITÓRIA! A BASE ESTÁ SALVA!", 48, WIDTH//2, HEIGHT//3, GREEN)
            draw_text(screen, f"Darth Vader foi derrotado! Pontuação: {score}", 24, WIDTH//2, HEIGHT//2)
            draw_text(screen, "Aperte [ENTER] para Menu Principal", 24, WIDTH//2, HEIGHT//2 + 60)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

"""
O que você deve editar (Dicas Práticas):
Gráficos: Na pasta do seu projeto, salve as imagens (ex: nave.png, vader.png). 
No código, vá na classe do personagem (ex: Player), apague a linha self.image = pygame.Surface((40, 40)) e ative a linha de cima substituindo o nome do arquivo da imagem. 
Você pode precisar redimensionar a imagem usando pygame.transform.scale().
Sons e Música (Guia 6): Crie uma pasta sons. 
No início do bloco main() inicialize a música com pygame.mixer.music.load('sons/fundo.ogg') e pygame.mixer.music.play(-1).

Mecânica de Onda (Barema): O jogo atual pausa os stormtroopers e invoca o Darth Vader ao chegar nos 200 pontos. 
Se quiser prolongar o jogo para testar, altere o valor de score >= 200 no bloco update para 500 ou 1000.
"""