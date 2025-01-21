import pygame
import random
import math

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 1540, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Защита Башни")

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 127)
BLUE = (100, 149, 237)
BLACK = (0, 0, 0)

# Загрузка изображений
try:
    background = pygame.image.load("images/background.png")
    player_image = pygame.image.load("images/player.png")
    enemy_image = pygame.image.load("images/enemy.png")
    tower_image = pygame.image.load("images/tower.png")
except Exception as e:
    print(f"Ошибка загрузки изображений: {e}")
    pygame.quit()
    exit()

pygame.mixer.init()
try:
    pygame.mixer.music.load("sounds/music.mp3")
    pygame.mixer.music.set_volume(0.5)  # Установка громкости (0.0 - 1.0)
    pygame.mixer.music.play(-1)  # -1 для бесконечного повторения
    hit_sound = pygame.mixer.Sound("sounds/music.mp3")
    defeat_sound = pygame.mixer.Sound("sounds/music.mp3")
except Exception as e:
    print(f"Ошибка загрузки музыки: {e}")

# Масштабирование спрайтов
player_image = pygame.transform.scale(player_image, (50, 50))  # Размер игрока 50x50
player_image_flipped = pygame.transform.flip(player_image, True, False)  # Зеркальное отображение
enemy_image = pygame.transform.scale(enemy_image, (40, 40))  # Размер врага 40x40
tower_image = pygame.transform.scale(tower_image, (100, 100))  # Размер башни 100x100

# Масштабирование фона на весь экран
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Игрок
player_rect = player_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
player_speed = 5
player_direction = "right"

# Башня
tower_rect = tower_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
tower_health = 100

# Враги
enemies = []
wave = 0  # Начинаем с нулевой волны
enemy_spawn_rate = 100  # Частота появления врагов в кадрах
enemy_speed = 2
max_enemies_per_wave = 5
current_wave_enemy_count = 0

# Деньги
money = 0

# Шрифт
try:
    font = pygame.font.Font("shrift.ttf", 32)  # Используем кастомный шрифт
except:
    font = pygame.font.Font(None, 36)  # Если шрифт не найден, используем стандартный

# Основной цикл игры
clock = pygame.time.Clock()
running = True
frame_count = 0
wave_active = False  # Изначально волна не активна
show_next_wave_text = True  # Показывать текст "Нажмите T"

# Текст для перехода на следующую волну
next_wave_text = font.render("Нажмите 'T' для начала волны", True, WHITE)
next_wave_text_rect = next_wave_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t and show_next_wave_text:
                wave += 1
                max_enemies_per_wave += 2
                enemy_speed += 0.2
                enemy_spawn_rate = max(20, enemy_spawn_rate - 5)
                current_wave_enemy_count = 0
                wave_active = True
                show_next_wave_text = False

    # Движение игрока
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and player_rect.top > 0:
        player_rect.y -= player_speed
    if keys[pygame.K_s] and player_rect.bottom < HEIGHT:
        player_rect.y += player_speed
    if keys[pygame.K_a] and player_rect.left > 0:
        player_rect.x -= player_speed
        player_direction = "left"
    if keys[pygame.K_d] and player_rect.right < WIDTH:
        player_rect.x += player_speed
        player_direction = "right"

    # Создание врагов
    if wave_active and frame_count % enemy_spawn_rate == 0 and current_wave_enemy_count < max_enemies_per_wave:
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            enemy_rect = enemy_image.get_rect(center=(random.randint(0, WIDTH), -50))
        elif side == "bottom":
            enemy_rect = enemy_image.get_rect(center=(random.randint(0, WIDTH), HEIGHT + 50))
        elif side == "left":
            enemy_rect = enemy_image.get_rect(center=(-50, random.randint(0, HEIGHT)))
        elif side == "right":
            enemy_rect = enemy_image.get_rect(center=(WIDTH + 50, random.randint(0, HEIGHT)))
        enemies.append({"rect": enemy_rect, "health": 2})  # Добавляем здоровье врага
        current_wave_enemy_count += 1

    # Движение врагов
    for enemy in enemies[:]:  # Используем срез, чтобы избежать ошибок при удалении
        dx = tower_rect.x - enemy["rect"].x
        dy = tower_rect.y - enemy["rect"].y
        distance = math.hypot(dx, dy)
        if distance > 0:
            enemy["rect"].x += min(enemy_speed, dx / distance)
            enemy["rect"].y += min(enemy_speed, dy / distance)

        # Проверка столкновения врага с башней
        if enemy["rect"].colliderect(tower_rect):
            tower_health -= 5
            enemies.remove(enemy)
            hit_sound.play()

        # Проверка столкновения игрока с врагом
        if enemy["rect"].colliderect(player_rect):
            enemy["health"] -= 1
            if enemy["health"] <= 0:
                money += 10
                enemies.remove(enemy)
                defeat_sound.play()

    # Проверка окончания волны
    if wave_active and not enemies and current_wave_enemy_count == max_enemies_per_wave:
        wave_active = False
        show_next_wave_text = True

    # Отрисовка
    screen.blit(background, (0, 0))  # Фон на весь экран
    screen.blit(tower_image, tower_rect)
    screen.blit(player_image_flipped if player_direction == "left" else player_image, player_rect)
    for enemy in enemies:
        screen.blit(enemy_image, enemy["rect"])
        # Полоска здоровья врага
        pygame.draw.rect(screen, BLACK, (enemy["rect"].x - 5, enemy["rect"].y - 10, 55, 11))  # Обводка
        pygame.draw.rect(screen, RED, (enemy["rect"].x - 3, enemy["rect"].y - 6, max(0, enemy["health"] * 25), 3))

    # Текст для перехода на следующую волну
    if show_next_wave_text:
        screen.blit(next_wave_text, next_wave_text_rect)

    # Полоска здоровья башни
    pygame.draw.rect(screen, BLACK, (tower_rect.x - 5, tower_rect.y - 20, 110, 20))  # Обводка
    pygame.draw.rect(screen, BLUE, (tower_rect.x, tower_rect.y - 15, max(0, tower_health), 10))

    # Отображение текста
    health_text = font.render(f"Здоровье башни: {tower_health}", True, RED)
    money_text = font.render(f"Деньги: {money}", True, RED)
    wave_text = font.render(f"Волна: {wave}", True, RED)
    enemies_left_text = font.render(f"Оставшиеся враги: {max_enemies_per_wave - current_wave_enemy_count}", True, RED)
    screen.blit(health_text, (10, 10))
    screen.blit(money_text, (10, 50))
    screen.blit(wave_text, (10, 90))
    screen.blit(enemies_left_text, (10, 130))

    pygame.display.flip()
    clock.tick(60)
    frame_count += 1

pygame.quit()
