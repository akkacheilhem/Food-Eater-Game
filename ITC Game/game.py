import cv2
import mediapipe as mp
import pygame
import random
import math



pygame.init()
pygame.mixer.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Food Eater Game")

clock = pygame.time.Clock()

CAM_X = 20
CAM_Y = 70
CAM_W = 760
CAM_H = 470
CAM_RADIUS = 10
WEBCAM_FOOD_RADIUS = 25


WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (220, 50, 70)
GREEN = (50, 200, 100)
YELLOW = (255, 210, 60)
BLUE = (70, 140, 255)
PURPLE = (160, 90, 220)

HEART_COLOR = (235, 50, 80)


font = pygame.font.SysFont("arial", 22, bold=True)
small_font = pygame.font.SysFont("arial", 20, bold=True)
big_font = pygame.font.SysFont("arial", 55, bold=True)
title_font = pygame.font.SysFont("arial", 65, bold=True)


BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


landmarker_options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="face_landmarker.task"
    ),
    running_mode=VisionRunningMode.VIDEO,
    num_faces=1
)

landmarker = FaceLandmarker.create_from_options(landmarker_options)


camera = None


def start_camera():
    global camera

    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)

    return camera is not None and camera.isOpened()


eat_sound = pygame.mixer.Sound("assets/sounds/eat.mp3")
bonus_sound = pygame.mixer.Sound("assets/sounds/bonus.mp3")
bomb_sound = pygame.mixer.Sound("assets/sounds/bomb.mp3")
game_over_sound = pygame.mixer.Sound("assets/sounds/game_over.mp3")

def load_food_image(path):
    image = pygame.image.load(path).convert_alpha()
    image = pygame.transform.scale(image, (50, 50))
    return image


food_images = {
    "apple": load_food_image("assets/apple.png"),
    "banana": load_food_image("assets/banana.png"),
    "pizza": load_food_image("assets/pizza.png"),
    "burger": load_food_image("assets/burger.png"),
    "bonus": load_food_image("assets/bonus.png"),
    "bomb": load_food_image("assets/bomb.png")
}

background_foods = []


def create_background_food():
    food_type = random.choice([
        "apple",
        "banana",
        "pizza",
        "burger"
    ])

    original_image = food_images[food_type]

    size = random.randint(25, 42)

    image = pygame.transform.smoothscale(
        original_image,
        (size, size)
    )

    # Transparence
    image.set_alpha(random.randint(35, 75))

    return {
        "image": image,
        "x": random.randint(0, WIDTH),
        "y": random.randint(-HEIGHT, HEIGHT),
        "speed": random.uniform(0.5, 1.5),
        "rotation": random.uniform(0, 360),
        "rotation_speed": random.uniform(-1, 1)
    }


def initialize_background():
    global background_foods

    background_foods = []

    for _ in range(18):
        background_foods.append(create_background_food())


def update_background():
    for food in background_foods:

        food["y"] += food["speed"]
        food["rotation"] += food["rotation_speed"]

    
        if food["y"] > HEIGHT + 50:

            food["y"] = random.randint(-100, -30)
            food["x"] = random.randint(0, WIDTH)

            food["speed"] = random.uniform(0.5, 1.5)

    # On met à jour l'affichage
    for food in background_foods:

        rotated_image = pygame.transform.rotate(
            food["image"],
            food["rotation"]
        )

        rect = rotated_image.get_rect(
            center=(
                int(food["x"]),
                int(food["y"])
            )
        )

        screen.blit(rotated_image, rect)


player_x = CAM_X + CAM_W // 2
player_y = CAM_Y + CAM_H // 2

player_radius = 35

mouth_opening = 0
mouth_threshold = 15
face_detected = False


score = 0
lives = 3
best_score = 0

food_speed = 4


food_x = WIDTH // 2
food_y = -50

food_type = "apple"
food_radius = 25


game_state = "menu"

game_over_sound_played = False

effects = []


def add_text_effect(text, x, y, duration=60, color=YELLOW):

    effects.append({
        "type": "text",
        "text": text,
        "x": x,
        "y": y,
        "life": duration,
        "max_life": duration,
        "color": color
    })


def add_explosion_effect(x, y, duration=30):

    effects.append({
        "type": "explosion",
        "x": x,
        "y": y,
        "life": duration,
        "max_life": duration
    })


def draw_effects(surface):

    for effect in effects[:]:

        effect["life"] -= 1


        if effect["type"] == "text":

            effect["y"] -= 1.5

            alpha_ratio = (
                effect["life"] /
                effect["max_life"]
            )

            effect_font = pygame.font.SysFont("arial", 30, bold=True)

            text_surface = effect_font.render(
                effect["text"],
                True,
                effect.get("color", YELLOW)
            )

            text_surface.set_alpha(
                int(255 * alpha_ratio)
            )

            surface.blit(
                text_surface,
                (
                    int(effect["x"] - text_surface.get_width() / 2),
                    int(effect["y"])
                )
            )


        elif effect["type"] == "explosion":

            progress = (
                1 -
                effect["life"] /
                effect["max_life"]
            )

            radius = int(20 + progress * 70)

            pygame.draw.circle(
                surface,
                (255, 130, 30),
                (
                    int(effect["x"]),
                    int(effect["y"])
                ),
                radius,
                5
            )

            pygame.draw.circle(
                surface,
                (255, 220, 50),
                (
                    int(effect["x"]),
                    int(effect["y"])
                ),
                max(5, int(radius * 0.35))
            )

        if effect["life"] <= 0:
            effects.remove(effect)


def draw_heart(surface, x, y, size, color):

    radius = size // 4

    pygame.draw.circle(
        surface,
        color,
        (x - radius, y - radius // 2),
        radius
    )

    pygame.draw.circle(
        surface,
        color,
        (x + radius, y - radius // 2),
        radius
    )

    pygame.draw.polygon(
        surface,
        color,
        [
            (x - size // 2, y - radius // 2),
            (x + size // 2, y - radius // 2),
            (x, y + size // 2)
        ]
    )


def draw_lives(surface, lives):

    x = 35
    y = HEIGHT - 38

    for i in range(lives):

        draw_heart(
            surface,
            x + i * 42,
            y,
            30,
            HEART_COLOR
        )


def draw_mouth(surface, x, y, opening):

    mouth_width = 65


    if opening <= mouth_threshold:

        pygame.draw.ellipse(
            surface,
            (220, 70, 100),
            (
                x - mouth_width // 2,
                y - 8,
                mouth_width,
                16
            )
        )

        pygame.draw.line(
            surface,
            (120, 30, 50),
            (x - 25, y),
            (x + 25, y),
            3
        )


    else:

        mouth_height = (
            20 +
            int(min(opening, 40) * 0.8)
        )

        pygame.draw.ellipse(
            surface,
            (220, 70, 100),
            (
                x - mouth_width // 2,
                y - mouth_height // 2,
                mouth_width,
                mouth_height
            )
        )

        inner_width = mouth_width - 12

        inner_height = max(
            8,
            mouth_height - 10
        )

        pygame.draw.ellipse(
            surface,
            (20, 10, 10),
            (
                x - inner_width // 2,
                y - inner_height // 2,
                inner_width,
                inner_height
            )
        )


def draw_button(
    surface,
    text,
    rect,
    color,
    hover_color
):

    mouse_pos = pygame.mouse.get_pos()

    current_color = color

    if rect.collidepoint(mouse_pos):
        current_color = hover_color

    pygame.draw.rect(
        surface,
        current_color,
        rect,
        border_radius=12
    )

    pygame.draw.rect(
        surface,
        WHITE,
        rect,
        2,
        border_radius=12
    )

    text_surface = font.render(
        text,
        True,
        WHITE
    )

    text_rect = text_surface.get_rect(
        center=rect.center
    )

    surface.blit(
        text_surface,
        text_rect
    )

def draw_webcam_frame():
    # Petit cadre bleu, sans changer le reste du design.
    pygame.draw.rect(
        screen,
        (5, 5, 5),
        (CAM_X + 3, CAM_Y + 4, CAM_W, CAM_H),
        border_radius=CAM_RADIUS
    )

    pygame.draw.rect(
        screen,
        BLUE,
        (CAM_X - 2, CAM_Y - 2, CAM_W + 4, CAM_H + 4),
        width=3,
        border_radius=CAM_RADIUS + 2
    )


def draw_webcam(frame_rgb):
    if frame_rgb is None:
        return

    surface = pygame.surfarray.make_surface(
        frame_rgb.swapaxes(0, 1)
    )
    surface = pygame.transform.scale(
        surface,
        (CAM_W, CAM_H)
    )

    # Masque pour reproduire les coins arrondis de la capture.
    webcam_surface = pygame.Surface(
        (CAM_W, CAM_H),
        pygame.SRCALPHA
    )
    webcam_surface.blit(surface, (0, 0))

    mask = pygame.Surface(
        (CAM_W, CAM_H),
        pygame.SRCALPHA
    )
    pygame.draw.rect(
        mask,
        (255, 255, 255, 255),
        (0, 0, CAM_W, CAM_H),
        border_radius=CAM_RADIUS
    )
    webcam_surface.blit(
        mask,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_MULT
    )

    screen.blit(
        webcam_surface,
        (CAM_X, CAM_Y)
    )

def reset_food():

    global food_x
    global food_y
    global food_type

    food_x = random.randint(
        CAM_X + food_radius,
        CAM_X + CAM_W - food_radius
    )

    food_y = CAM_Y + food_radius

    chance = random.random()

    if chance < 0.60:

        food_type = random.choice([
            "apple",
            "banana",
            "pizza",
            "burger"
        ])

    elif chance < 0.80:

        food_type = "bonus"

    else:

        food_type = "bomb"

def reset_game():

    global score
    global lives
    global food_speed
    global player_x
    global player_y
    global mouth_opening
    global effects
    global game_over_sound_played
    global face_detected

    score = 0
    lives = 3

    food_speed = 4

    player_x = CAM_X + CAM_W // 2
    player_y = CAM_Y + CAM_H // 2

    mouth_opening = 0
    face_detected = False

    effects = []

    game_over_sound_played = False

    reset_food()

def check_collision():

    distance = math.sqrt(
        (player_x - food_x) ** 2 +
        (player_y - food_y) ** 2
    )

    return face_detected and distance < (
        player_radius +
        food_radius + 12
    )

def get_level():

    return 1 + score // 50

def draw_game_interface():

    # SCORE / BEST / LEVEL are ABOVE the webcam.
    screen.blit(font.render(f"SCORE: {score}", True, WHITE), (20, 25))
    screen.blit(font.render(f"BEST: {best_score}", True, WHITE), (250, 25))
    screen.blit(font.render(f"LEVEL: {get_level()}", True, WHITE), (480, 25))

    # Lives are BELOW the webcam.
    draw_lives(screen, lives)



def draw_menu():

    # Background animé
    update_background()

    # Voile sombre léger pour améliorer la lisibilité
    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 70)
    )

    screen.blit(
        overlay,
        (0, 0)
    )


    title = title_font.render(
        "FOOD EATER",
        True,
        WHITE
    )

    title_rect = title.get_rect(
        center=(WIDTH // 2, 150)
    )

    screen.blit(
        title,
        title_rect
    )


    subtitle = font.render(
        "Eat the food with your mouth!",
        True,
        WHITE
    )

    subtitle_rect = subtitle.get_rect(
        center=(WIDTH // 2, 220)
    )

    screen.blit(
        subtitle,
        subtitle_rect
    )


    start_rect = pygame.Rect(
        WIDTH // 2 - 110,
        300,
        220,
        60
    )

    draw_button(
        screen,
        "START",
        start_rect,
        BLUE,
        (100, 170, 255)
    )


    cancel_rect = pygame.Rect(
        WIDTH // 2 - 110,
        380,
        220,
        60
    )

    draw_button(
        screen,
        "CANCEL",
        cancel_rect,
        RED,
        (255, 90, 110)
    )

    return start_rect, cancel_rect


def draw_game_over():

    # Background animé
    update_background()

    # Voile sombre
    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 130)
    )

    screen.blit(
        overlay,
        (0, 0)
    )


    game_over_text = big_font.render(
        "GAME OVER",
        True,
        RED
    )

    game_over_rect = game_over_text.get_rect(
        center=(WIDTH // 2, 150)
    )

    screen.blit(
        game_over_text,
        game_over_rect
    )

    final_score_text = font.render(
        f"SCORE: {score}",
        True,
        WHITE
    )

    final_score_rect = final_score_text.get_rect(
        center=(WIDTH // 2, 230)
    )

    screen.blit(
        final_score_text,
        final_score_rect
    )


    final_best_text = font.render(
        f"BEST: {best_score}",
        True,
        YELLOW
    )

    final_best_rect = final_best_text.get_rect(
        center=(WIDTH // 2, 270)
    )

    screen.blit(
        final_best_text,
        final_best_rect
    )


    restart_rect = pygame.Rect(
        WIDTH // 2 - 110,
        330,
        220,
        60
    )

    draw_button(
        screen,
        "RESTART",
        restart_rect,
        GREEN,
        (80, 230, 130)
    )


    cancel_rect = pygame.Rect(
        WIDTH // 2 - 110,
        410,
        220,
        60
    )

    draw_button(
        screen,
        "CANCEL",
        cancel_rect,
        RED,
        (255, 90, 110)
    )

    return restart_rect, cancel_rect


initialize_background()


running = True


while running:


    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse_pos = event.pos

            if game_state == "menu":

                start_rect, cancel_rect = draw_menu()

                if start_rect.collidepoint(mouse_pos):

                    if start_camera():

                        reset_game()
                        game_state = "playing"

                elif cancel_rect.collidepoint(mouse_pos):

                    running = False

            elif game_state == "game_over":

                restart_rect, cancel_rect = draw_game_over()

                if restart_rect.collidepoint(mouse_pos):

                    reset_game()
                    game_state = "playing"

                elif cancel_rect.collidepoint(mouse_pos):

                    running = False

        if event.type == pygame.KEYDOWN:

            if (
                event.key == pygame.K_r
                and game_state == "game_over"
            ):

                reset_game()
                game_state = "playing"

    if game_state == "menu":

        screen.fill(
            (25, 30, 45)
        )

        draw_menu()

    elif game_state == "playing":

        screen.fill(
            (25, 30, 45)
        )

        # Le fond reste uni pendant le jeu : les seuls aliments
        # visibles sont ceux qui tombent dans la webcam.

        camera_frame_rgb = None
        face_detected = False

        if camera is not None:

            ret, frame = camera.read()

            if ret:

                # Webcam miroir comme une caméra classique.
                frame = cv2.flip(frame, 1)

                # Image affichée dans la zone webcam.
                camera_frame_rgb = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                # Image pour MediaPipe.
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=camera_frame_rgb
                )

                timestamp = pygame.time.get_ticks()

                if not hasattr(start_camera, "_last_timestamp"):
                    start_camera._last_timestamp = 0
                if timestamp <= start_camera._last_timestamp:
                    timestamp = start_camera._last_timestamp + 1
                start_camera._last_timestamp = timestamp

                result = landmarker.detect_for_video(
                    mp_image,
                    timestamp
                )

                if result.face_landmarks:

                    face_detected = True
                    face_landmarks = result.face_landmarks[0]

                    # Position X de la bouche.
                    mouth_x_normalized = face_landmarks[13].x

                    camera_left = 0.25
                    camera_right = 0.75

                    mapped_x = (
                        (mouth_x_normalized - camera_left)
                        / (camera_right - camera_left)
                    )

                    mapped_x = max(0.0, min(1.0, mapped_x))

                    player_x = int(
                        CAM_X
                        + mapped_x * (CAM_W - 2 * player_radius)
                        + player_radius
                    )

                    # Position Y de la bouche dans la webcam.
                    player_y = int(
                        CAM_Y
                        + face_landmarks[13].y * CAM_H
                    )

                    player_y = max(
                        CAM_Y + player_radius,
                        min(
                            CAM_Y + CAM_H - player_radius,
                            player_y
                        )
                    )

                    # Ouverture de la bouche.
                    upper_lip = face_landmarks[13]
                    lower_lip = face_landmarks[14]

                    upper_y = int(
                        upper_lip.y * frame.shape[0]
                    )

                    lower_y = int(
                        lower_lip.y * frame.shape[0]
                    )

                    mouth_opening = lower_y - upper_y

        draw_webcam_frame()

        if camera_frame_rgb is not None:
            draw_webcam(camera_frame_rgb)

        food_y += food_speed

        if food_y - food_radius > CAM_Y + CAM_H:

            reset_food()

        if check_collision():

            if mouth_opening > mouth_threshold:
                if food_type in [
                    "apple",
                    "banana"
                ]:

                    score += 10

                    eat_sound.play()

                    add_text_effect(
                        "+10",
                        food_x,
                        food_y,
                        color=GREEN
                    )

                elif food_type in [
                    "pizza",
                    "burger"
                ]:

                    score += 20

                    eat_sound.play()

                    add_text_effect(
                        "+20",
                        food_x,
                        food_y,
                        color=GREEN
                    )


                elif food_type == "bonus":

                    score += 30

                    bonus_sound.play()

                    add_text_effect(
                        "+30 BONUS!",
                        food_x,
                        food_y,
                        color=YELLOW
                    )

                elif food_type == "bomb":

                    lives -= 1

                    bomb_sound.play()

                    add_text_effect(
                        "-1 LIFE",
                        food_x,
                        food_y,
                        color=RED
                    )

                    add_explosion_effect(
                        food_x,
                        food_y
                    )

                if score > best_score:
                    best_score = score

                if lives <= 0:

                    game_state = "game_over"

                reset_food()

        food_speed = min(
            10,
            4 + score // 50
        )

        food_image = food_images[
            food_type
        ]

        food_rect = food_image.get_rect(
            center=(
                food_x,
                food_y
            )
        )

        screen.blit(
            food_image,
            food_rect
        )

        draw_game_interface()

        draw_effects(screen)


    elif game_state == "game_over":

        if not game_over_sound_played:

            game_over_sound.play()

            game_over_sound_played = True

        screen.fill(
            (25, 30, 45)
        )

        draw_game_over()


    pygame.display.flip()

    clock.tick(60)


if camera is not None:

    camera.release()

landmarker.close()

pygame.quit()