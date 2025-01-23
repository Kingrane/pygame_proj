import pygame
import random
import math
import sys

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
YELLOW = (255, 255, 0)
DARK_GREEN = (0, 100, 0)
ORANGE = (255, 165, 0)


# Загрузка изображений
def load_image(name):
    try:
        image = pygame.image.load(name).convert_alpha()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)
    return image


try:
    background = pygame.transform.scale(load_image("images/background1.png"), (WIDTH, HEIGHT))
    player_sprite_sheet = load_image("images/player_walk.png")
    enemy_image = pygame.transform.scale(load_image("images/enemy.png"), (40, 40))
    tower_image = pygame.transform.scale(load_image("images/tower.png"), (130, 130))
    attack_image = pygame.transform.scale(load_image("images/sword3.png"), (70, 70))
except Exception as e:
    print(f"Ошибка загрузки изображений: {e}")
    pygame.quit()
    exit()

# Размеры кадра спрайт-листа
frame_width = 30
frame_height = 30

# Количество кадров в строке и столбце
columns = player_sprite_sheet.get_width() // frame_width
rows = player_sprite_sheet.get_height() // frame_height

# Извлечение кадров
player_walk_right = []
for row in range(rows):
    for col in range(columns):
        frame = player_sprite_sheet.subsurface(
            pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
        )
        scaled_frame = pygame.transform.scale(frame, (70, 70))
        player_walk_right.append(scaled_frame)

# Зеркальное отображение кадров для ходьбы влево
player_walk_left = [pygame.transform.flip(frame, True, False) for frame in player_walk_right]

# Инициализация звуков
hit_sound = defeat_sound = None
try:
    pygame.mixer.init()
    pygame.mixer.music.load("sounds/chiltheme.wav")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
    hit_sound = pygame.mixer.Sound("sounds/slash.wav")
    hit_sound.set_volume(0.5)
    defeat_sound = pygame.mixer.Sound("sounds/deth.wav")
    defeat_sound.set_volume(0.7)
    coin_sound = pygame.mixer.Sound("sounds/slash.wav")  # Звук подбора монеты
    coin_sound.set_volume(0.6)
except Exception as e:
    print(f"Ошибка загрузки музыки: {e}")


# Игрок
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = player_walk_right[0]
        self.rect = self.image.get_rect(center=pos)
        self.speed = 6  # увеличена скорость
        self.direction = "right"
        self.animation_index = 0
        self.animation_speed = 0.20  # увеличена скорость анимации
        self.is_attacking = False
        self.attack_cooldown = 15  # Уменьшил кулдаун
        self.attack_timer = 0
        self.attack_range = 95  # увеличена дальность

    def update(self):
        self.move()
        self.animate()
        self.attack()

    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_s] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed
        if keys[pygame.K_a] and self.rect.left > 0:
            self.rect.x -= self.speed
            self.direction = "left"
        if keys[pygame.K_d] and self.rect.right < WIDTH:
            self.rect.x += self.speed
            self.direction = "right"

    def animate(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_w] or keys[pygame.K_s]:
            self.animation_index += self.animation_speed
            if self.animation_index >= len(player_walk_right):
                self.animation_index = 0
        else:
            self.animation_index = 0

        if self.direction == "right":
            self.image = player_walk_right[int(self.animation_index)]
        else:
            self.image = player_walk_left[int(self.animation_index)]

    def attack(self):
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False

    def draw_attack(self, surface):
        if self.is_attacking:
            if self.direction == "right":
                attack_rect = attack_image.get_rect(center=(self.rect.centerx + 35, self.rect.centery))
                surface.blit(attack_image, attack_rect)
            else:
                attack_rect = attack_image.get_rect(center=(self.rect.centerx - 35, self.rect.centery))
                surface.blit(pygame.transform.flip(attack_image, True, False), attack_rect)


# Башня
class Tower(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = tower_image
        self.rect = self.image.get_rect(center=pos)
        self.health = 100  # увеличено
        self.max_health = self.health

    def draw_health_bar(self, surface):
        bar_width = self.rect.width + 20
        bar_height = 10
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - bar_height - 10

        health_ratio = self.health / self.max_health
        health_bar_width = int(bar_width * health_ratio)

        pygame.draw.rect(surface, BLACK, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, BLUE, (bar_x, bar_y, health_bar_width, bar_height))


# Враги
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, speed, health, wave):
        super().__init__()
        self.image = enemy_image
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed
        self.health = health + wave * 2  # увеличено
        self.max_health = self.health
        self.wave = wave
        self.money_drop = 10 + wave * 2  # увеличено

    def update(self):
        self.move_towards(tower)

    def move_towards(self, tower):
        dx = tower.rect.centerx - self.rect.centerx
        dy = tower.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx = dx / distance
            dy = dy / distance
            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - bar_height - 5

        health_ratio = self.health / self.max_health
        health_bar_width = int(bar_width * health_ratio)

        pygame.draw.rect(surface, BLACK, (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, health_bar_width, bar_height))


# Группы спрайтов
all_sprites = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()

# Создание игрока и башни
player = Player((WIDTH // 2, HEIGHT // 2))
tower = Tower((WIDTH // 2, HEIGHT // 2))
all_sprites.add(player, tower)

# Игровые параметры
wave = 0
enemy_spawn_rate = 90  # изменено
enemy_base_speed = 2.2  # изменено
max_enemies_per_wave = 5
current_wave_enemy_count = 0
money = 0
wave_delay = 120
wave_delay_timer = 0

# Шрифт
try:
    font = pygame.font.Font("fontss.ttf", 32)
    title_font = pygame.font.Font("fontss.ttf", 48)
except:
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)

# Основной цикл игры
clock = pygame.time.Clock()
running = True
frame_count = 0
wave_active = False
show_next_wave_text = True

# Текст для перехода на следующую волну
next_wave_text = title_font.render("Нажмите 'T' для начала волны", True, WHITE)
next_wave_text_rect = next_wave_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))


# Функция для отображения текста
def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)


# Функция спавна врагов
def spawn_enemy():
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        pos = (random.randint(0, WIDTH), -50)
    elif side == "bottom":
        pos = (random.randint(0, WIDTH), HEIGHT + 50)
    elif side == "left":
        pos = (-50, random.randint(0, HEIGHT))
    elif side == "right":
        pos = (WIDTH + 50, random.randint(0, HEIGHT))
    enemy = Enemy(pos, enemy_base_speed + wave * 0.2, 2, wave)
    all_sprites.add(enemy)
    enemies_group.add(enemy)


# Функция для завершения игры
def terminate():
    pygame.quit()
    sys.exit()


# Функция для отображения заставки
def start_screen():
    intro_text = ["The Last Tower", "",
                  "Правила игры:",
                  "WASD - перемещение",
                  "ЛКМ - атака",
                  "T - новая волна"]

    # Загружаем и масштабируем фон
    fon = pygame.transform.scale(load_image('images/screen0.png'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))

    shadow = pygame.Surface((WIDTH, HEIGHT))
    shadow.fill((0, 0, 0))
    shadow.set_alpha(160)  # Делаем фон чуть темнее
    screen.blit(shadow, (0, 0))

    # Настройка шрифтов
    title_font = pygame.font.Font("shrift.ttf", 46)
    font = pygame.font.Font("shrift.ttf", 28)

    # Отрисовка заголовка
    title_rendered = title_font.render(intro_text[0], True, (255, 255, 255))
    title_rect = title_rendered.get_rect(centerx=WIDTH * 0.7, top=420)
    screen.blit(title_rendered, title_rect)

    # Отрисовка текста
    text_coord = 500
    for line in intro_text[2:]:  # Начинаем с правил игры
        string_rendered = font.render(line, True, (255, 255, 255))
        intro_rect = string_rendered.get_rect()
        intro_rect.x = WIDTH * 0.61  # Немного сдвигаем вправо
        intro_rect.top = text_coord
        screen.blit(string_rendered, intro_rect)
        text_coord += 35

    # Декоративная линия
    pygame.draw.line(screen, (255, 255, 255),
                    (WIDTH * 0.55 - 20, 490),
                    (WIDTH * 0.75 + 200, 490),
                    2)

    # Текст "Нажмите любую клавишу" внизу экрана
    start_text = font.render("Нажмите любую клавишу для начала игры", True, (255, 255, 255))
    start_text.set_alpha(160)
    start_text_rect = start_text.get_rect(centerx=WIDTH // 2, bottom=HEIGHT - 50)
    screen.blit(start_text, start_text_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(50)


# Заставка
start_screen()

# Цикл игры
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t and show_next_wave_text:
                wave += 1
                max_enemies_per_wave += 2
                current_wave_enemy_count = 0
                wave_active = True
                show_next_wave_text = False
                wave_delay_timer = wave_delay
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not player.is_attacking:
                player.is_attacking = True
                player.attack_timer = player.attack_cooldown

    # Обновление спрайтов
    all_sprites.update()

    # Создание врагов с задержкой
    if wave_active:
        if wave_delay_timer > 0:
            wave_delay_timer -= 1
        elif frame_count % enemy_spawn_rate == 0 and current_wave_enemy_count < max_enemies_per_wave:
            spawn_enemy()
            current_wave_enemy_count += 1

    # Атака игрока
    if player.is_attacking:
        for enemy in enemies_group:
            dx = enemy.rect.centerx - player.rect.centerx
            dy = enemy.rect.centery - player.rect.centery
            distance = math.hypot(dx, dy)

            if distance <= player.attack_range:
                if (player.direction == "right" and dx > 0) or (player.direction == "left" and dx < 0):
                    enemy.health -= 1
                    if hit_sound:
                        hit_sound.play()
                    if enemy.health <= 0:
                        money += enemy.money_drop
                        enemy.kill()
                        if defeat_sound:
                            defeat_sound.play()
                        if coin_sound:
                            coin_sound.play()

    # Проверка столкновения врагов с башней
    hits = pygame.sprite.spritecollide(tower, enemies_group, False)
    for hit in hits:
        tower.health -= 5
        hit.kill()
        if hit_sound:
            hit_sound.play()
        if tower.health <= 0:
            running = False

    # Проверка окончания волны
    if wave_active and not enemies_group and current_wave_enemy_count == max_enemies_per_wave:
        wave_active = False
        show_next_wave_text = True
        money += wave * 5

    # Отрисовка
    screen.blit(background, (0, 0))
    all_sprites.draw(screen)

    # Отрисовка анимации атаки
    player.draw_attack(screen)

    # Отрисовка здоровья врагов
    for enemy in enemies_group:
        enemy.draw_health_bar(screen)

    # Отрисовка здоровья башни
    tower.draw_health_bar(screen)

    # Текст для перехода на следующую волну
    if show_next_wave_text:
        screen.blit(next_wave_text, next_wave_text_rect)

    # Отображение текста и иконок
    draw_text(f"Здоровье башни: {tower.health}", font, WHITE, screen, 10, 10)
    draw_text(f"Деньги: {money}", font, YELLOW, screen, 10, 50)
    draw_text(f"Волна: {wave}", title_font, ORANGE, screen, 10, 90)  # Изменен цвет
    if wave_active:
        draw_text(f"Оставшиеся враги: {max_enemies_per_wave - current_wave_enemy_count}", font, WHITE, screen, 10, 140)
    else:
        draw_text(f"Оставшиеся враги: 0", font, WHITE, screen, 10, 140)

    # Обновление экрана
    pygame.display.flip()
    clock.tick(60)
    frame_count += 1

pygame.quit()
