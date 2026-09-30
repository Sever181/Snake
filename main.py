import pygame
import random
import sys
from pathlib import Path

# -------------------- DATABASE --------------------
# SQL Server is optional: if it is unavailable, the game still works.
try:
    import pyodbc
except ImportError:
    pyodbc = None

DB_SERVER = r"DESKTOP-D1SS2G0"
DB_NAME = "SnakeGame"
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={DB_SERVER};DATABASE={DB_NAME};"
    "Trusted_Connection=yes;TrustServerCertificate=yes;"
)

def save_score(player_name, score):
    if pyodbc is None:
        return
    try:
        with pyodbc.connect(CONNECTION_STRING, timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO SnakeScores (PlayerName, Score) VALUES (?, ?)",
                    player_name, score
                )
            connection.commit()
    except pyodbc.Error as error:
        print("Не удалось сохранить результат:", error)

# -------------------- GAME --------------------
pygame.init()
WIDTH, HEIGHT = 720, 720
CELL = 24
FPS = 12
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake — Deluxe")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 26)
SMALL = pygame.font.SysFont("Arial", 18)
BIG = pygame.font.SysFont("Arial", 58, bold=True)

BG = (10, 14, 20)
GRID = (22, 30, 39)
WHITE = (240, 245, 250)
MUTED = (130, 145, 160)
GREEN = (60, 205, 82)
GREEN_DARK = (35, 145, 55)
RED = (235, 70, 75)
PANEL = (17, 23, 31)

# Папка с игровыми изображениями.
# Она находится рядом с main.py:
# Snake_Deluxe/
# ├── main.py
# └── assets/
ASSETS = Path(__file__).resolve().parent / "assets"

def load_asset(filename, size=(CELL, CELL)):
    """Загружает картинку из папки assets и масштабирует её."""
    path = ASSETS / filename
    if not path.exists():
        print(f"Предупреждение: файл не найден: {path}")
        return None

    image = pygame.image.load(str(path)).convert_alpha()
    return pygame.transform.smoothscale(image, size)

# Голова и тело змейки теперь РЕАЛЬНО берутся из assets.
SNAKE_HEAD = load_asset("snake_head.png", (CELL + 8, CELL + 8))
SNAKE_BODY = load_asset("snake_body.png", (CELL + 4, CELL + 4))

# Загружаем всю еду из assets.
# Поэтому достаточно положить новый .png в assets — он автоматически
# сможет использоваться в игре.
FOODS = []
for path in sorted(ASSETS.glob("*.png")):
    if path.name.lower() in {"snake_head.png", "snake_body.png"}:
        continue
    image = load_asset(path.name, (CELL + 16, CELL + 16))
    if image is not None:
        FOODS.append(image)

# Если в assets пока только одна картинка еды (например pizza.png),
# игра будет использовать её. Если картинок нет — остаётся запасной вариант.

def draw_grid():
    for x in range(0, WIDTH, CELL):
        pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL):
        pygame.draw.line(screen, GRID, (0, y), (WIDTH, y))

def text_center(text, font, color, y):
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))

def get_player_name():
    name = ""
    while True:
        screen.fill(BG)
        text_center("SNAKE", BIG, GREEN, 190)
        text_center("Deluxe", FONT, MUTED, 245)

        box = pygame.Rect(170, 300, 380, 58)
        pygame.draw.rect(screen, PANEL, box, border_radius=14)
        pygame.draw.rect(screen, GREEN, box, 2, border_radius=14)

        value = FONT.render(name or "Введите имя...", True, WHITE if name else MUTED)
        screen.blit(value, (box.x + 18, box.y + 14))
        text_center("ENTER — начать   •   ESC — выход", SMALL, MUTED, 405)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_RETURN and name.strip():
                    return name.strip()[:20]
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode.isprintable() and len(name) < 20:
                    name += event.unicode

def create_food(snake):
    while True:
        pos = (random.randrange(1, WIDTH // CELL - 1) * CELL,
               random.randrange(1, HEIGHT // CELL - 1) * CELL)
        if pos not in snake:
            return pos, random.randrange(len(FOODS)) if FOODS else 0

def draw_food(pos, index):
    """Рисует еду картинкой из assets."""
    x, y = pos

    if FOODS:
        image = FOODS[index % len(FOODS)]
        screen.blit(image, (x - 8, y - 8))
    else:
        # Запасной вариант, если в assets нет еды.
        pygame.draw.circle(
            screen,
            RED,
            (x + CELL // 2, y + CELL // 2),
            CELL // 2 - 2
        )


def rotate_head(direction):
    """Поворачивает картинку головы под направление движения.

    Исходная snake_head.png считается направленной ВПРАВО.
    """
    if SNAKE_HEAD is None:
        return None

    dx, dy = direction

    if dx > 0:      # вправо — исходное положение
        angle = 0
    elif dx < 0:    # влево
        angle = 180
    elif dy < 0:    # вверх
        angle = 90
    else:           # вниз
        angle = -90

    return pygame.transform.rotate(SNAKE_HEAD, angle)


def draw_snake(snake, direction):
    """Рисует змейку изображениями из папки assets."""
    head_image = rotate_head(direction)

    for i, (x, y) in enumerate(snake):
        if i == 0 and head_image is not None:
            # Голова берётся из assets/snake_head.png
            rect = head_image.get_rect(
                center=(x + CELL // 2, y + CELL // 2)
            )
            screen.blit(head_image, rect)

        elif SNAKE_BODY is not None:
            # Каждый сегмент тела берётся из assets/snake_body.png
            rect = SNAKE_BODY.get_rect(
                center=(x + CELL // 2, y + CELL // 2)
            )
            screen.blit(SNAKE_BODY, rect)

        else:
            # Запасной вариант, если snake_body.png отсутствует.
            rect = pygame.Rect(
                x + 2, y + 2, CELL - 4, CELL - 4
            )
            pygame.draw.rect(
                screen,
                GREEN_DARK,
                rect,
                border_radius=8
            )

def game(player_name):
    center = (WIDTH//2, HEIGHT//2)
    snake = [(center[0], center[1]), (center[0]-CELL, center[1]), (center[0]-CELL*2, center[1])]
    direction = (CELL, 0)
    next_direction = direction
    food, food_index = create_food(snake)
    score = 0
    paused = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return score
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if not paused:
                    if event.key == pygame.K_UP and direction != (0, CELL):
                        next_direction = (0, -CELL)
                    elif event.key == pygame.K_DOWN and direction != (0, -CELL):
                        next_direction = (0, CELL)
                    elif event.key == pygame.K_LEFT and direction != (CELL, 0):
                        next_direction = (-CELL, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-CELL, 0):
                        next_direction = (CELL, 0)

        if not paused:
            direction = next_direction
            hx, hy = snake[0]
            new_head = (hx + direction[0], hy + direction[1])
            snake.insert(0, new_head)

            if new_head == food:
                score += 1
                food, food_index = create_food(snake)
            else:
                snake.pop()

            x, y = snake[0]
            if x < CELL or x >= WIDTH-CELL or y < CELL or y >= HEIGHT-CELL:
                running = False
            if snake[0] in snake[1:]:
                running = False

        screen.fill(BG)
        draw_grid()
        # Border
        pygame.draw.rect(screen, (35, 48, 60), (CELL-2, CELL-2, WIDTH-2*CELL+4, HEIGHT-2*CELL+4), 3, border_radius=8)

        draw_food(food, food_index)
        draw_snake(snake, direction)

        panel = pygame.Rect(12, 10, 210, 48)
        pygame.draw.rect(screen, PANEL, panel, border_radius=14)
        screen.blit(FONT.render(f"Очки: {score}", True, WHITE), (28, 20))
        screen.blit(SMALL.render(f"Длина: {len(snake)}", True, MUTED), (125, 24))

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,150))
            screen.blit(overlay, (0,0))
            text_center("ПАУЗА", BIG, WHITE, HEIGHT//2 - 25)
            text_center("SPACE — продолжить", SMALL, MUTED, HEIGHT//2 + 35)

        pygame.display.flip()
        clock.tick(min(24, FPS + score // 5))

    save_score(player_name, score)
    return score

def game_over(player_name, score):
    while True:
        screen.fill(BG)
        text_center("GAME OVER", BIG, RED, 220)
        text_center(player_name, FONT, WHITE, 300)
        text_center(f"Очки: {score}", FONT, GREEN, 345)
        text_center("ENTER — новая игра   •   ESC — выход", SMALL, MUTED, 420)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

def main():
    player = get_player_name()
    while True:
        score = game(player)
        if not game_over(player, score):
            break
    pygame.quit()

if __name__ == "__main__":
    main()
