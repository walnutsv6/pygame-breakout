import pygame
from constants.constants import *

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = BULLET_SIZE
        self.speed = BULLET_SPEED
        self.active = True
        
        # 弾の画像を読み込み
        try:
            self.image = pygame.image.load("game_resources/bullet.png")
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
            self.use_image = True
        except (pygame.error, FileNotFoundError):
            self.use_image = False
    
    def update(self):
        if self.active:
            self.y -= self.speed
            # 画面上端に到達したら非アクティブ化
            if self.y < GAME_AREA_Y:
                self.active = False
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
    
    def draw(self, screen):
        if self.active:
            center_x = int(self.x)
            center_y = int(self.y)
            
            if self.use_image:
                # 画像を使用して描画
                rect = self.get_rect()
                screen.blit(self.image, rect)
            else:
                # 従来の描画処理（フォールバック）
                radius = self.size//2
                pygame.draw.circle(screen, CYAN, (center_x, center_y), radius)
                pygame.draw.circle(screen, DARKGRAY, (center_x, center_y), radius, 1)
