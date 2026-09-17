import pygame
import random
import pyodbc
import sys


# НАСТРОЙКИ БАЗЫ ДАННЫХ


DB_SERVER = r"DESKTOP-D1SS2G0"
DB_NAME = "SnakeGame"

# Если используется Windows Authentication:
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


def save_score(player_name, score):
    """Сохраняет результат игры в MS SQL Server."""

    try:
        connection = pyodbc.connect(CONNECTION_STRING)
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO SnakeScores (PlayerName, Score)
            VALUES (?, ?)
            """,
            player_name,
            score
        )

        connection.commit()

        cursor.close()
        connection.close()

        print("Очки сохранены в базу данных.")

    except pyodbc.Error as error:
        print("Ошибка подключения к базе данных:")
        print(error)


# НАСТРОЙКИ ИГРЫ


pygame.init()

WIDTH = 600
HEIGHT = 600

CELL_SIZE = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 30)
big_font = pygame.font.SysFont("Arial", 50)


# ЦВЕТА


BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 120, 0)
RED = (220, 50, 50)
GRAY = (100, 100, 100)


# ИМЯ ИГРОКА


def get_player_name():
    name = ""

    while True:
        screen.fill(BLACK)

        title = big_font.render("SNAKE", True, GREEN)
        title_rect = title.get_rect(center=(WIDTH // 2, 180))
        screen.blit(title, title_rect)

        text = font.render("Введите имя:", True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, 270))
        screen.blit(text, text_rect)

        name_text = font.render(name, True, GREEN)
        name_rect = name_text.get_rect(center=(WIDTH // 2, 320))
        screen.blit(name_text, name_rect)

        hint = pygame.font.SysFont("Arial", 20).render(
            "ENTER - начать игру", True, GRAY
        )
        hint_rect = hint.get_rect(center=(WIDTH // 2, 370))
        screen.blit(hint, hint_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:
                    if name.strip():
                        return name.strip()

                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]

                else:
                    if len(name) < 20:
                        if event.unicode.isprintable():
                            name += event.unicode



# СОЗДАНИЕ ЕДЫ

def create_food(snake):
    while True:
        food = (
            random.randrange(0, WIDTH, CELL_SIZE),
            random.randrange(0, HEIGHT, CELL_SIZE)
        )

        if food not in snake:
            return food



# ИГРА

def game(player_name):

    snake = [
        (300, 300),
        (280, 300),
        (260, 300)
    ]

    direction = (CELL_SIZE, 0)
    next_direction = direction

    food = create_food(snake)

    score = 0

    speed = 10

    running = True

    while running:

        # ОБРАБОТКА СОБЫТИЙ
  
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_UP:
                    if direction != (0, CELL_SIZE):
                        next_direction = (0, -CELL_SIZE)

                elif event.key == pygame.K_DOWN:
                    if direction != (0, -CELL_SIZE):
                        next_direction = (0, CELL_SIZE)

                elif event.key == pygame.K_LEFT:
                    if direction != (CELL_SIZE, 0):
                        next_direction = (-CELL_SIZE, 0)

                elif event.key == pygame.K_RIGHT:
                    if direction != (-CELL_SIZE, 0):
                        next_direction = (CELL_SIZE, 0)

        direction = next_direction

        # ДВИЖЕНИЕ ЗМЕИ

        head_x, head_y = snake[0]

        new_head = (
            head_x + direction[0],
            head_y + direction[1]
        )

        snake.insert(0, new_head)


        # ПРОВЕРКА ЕДЫ

        if new_head == food:

            score += 1

            food = create_food(snake)

            # Немного увеличиваем скорость
            speed = min(25, 10 + score // 5)

        else:
            snake.pop()

        # СТОЛКНОВЕНИЕ СО СТЕНОЙ

        x, y = snake[0]

        if (
            x < 0
            or x >= WIDTH
            or y < 0
            or y >= HEIGHT
        ):
            running = False

        # СТОЛКНОВЕНИЕ С СОБОЙ

        if snake[0] in snake[1:]:
            running = False

        # ОТРИСОВКА

        screen.fill(BLACK)

        # Еда
        pygame.draw.rect(
            screen,
            RED,
            (
                food[0],
                food[1],
                CELL_SIZE,
                CELL_SIZE
            )
        )

        # Змея
        for index, part in enumerate(snake):

            color = GREEN if index == 0 else DARK_GREEN

            pygame.draw.rect(
                screen,
                color,
                (
                    part[0],
                    part[1],
                    CELL_SIZE,
                    CELL_SIZE
                )
            )

        # Очки
        score_text = font.render(
            f"Очки: {score}",
            True,
            WHITE
        )

        screen.blit(score_text, (10, 10))

        pygame.display.flip()

        clock.tick(speed)

    # СОХРАНЕНИЕ РЕЗУЛЬТАТА


    save_score(player_name, score)

    return score


def game_over(player_name, score):

    while True:

        screen.fill(BLACK)

        title = big_font.render(
            "GAME OVER",
            True,
            RED
        )

        title_rect = title.get_rect(
            center=(WIDTH // 2, 200)
        )

        screen.blit(title, title_rect)

        score_text = font.render(
            f"Игрок: {player_name}",
            True,
            WHITE
        )

        score_rect = score_text.get_rect(
            center=(WIDTH // 2, 280)
        )

        screen.blit(score_text, score_rect)

        points_text = font.render(
            f"Очки: {score}",
            True,
            GREEN
        )

        points_rect = points_text.get_rect(
            center=(WIDTH // 2, 330)
        )

        screen.blit(points_text, points_rect)

        restart_text = pygame.font.SysFont(
            "Arial", 20
        ).render(
            "ENTER - новая игра    ESC - выход",
            True,
            GRAY
        )

        restart_rect = restart_text.get_rect(
            center=(WIDTH // 2, 400)
        )

        screen.blit(restart_text, restart_rect)

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:
                    return True

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


def main():

    player_name = get_player_name()

    while True:

        score = game(player_name)

        restart = game_over(
            player_name,
            score
        )

        if not restart:
            break


if __name__ == "__main__":
    main()
