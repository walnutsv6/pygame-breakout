import pygame
from constants.constants import *

class Paddle:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2
        self.y = SCREEN_HEIGHT - PADDLE_HEIGHT - 20
        self.width = PADDLE_WIDTH  # パドル幅を管理する変数
        self.height = PADDLE_HEIGHT
        self.speed = 8
        
        # パドル画像の読み込み
        self.images = {}
        self.use_images = True
        try:
            self.images['left'] = pygame.image.load('game_resources/paddle_left.png')
            self.images['center'] = pygame.image.load('game_resources/paddle_center.png')
            self.images['right'] = pygame.image.load('game_resources/paddle_right.png')
        except (pygame.error, FileNotFoundError):
            self.use_images = False
    
    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        elif direction == "right" and self.x < SCREEN_WIDTH - self.width:  # widthを使用
            self.x += self.speed
    
    def move_to_mouse(self, mouse_x):
        # マウスの位置に合わせてパドルを移動（画面内に制限）
        self.x = max(0, min(mouse_x - self.width // 2, SCREEN_WIDTH - self.width))  # widthを使用
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)  # widthとheightを使用
    
    def draw(self, screen):
        rect = self.get_rect()
        
        if self.use_images:
            # 画像を使用した描画
            left_img = self.images['left']
            center_img = self.images['center']
            right_img = self.images['right']
            
            left_width = left_img.get_width()
            right_width = right_img.get_width()
            center_img_width = center_img.get_width()
            
            # パドルの幅が左右の画像の合計より小さい場合の処理
            if rect.width <= left_width + right_width:
                # 左端画像のみ描画（幅が足りない場合）
                if rect.width <= left_width:
                    # 左端画像をクリップして描画
                    clipped_left = pygame.Surface((rect.width, left_img.get_height()))
                    clipped_left.blit(left_img, (0, 0))
                    screen.blit(clipped_left, (rect.x, rect.y))
                else:
                    # 左端と右端を適切に配置
                    screen.blit(left_img, (rect.x, rect.y))
                    remaining_width = rect.width - left_width
                    clipped_right = pygame.Surface((remaining_width, right_img.get_height()))
                    clipped_right.blit(right_img, (right_width - remaining_width, 0))
                    screen.blit(clipped_right, (rect.x + left_width, rect.y))
            else:
                # 通常の描画（左端、中央、右端）
                # 左端部分の描画
                screen.blit(left_img, (rect.x, rect.y))
                
                # 中央部分の描画（左端と右端の間を埋める）
                center_start_x = rect.x + left_width
                center_end_x = rect.x + rect.width - right_width
                center_width = center_end_x - center_start_x
                
                if center_width > 0:
                    # 中央画像を必要な幅だけ繰り返し描画
                    x = center_start_x
                    while x < center_end_x:
                        # 最後の部分で画像をクリップする必要がある場合
                        if x + center_img_width > center_end_x:
                            clip_width = center_end_x - x
                            clipped_center = pygame.Surface((clip_width, center_img.get_height()))
                            clipped_center.blit(center_img, (0, 0))
                            screen.blit(clipped_center, (x, rect.y))
                        else:
                            screen.blit(center_img, (x, rect.y))
                        x += center_img_width
                
                # 右端部分の描画
                screen.blit(right_img, (rect.x + rect.width - right_width, rect.y))
        else:
            # 従来の立体的なパドルの描画
            # メインのパドル（明るいグレー）
            pygame.draw.rect(screen, (200, 200, 200), rect)
            # 上側のハイライト（白）
            pygame.draw.rect(screen, WHITE, (rect.x, rect.y, rect.width, 4))
            # 左側のハイライト（白）
            pygame.draw.rect(screen, WHITE, (rect.x, rect.y, 4, rect.height))
            # 下側の影（暗いグレー）
            pygame.draw.rect(screen, (100, 100, 100), (rect.x, rect.y + rect.height - 4, rect.width, 4))
            # 右側の影（暗いグレー）
            pygame.draw.rect(screen, (100, 100, 100), (rect.x + rect.width - 4, rect.y, 4, rect.height))
