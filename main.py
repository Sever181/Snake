import pygame
import random
import sys
import threading
from pathlib import Path

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


def save_score_async(player_name, score):
    # Сохраняем в фоне, чтобы не подвешивать игру на время подключения к БД
    threading.Thread(
        target=save_score, args=(player_name, score), daemon=True
    ).start()


pygame.init()
WIDTH, HEIGHT = 480, 480
CELL = 24
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake — Deluxe")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 18)
SMALL = pygame.font.SysFont("Arial", 13)
BIG = pygame.font.SysFont("Arial", 38, bold=True)

BG = (10, 14, 20)
GRID = (22, 30, 39)
WHITE = (240, 245, 250)
MUTED = (130, 145, 160)
GREEN = (60, 205, 82)
GREEN_DARK = (35, 145, 55)
RED = (235, 70, 75)
PANEL = (17, 23, 31)

# Папка с изображениями рядом с main.py
ASSETS = Path(__file__).resolve().parent / "assets"

def load_asset(filename, size=(CELL, CELL)):
    path = ASSETS / filename
    if not path.exists():
        print(f"Предупреждение: файл не найден: {path}")
        return None
    image = pygame.image.load(str(path)).convert_alpha()
    return pygame.transform.smoothscale(image, size)

SNAKE_HEAD = load_asset("snake_head.png", (CELL + 8, CELL + 8))
SNAKE_BODY = load_asset("snake_body.png", (CELL + 4, CELL + 4))

# Вся еда — это все .png в assets, кроме головы и тела
FOODS = []
for path in sorted(ASSETS.glob("*.png")):
    if path.name.lower() in {"snake_head.png", "snake_body.png"}:
        continue
    image = load_asset(path.name, (CELL + 16, CELL + 16))
    if image is not None:
        FOODS.append(image)


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
        text_center("SNAKE", BIG, GREEN, 130)
        text_center("Deluxe", FONT, MUTED, 170)

        box = pygame.Rect(90, 210, 300, 46)
        pygame.draw.rect(screen, PANEL, box, border_radius=12)
        pygame.draw.rect(screen, GREEN, box, 2, border_radius=12)

        value = FONT.render(name or "Введите имя...", True, WHITE if name else MUTED)
        screen.blit(value, (box.x + 14, box.y + 12))
        text_center("ENTER — начать   •   ESC — выход", SMALL, MUTED, 290)
        pygame.display.flip()

        clock.tick(60)

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


def create_food(snake, foods):
    # Создаёт еду, не пересекающуюся со змейкой и другими едами
    occupied = set(snake) | {pos for pos, _ in foods}
    for _ in range(1000):
        pos = (random.randrange(1, WIDTH // CELL - 1) * CELL,
               random.randrange(1, HEIGHT // CELL - 1) * CELL)
        if pos not in occupied:
            index = random.randrange(len(FOODS)) if FOODS else 0
            return (pos, index)
    return None


def spawn_foods(snake, foods, count):
    # Добавляет count новых единиц еды
    for _ in range(count):
        new_food = create_food(snake, foods)
        if new_food is None:
            break
        foods.append(new_food)


def draw_food(pos, index):
    x, y = pos
    if FOODS:
        image = FOODS[index % len(FOODS)]
        screen.blit(image, (x - 8, y - 8))
    else:
        pygame.draw.circle(screen, RED,
                           (x + CELL // 2, y + CELL // 2),
                           CELL // 2 - 2)


def rotate_head(direction):
    # Поворачивает голову; исходный спрайт смотрит вправо
    if SNAKE_HEAD is None:
        return None
    dx, dy = direction
    if dx > 0:
        angle = 0
    elif dx < 0:
        angle = 180
    elif dy < 0:
        angle = 90
    else:
        angle = -90
    return pygame.transform.rotate(SNAKE_HEAD, angle)


def draw_snake(snake, direction):
    head_image = rotate_head(direction)
    for i, (x, y) in enumerate(snake):
        if i == 0 and head_image is not None:
            rect = head_image.get_rect(center=(x + CELL // 2, y + CELL // 2))
            screen.blit(head_image, rect)
        elif SNAKE_BODY is not None:
            rect = SNAKE_BODY.get_rect(center=(x + CELL // 2, y + CELL // 2))
            screen.blit(SNAKE_BODY, rect)
        else:
            rect = pygame.Rect(x + 2, y + 2, CELL - 4, CELL - 4)
            pygame.draw.rect(screen, GREEN_DARK, rect, border_radius=8)


def game(player_name):
    center = (WIDTH // 2, HEIGHT // 2)
    snake = [(center[0], center[1]),
             (center[0] - CELL, center[1]),
             (center[0] - CELL * 2, center[1])]
    direction = (CELL, 0)
    next_direction = direction

    foods = []
    spawn_foods(snake, foods, 1)

    score = 0
    paused = False
    running = True

    # Тайминг шагов змейки (в миллисекундах)
    move_delay_start = 180
    move_delay_min   = 90
    move_delay_step  = 6
    move_timer = 0

    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save_score_async(player_name, score)
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
            move_timer += dt
            move_delay = max(move_delay_min,
                             move_delay_start - score * move_delay_step)
            if move_timer >= move_delay:
                move_timer = 0
                direction = next_direction
                hx, hy = snake[0]
                new_head = (hx + direction[0], hy + direction[1])
                snake.insert(0, new_head)

                eaten_index = None
                for i, (pos, _) in enumerate(foods):
                    if pos == new_head:
                        eaten_index = i
                        break

                if eaten_index is not None:
                    foods.pop(eaten_index)
                    score += 1
                    spawn_foods(snake, foods, 2)
                else:
                    snake.pop()

                x, y = snake[0]
                if x < CELL or x >= WIDTH - CELL or y < CELL or y >= HEIGHT - CELL:
                    running = False
                if snake[0] in snake[1:]:
                    running = False

        screen.fill(BG)
        draw_grid()
        pygame.draw.rect(screen, (35, 48, 60),
                         (CELL - 2, CELL - 2,
                          WIDTH - 2 * CELL + 4,
                          HEIGHT - 2 * CELL + 4),
                         3, border_radius=8)

        for pos, idx in foods:
            draw_food(pos, idx)

        draw_snake(snake, direction)

        panel = pygame.Rect(8, 6, 160, 34)
        pygame.draw.rect(screen, PANEL, panel, border_radius=10)
        screen.blit(FONT.render(f"Очки: {score}", True, WHITE), (18, 13))
        screen.blit(SMALL.render(f"Длина: {len(snake)}", True, MUTED), (100, 16))

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            text_center("ПАУЗА", BIG, WHITE, HEIGHT // 2 - 25)
            text_center("SPACE — продолжить", SMALL, MUTED, HEIGHT // 2 + 25)

        pygame.display.flip()

    save_score_async(player_name, score)
    return score


def game_over(player_name, score):
    while True:
        screen.fill(BG)
        text_center("GAME OVER", BIG, RED, 150)
        text_center(player_name, FONT, WHITE, 200)
        text_center(f"Очки: {score}", FONT, GREEN, 230)
        text_center("ENTER — новая игра", SMALL, MUTED, 290)
        text_center("ESC — выход", SMALL, MUTED, 310)
        pygame.display.flip()

        clock.tick(60)

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