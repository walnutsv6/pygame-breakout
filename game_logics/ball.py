import pygame
import math
import random
from constants.constants import *

class Ball:
    def __init__(self, paddle_x=None, ball_speed=BALL_SPEED_INITIAL):
        if paddle_x is not None:
            # パドルの上にボールを配置
            self.x = paddle_x + PADDLE_WIDTH // 2 - BALL_SIZE // 2
            self.y = SCREEN_HEIGHT - PADDLE_HEIGHT - 20 - BALL_SIZE - 5
        else:
            self.x = SCREEN_WIDTH // 2
            self.y = SCREEN_HEIGHT // 2
        
        # 現在のボール速度を保存
        self.current_speed = ball_speed
        
        # ベクトルを使用した速度管理
        initial_angle = random.uniform(-math.pi/4, math.pi/4)  # -45度から45度の範囲
        self.velocity_x = self.current_speed * math.sin(initial_angle)
        self.velocity_y = -self.current_speed * math.cos(initial_angle)  # 上向きに発射
        
        self.size = BALL_SIZE
        self.stuck_to_paddle = True  # ボールがパドルに固定されているかどうか
        self.power_ball = False  # パワーボール状態かどうか
    
    def move(self, paddle=None):
        if self.stuck_to_paddle and paddle:
            # パドルに固定されている場合はパドルと一緒に移動
            self.x = paddle.x + paddle.width // 2 - BALL_SIZE // 2  # paddle.widthを使用
            self.y = paddle.y - BALL_SIZE - 5
        else:
            # 通常の移動
            self.x += self.velocity_x
            self.y += self.velocity_y
    
    def release(self):
        # ボールをパドルから解放
        self.stuck_to_paddle = False
    
    def normalize_velocity(self):
        # 速度ベクトルを正規化して一定の速度を保つ
        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if current_speed > 0:
            self.velocity_x = (self.velocity_x / current_speed) * self.current_speed
            self.velocity_y = (self.velocity_y / current_speed) * self.current_speed
    
    def update_speed(self, new_speed):
        # ボールの速度を更新
        self.current_speed = new_speed
        # 現在の速度ベクトルを新しい速度で正規化
        self.normalize_velocity()
    
    def bounce_wall(self):
        # 左右の壁との衝突判定と位置修正
        if self.x <= 0:
            self.x = 0  # 左の壁にめり込まないよう位置を修正
            self.velocity_x = abs(self.velocity_x)  # 右向きに修正
        elif self.x >= SCREEN_WIDTH - self.size:
            self.x = SCREEN_WIDTH - self.size  # 右の壁にめり込まないよう位置を修正
            self.velocity_x = -abs(self.velocity_x)  # 左向きに修正
        
        # 上の壁との衝突判定と位置修正
        if self.y <= GAME_AREA_Y:  # セーフエリアを考慮した上壁判定
            self.y = GAME_AREA_Y  # 上の壁にめり込まないよう位置を修正
            self.velocity_y = abs(self.velocity_y)  # 下向きに修正
        
        # 速度を正規化して一定の速度を保つ
        self.normalize_velocity()
    
    def bounce_paddle(self, paddle):
        if self.stuck_to_paddle:
            return False
            
        ball_rect = self.get_rect()
        paddle_rect = paddle.get_rect()
        
        if ball_rect.colliderect(paddle_rect):
            # パドルのどの位置で跳ね返るかによって角度を変える
            hit_pos = (self.x + self.size/2 - paddle.x) / paddle.width  # paddle.widthを使用
            hit_pos = max(0, min(1, hit_pos))  # 0-1の範囲に制限
            
            # 反射角度を計算（-60度から60度の範囲）
            angle = (hit_pos - 0.5) * (2 * math.pi/3)  # -π/3 から π/3
            
            # 新しい速度ベクトルを計算
            self.velocity_x = self.current_speed * math.sin(angle)
            self.velocity_y = -self.current_speed * math.cos(angle)  # 常に上向き
            
            return True
        return False
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
    def draw(self, screen):
        center_x = int(self.x + self.size//2)
        center_y = int(self.y + self.size//2)
        radius = self.size//2
        
        # 立体的なボールの描画
        # 濃いグレーの縁取り
        pygame.draw.circle(screen, (50, 50, 50), (center_x, center_y), radius + 1)
        
        # パワーボール状態の場合はオレンジ色に
        if self.power_ball:
            # メインのボール（オレンジ）
            pygame.draw.circle(screen, ORANGE, (center_x, center_y), radius)
            # ハイライト（黄色）
            highlight_offset = radius // 3
            pygame.draw.circle(screen, YELLOW, (center_x - highlight_offset, center_y - highlight_offset), radius // 3)
            # 影の効果（暗いオレンジ）
            shadow_offset = radius // 4
            pygame.draw.circle(screen, (150, 100, 0), (center_x + shadow_offset, center_y + shadow_offset), radius // 4)
        else:
            # メインのボール（明るいグレー）
            pygame.draw.circle(screen, (220, 220, 220), (center_x, center_y), radius)
            # ハイライト（白い小さな円）
            highlight_offset = radius // 3
            pygame.draw.circle(screen, WHITE, (center_x - highlight_offset, center_y - highlight_offset), radius // 3)
            # 影の効果（暗いグレーの小さな円）
            shadow_offset = radius // 4
            pygame.draw.circle(screen, (150, 150, 150), (center_x + shadow_offset, center_y + shadow_offset), radius // 4)
    
    def is_out_of_bounds(self):
        return self.y > SCREEN_HEIGHT
