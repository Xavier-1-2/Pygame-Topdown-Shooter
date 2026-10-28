import pygame
from sys import exit
import math
import random
from player_data import *

pygame.init()

# Initialize mixer
pygame.mixer.init()

# Load and play background music
pygame.mixer.music.load("Audio/BgMusic.mp3")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)

# Load shooting sound
shoot_sound = pygame.mixer.Sound("Audio/ARSingleShot.mp3")
shoot_sound.set_volume(0.3)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Shooter')
clock = pygame.time.Clock()
font = pygame.font.Font("Fassero-Regular.otf", 36)

# Load Background
background = pygame.image.load('Sprites/ground.png').convert()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.pos = pygame.math.Vector2(playerstartx, playerstarty)
        self.angle = 0
        self.image = pygame.transform.rotozoom(
            pygame.image.load('Sprites/Player_Shotgun/move/survivor-move_shotgun_0.png').convert_alpha(),
            0,
            playersizewads
        )
        self.base_player_image = self.image
        self.rect = self.image.get_rect(center=self.pos)

        # Add smaller hitbox for better collisions
        self.hitbox_rect = self.rect.inflate(-40, -40)

        self.speed = playerspeed
        self.shoot = False
        self.shoot_cooldown = 0
        self.barreloffset = pygame.math.Vector2(gox, goy)

    def player_rotation(self):
        mouse_coords = pygame.mouse.get_pos()
        x_mouse_player = mouse_coords[0] - WIDTH // 2
        y_mouse_player = mouse_coords[1] - HEIGHT // 2
        self.angle = math.degrees(math.atan2(y_mouse_player, x_mouse_player))
        self.image = pygame.transform.rotate(self.base_player_image, -self.angle)
        self.rect = self.image.get_rect(center=self.hitbox_rect.center)

    def user_input(self):
        self.velocity_x = 0
        self.velocity_y = 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.velocity_y = -self.speed
        if keys[pygame.K_a]:
            self.velocity_x = -self.speed
        if keys[pygame.K_s]:
            self.velocity_y = self.speed
        if keys[pygame.K_d]:
            self.velocity_x = self.speed

        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)

        if pygame.mouse.get_pressed() == (1, 0, 0) or keys[pygame.K_q]:
            self.shoot = True
            self.isShooting()
        else:
            self.shoot = False

    def isShooting(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = ShotCooldown
            spawn_bul_pos = self.pos + self.barreloffset.rotate(self.angle)
            bullet = Bullet(spawn_bul_pos[0], spawn_bul_pos[1], self.angle)
            bullet_groups.add(bullet)
            all_sprite_groups.add(bullet)
            shoot_sound.play()

    def move(self):
        self.pos += pygame.math.Vector2(self.velocity_x, self.velocity_y)
        self.rect.center = self.pos
        self.hitbox_rect.center = self.pos  #  keep hitbox synced

    def update(self):
        self.user_input()
        self.move()
        self.player_rotation()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1



class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.image.load("Sprites/Bullet2.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, bulletsize)
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = bulletspeed
        self.x_vel = math.cos(math.radians(self.angle)) * self.speed
        self.y_vel = math.sin(math.radians(self.angle)) * self.speed
        self.bulletlife = bulletlife
        self.spawntime = pygame.time.get_ticks()

    def bullet_move(self):
        self.x += self.x_vel
        self.y += self.y_vel
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        if pygame.time.get_ticks() - self.spawntime > self.bulletlife:
            self.kill()

    def update(self):
        self.bullet_move()



class Enemy(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__(enemy_group, all_sprite_groups)
        self.image = pygame.image.load("Sprites/0.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, 2)
        self.rect = self.image.get_rect(center=position)

        # Smaller hitbox for more realistic collision
        self.hitbox_rect = self.rect.inflate(-30, -30)

        self.position = pygame.math.Vector2(position)
        self.direction = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.speed = enemyspeed
        self.health = 1

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False

    def track_player(self):
        player_vector = pygame.math.Vector2(player.hitbox_rect.center)
        enemy_vector = pygame.math.Vector2(self.hitbox_rect.center)
        distance = (player_vector - enemy_vector).magnitude()

        if distance > 0:
            self.direction = (player_vector - enemy_vector).normalize()
        else:
            self.direction = pygame.math.Vector2()

        self.velocity = self.direction * self.speed
        self.position += self.velocity
        self.rect.center = self.position
        self.hitbox_rect.center = self.position  #  keep hitbox synced

    def update(self):
        self.track_player()



class Camera(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.offset = pygame.math.Vector2()
        self.floor_rect = background.get_rect(topleft=(0, 0))

    def custom_draw(self):
        self.offset.x = player.rect.centerx - WIDTH // 2
        self.offset.y = player.rect.centery - HEIGHT // 2

        floor_offset_pos = self.floor_rect.topleft - self.offset
        screen.blit(background, floor_offset_pos)

        for sprite in all_sprite_groups:
            offset_pos = sprite.rect.topleft - self.offset
            screen.blit(sprite.image, offset_pos)

    @staticmethod
    def spawn_wave(wave_number):
        enemies_to_spawn = 3 + (wave_number - 1) * 2
        for i in range(enemies_to_spawn):
            side = i % 4
            if side == 0:
                pos = (0, random.randint(0, HEIGHT))
            elif side == 1:
                pos = (WIDTH, random.randint(0, HEIGHT))
            elif side == 2:
                pos = (random.randint(0, WIDTH), 0)
            else:
                pos = (random.randint(0, WIDTH), HEIGHT)
            Enemy(pos)



all_sprite_groups = pygame.sprite.Group()
bullet_groups = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

score = 0
player = Player()
all_sprite_groups.add(player)
enemy = Enemy((400, 400))
camera = Camera()

wave_in_progress = False
wave_delay_timer = 0
wave_delay_duration = 2000
wave_number = 1


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    all_sprite_groups.update()

    # Use hitbox collision instead of rect collision
    for enemy in enemy_group:
        if player.hitbox_rect.colliderect(enemy.hitbox_rect):
            # Game Over screen
            game_over = True
            while game_over:
                screen.fill((0, 0, 0))
                go_text = font.render("GAME OVER", True, (255, 0, 0))
                screen.blit(go_text, go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

                score_text = font.render(f"Score: {score}", True, (255, 255, 255))
                screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

                restart_text = font.render("Press SPACE to Restart", True, (200, 200, 200))
                screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))

                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        # Reset everything
                        score = 0
                        wave_number = 1
                        enemy_group.empty()
                        bullet_groups.empty()
                        all_sprite_groups.empty()
                        player = Player()
                        all_sprite_groups.add(player)
                        Enemy((400, 400))
                        game_over = False
    #  Bullet/Enemy Collisions
    hits = pygame.sprite.groupcollide(enemy_group, bullet_groups, False, True)
    for e in hits:
        e.take_damage(1)
        score += 1

    # Wave Management
    if not wave_in_progress and len(enemy_group) == 0:
        if wave_delay_timer == 0:
            wave_delay_timer = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - wave_delay_timer > wave_delay_duration:
            wave_number += 1
            camera.spawn_wave(wave_number)
            wave_in_progress = True
            wave_delay_timer = 0
    elif len(enemy_group) > 0:
        wave_in_progress = False

    camera.custom_draw()

    score_text = font.render(f"Score: {score}", True, "white")
    screen.blit(score_text, (20, 60))

    wave_text = font.render(f"Wave {wave_number}", True, "white")
    screen.blit(wave_text, (20, 20))

    pygame.display.update()
    clock.tick(60)
