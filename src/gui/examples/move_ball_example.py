import pygame

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0
DELTA_T_TO_POS_SCALING = 300
pastel_white = pygame.Color("#faf8f6")
pastel_rose = pygame.Color("#f6b8d0")

player_pos = pygame.Vector2(
    x=screen.get_width() / 2, 
    y=screen.get_height() / 2
)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from the last frame
    screen.fill(color=pastel_white)

    # Render your game here
    pygame.draw.circle(
        surface=screen, 
        color=pastel_rose, 
        center=player_pos, 
        radius=40
    )

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_pos.y -= DELTA_T_TO_POS_SCALING * dt
    if keys[pygame.K_s]:
        player_pos.y += DELTA_T_TO_POS_SCALING * dt
    if keys[pygame.K_a]:
        player_pos.x -= DELTA_T_TO_POS_SCALING * dt
    if keys[pygame.K_d]:
        player_pos.x += DELTA_T_TO_POS_SCALING * dt

    # flip the display to put your work on screen
    pygame.display.flip()

    # limit FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics
    dt = clock.tick(60) / 1000 # limit FPS to 60

pygame.quit()