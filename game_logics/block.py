import pygame
from constants.constants import *

class Block:
    def __init__(self, x, y, durability, foreground_surface, background_surface):
        self.x = x
        self.y = y
        self.durability = durability  # ブロックの耐久性（破壊に必要なヒット数）
        self.max_durability = durability  # 初期耐久性を保存
        self.destroyed = False
        self.foreground_surface = foreground_surface
        self.background_surface = background_surface
        
        # フォントの設定（耐久性表示用）
        try:
            self.font = pygame.font.Font("PixelMplus12-Regular.ttf", 18)
        except (pygame.error, FileNotFoundError):
            self.font = pygame.font.Font(None, 18)
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)
    
    def hit(self):
        """ブロックがヒットされた時の処理"""
        if not self.destroyed:
            self.durability -= 1
            if self.durability <= 0:
                self.destroyed = True
                return True  # ブロックが破壊された
        return False  # ブロックはまだ残っている
    
    def draw(self, screen):
        if not self.destroyed:
            rect = self.get_rect()
            
            # ブロックがある場合：前景画像の該当部分を表示
            fg_section = self.foreground_surface.subsurface(rect)
            screen.blit(fg_section, (self.x, self.y))
            
            # ブロックの境界を薄く縁取り
            pygame.draw.rect(screen, (80, 80, 80), rect, 1)
            
            # 耐久性が2以上の場合は数字を表示
            if self.durability >= 2:
                # 耐久性に応じて色を変える
                if self.durability >= 5:
                    text_color = RED
                elif self.durability >= 3:
                    text_color = ORANGE
                else:
                    text_color = YELLOW
                
                text = self.font.render(str(self.durability), True, text_color)
                text_rect = text.get_rect(center=(self.x + BLOCK_SIZE//2, self.y + BLOCK_SIZE//2))
                
                # 文字の背景に黒い縁取りを追加（視認性向上）
                outline_color = BLACK
                for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                    outline_text = self.font.render(str(self.durability), True, outline_color)
                    screen.blit(outline_text, (text_rect.x + dx, text_rect.y + dy))
                
                screen.blit(text, text_rect)
    
    def draw_paused(self, screen):
        """ポーズ中の描画（耐久度表示なし、枠線なし）"""
        if not self.destroyed:
            rect = self.get_rect()
            
            # ブロックがある場合：前景画像の該当部分のみを表示
            fg_section = self.foreground_surface.subsurface(rect)
            screen.blit(fg_section, (self.x, self.y))
