import pygame
from constants.constants import *

class Item:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.item_type = item_type
        self.size = ITEM_SIZE
        self.fall_speed = ITEM_FALL_SPEED
        self.active = True
        
        # アイテムタイプごとの色と効果
        self.item_data = {
            "wide_paddle": {"color": GREEN, "symbol": "W", "image": "game_resources/item_wide.png"},
            "multi_ball": {"color": RED, "symbol": "M", "image": "game_resources/item_multi.png"},
            "slow_ball": {"color": GREEN, "symbol": "S", "image": "game_resources/item_slow.png"},
            "extra_life": {"color": BLUE, "symbol": "B", "image": "game_resources/item_extra.png"},
            "bonus_score": {"color": PURPLE, "symbol": "P", "image": "game_resources/item_point.png"},
            "power_ball": {"color": ORANGE, "symbol": "F", "image": "game_resources/item_power.png"},
            "paddle_shot": {"color": CYAN, "symbol": "A", "image": "game_resources/item_shot.png"}
        }
        
        # 画像の読み込み
        self.image = None
        self.load_image()
    
    def load_image(self):
        """アイテム画像を読み込む"""
        try:
            image_path = self.item_data[self.item_type]["image"]
            self.image = pygame.image.load(image_path)
            # アイテムサイズにスケール
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        except (pygame.error, FileNotFoundError):
            # 画像読み込みに失敗した場合は None のまま
            self.image = None
    
    def update(self):
        if self.active:
            self.y += self.fall_speed
            # 画面下に落ちたら非アクティブ化
            if self.y > SCREEN_HEIGHT:
                self.active = False
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
    
    def draw(self, screen):
        if self.active:
            data = self.item_data[self.item_type]
            rect = self.get_rect()
            
            # 画像が読み込まれている場合は画像を表示
            if self.image:
                image_rect = self.image.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(self.image, image_rect)
            else:
                # 画像がない場合は従来の描画方法
                # アイテムの背景（円）
                pygame.draw.circle(screen, data["color"], (int(self.x), int(self.y)), self.size//2)
                pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size//2, 2)
                
                # アイテムのシンボル
                try:
                    font = pygame.font.Font("PixelMplus12-Regular.ttf", 20)
                except (pygame.error, FileNotFoundError):
                    font = pygame.font.Font(None, 20)
                text = font.render(data["symbol"], True, WHITE)
                text_rect = text.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(text, text_rect)
