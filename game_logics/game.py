import pygame
import sys
import random
import math
import json
import csv
import os
from constants.block_colors import BLOCK_COLORS
from constants.constants import *
from game_logics.paddle import Paddle
from game_logics.ball import Ball
from game_logics.bullet import Bullet
from game_logics.item import Item
from game_logics.block import Block
from save_manager import SaveManager

class Game:
    def __init__(self, game_config):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.clock = pygame.time.Clock()
        
        # ゲーム設定（キャラクター情報と難易度設定を含む）
        self.selected_chara = game_config['chara']
        self.difficulty_key = game_config['difficulty']
        self.difficulty_settings = game_config['difficulty_settings']
        
        # セーブデータ管理クラスの初期化
        self.save_manager = SaveManager()
        
        # 選択されたキャラクターのステージデータを読み込み
        self.stage_data = self.save_manager.load_stage_data(self.selected_chara["folder"])
        self.current_stage_index = 0
        self.current_stage_config = None
        
        # 現在のステージ設定を初期化
        self.load_current_stage_config()
        
        # ステージ管理（互換性のため）
        self.current_stage = self.current_stage_config["stage"]
        
        # ウィンドウタイトルを更新
        self.update_window_title()

        # 難易度設定に基づいてボール数を設定
        self.lives = self.difficulty_settings['balls'] - 1  # 残りボール数（現在のボールは含まない）
        self.blocks_destroyed = 0  # 破壊したブロック数
        # 難易度設定に基づいてボール速度を設定
        self.current_ball_speed = self.difficulty_settings['initial_ball_speed']
        self.max_ball_speed = self.difficulty_settings['max_ball_speed']
        self.combo_count = 0  # 連続破壊カウント
        self.combo_display_timer = 0  # コンボ表示用タイマー（30フレーム = 0.5秒）
        
        # 前景画像の読み込み
        try:
            foreground_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['foreground']}"
            self.foreground = pygame.image.load(foreground_path)
            self.foreground = pygame.transform.scale(self.foreground, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"前景画像が見つかりません。白い前景を使用します。")
            self.foreground = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.foreground.fill(WHITE)
        
        # 背景画像の読み込み
        try:
            background_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['background']}"
            self.background = pygame.image.load(background_path)
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"背景画像が見つかりません。元の背景を使用します。")
            try:
                self.background = pygame.image.load("back.png")
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except (pygame.error, FileNotFoundError):
                self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background.fill(BLACK)
        
        self.paddle = Paddle()
        self.balls = [Ball(self.paddle.x, self.current_ball_speed)]  # ボールを配列で管理
        self.blocks = []
        self.items = []  # アイテムのリスト
        self.score = 0
        self.last_item_score = 0  # 最後にアイテムを出現させたスコア
        
        # アイテム効果の状態管理
        self.paddle_wide_timer = 0
        self.ball_slow_timer = 0
        self.power_ball_timer = 0  # パワーボール効果のタイマー
        self.paddle_shot_count = 0  # パドルショットの残り回数
        self.bullets = []  # パドルショットの弾丸リスト
        self.original_paddle_width = PADDLE_WIDTH
        
        # アイテム効果の待機リスト（ボール打ち出し前に取得したアイテム）
        self.pending_item_effects = []
        
        # ゲーム状態管理
        self.game_state = "playing"  # "playing", "paused", "game_over", "stage_clear", "game_clear", "special_reward"
        self.stage_clear_timer = 0  # ステージクリア表示用タイマー
        self.start_time = pygame.time.get_ticks()  # ゲーム開始時刻
        self.end_time = None  # ゲーム終了時刻
        self.show_special_reward = False  # 特別報酬表示フラグ
        self.current_bonus_type = "bonus"  # 現在表示中のボーナス種類 ("bonus" or "bonus2")
        self.pause_start_time = None  # ポーズ開始時刻
        self.total_pause_time = 0  # 総ポーズ時間
        
        # フォントの設定
        try:
            self.font = pygame.font.Font("PixelMplus12-Regular.ttf", 24)
            self.small_font = pygame.font.Font("PixelMplus12-Regular.ttf", 18)
        except (pygame.error, FileNotFoundError):
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        
        self.create_blocks()
    
    def get_speed_percentage(self):
        """現在のボールスピードを0-100%で表示するためのパーセンテージを計算"""
        initial_speed = self.difficulty_settings['initial_ball_speed']
        max_speed = self.max_ball_speed
        
        # 初期値を0%、最大値を100%とする
        if max_speed <= initial_speed:
            return 0  # 最大値が初期値以下の場合は0%
        
        speed_range = max_speed - initial_speed
        current_increase = self.current_ball_speed - initial_speed
        percentage = int((current_increase / speed_range) * 100)
        
        return max(0, min(100, percentage))  # 0-100%の範囲に制限
    
    def can_emergency_clear(self):
        """緊急ステージクリアが可能かどうかを判定"""
        # 難易度がEasyまたはNormalでない場合は無効
        if self.difficulty_settings['name'] not in ["Easy", "Normal"]:
            return False
        
        # 制限時間を過ぎているかチェック
        if self.game_state == "playing":
            current_time = pygame.time.get_ticks()
            play_time_seconds = (current_time - self.start_time) / 1000
            if play_time_seconds <= self.current_stage_config["target_time"]:
                return False
        
        # 残りブロック数をチェック
        remaining_blocks = sum(1 for block in self.blocks if not block.destroyed)
        if remaining_blocks > 5:
            return False
        
        return True
    
    def update_window_title(self):
        """ウィンドウタイトルを現在のキャラクター名とステージ、難易度で更新"""
        title = f"{self.selected_chara['name']} - Stage {self.current_stage} ({self.difficulty_settings['name']})"
        pygame.display.set_caption(title)
    
    def create_blocks(self):
        # CSVファイルからブロック配置を読み込み
        csv_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['definition']}.csv"
        block_layout = self.load_block_layout_from_csv(csv_path)
        
        # ブロック配置ファイルから配置情報を読み込んで配置
        for row in range(len(block_layout)):
            for col in range(len(block_layout[row])):
                durability = block_layout[row][col]
                # 0（透明）の場合はブロックを配置しない
                if durability != 0:
                    # 難易度設定に基づいてブロック強度を調整
                    adjusted_durability = durability + self.difficulty_settings['block_strength_adjustment']
                    # 最小値は1に制限
                    adjusted_durability = max(1, adjusted_durability)
                    
                    x = col * BLOCK_SIZE
                    y = row * BLOCK_SIZE + GAME_AREA_Y  # セーフエリア分をオフセット
                    self.blocks.append(Block(x, y, adjusted_durability, self.foreground, self.background))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                # Escキーの処理
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        # ゲーム中の場合はポーズ
                        self.pause_game()
                    elif self.game_state == "paused":
                        # ポーズ中の場合はステージセレクトに戻る
                        return "back_to_select"
                    else:
                        # その他の状態では元の動作（ステージセレクトに戻る）
                        return "back_to_select"
                
                # ポーズ中のキー処理
                elif self.game_state == "paused":
                    # Esc以外のキーでゲーム再開
                    self.resume_game()
                
                # ゲーム中の他のキー処理
                elif self.game_state == "playing":
                    # Oキーで緊急ステージクリア（Easy/Normal、制限時間超過、残りブロック5個以下の場合）
                    if event.key == pygame.K_o:
                        if self.can_emergency_clear():
                            # 残りブロックを全て破壊
                            for block in self.blocks:
                                if not block.destroyed:
                                    block.destroyed = True
                            print("緊急ステージクリア発動！")
                    # テスト用チート機能（削除予定）
                    elif event.key == pygame.K_F1:  # F1キーでテスト用チート発動
                        # 全ブロックを破壊
                        for block in self.blocks:
                            block.destroyed = True
                        # スコアを100000に設定
                        self.score = 100000
                        print("チート発動: 全ブロック破壊 & スコア100000設定")
                    elif event.key == pygame.K_F2:  # F2キーでテスト用チート発動
                        # 全ブロックを破壊
                        for block in self.blocks:
                            block.destroyed = True
                        print("チート発動: 全ブロック破壊")
                        
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    if self.game_state == "paused":
                        # ポーズ中の左クリックでゲーム再開
                        self.resume_game()
                    elif self.game_state == "playing":
                        # パドルショットがある場合は弾を発射
                        if self.paddle_shot_count > 0:
                            self.fire_paddle_shot()
                        else:
                            # パドルショットがない場合はボールを解放
                            for ball in self.balls:
                                if ball.stuck_to_paddle:
                                    ball.release()
                            
                            # ボール打ち出し時に待機中のアイテム効果を発動
                            for item_type in self.pending_item_effects:
                                self.activate_item_effect(item_type)
                            self.pending_item_effects.clear()
                    elif self.game_state == "game_over":
                        # ゲームオーバー時：Extremeの場合は最初から、それ以外はステージをリトライ
                        if self.difficulty_settings['name'] == "Extreme":
                            self.reset_game()
                        else:
                            self.retry_stage()
                    elif self.game_state == "stage_clear":
                        # ステージクリア時：目標スコア以上でボーナス画像があり、難易度設定でボーナス画像が有効なら特別報酬、そうでなければ次のステージに進む
                        if (self.score >= self.current_stage_config["target_score"] and 
                            self.current_stage_config["bonus"] and 
                            self.difficulty_settings['get_bonus_image']):
                            self.show_special_reward_screen()
                        else:
                            self.next_stage()
                    elif self.game_state == "game_clear":
                        # ゲームクリア時：目標スコア以上でボーナス画像があり、難易度設定でボーナス画像が有効なら特別報酬、そうでなければキャラクター選択画面に戻る
                        if (self.score >= self.current_stage_config["target_score"] and 
                            self.current_stage_config["bonus"] and 
                            self.difficulty_settings['get_bonus_image']):
                            self.show_special_reward_screen()
                        else:
                            return "back_to_select"
                    elif self.game_state == "special_reward":
                        # 特別報酬画面：次のボーナス画像があるかチェック
                        if self.can_show_next_bonus():
                            # bonus2を表示
                            self.show_next_bonus()
                        else:
                            # 次のボーナス画像がない場合：最終ステージならキャラクター選択画面に戻る、そうでなければ次のステージに進む
                            if self.current_stage_index + 1 < len(self.stage_data):
                                self.next_stage()
                            else:
                                return "back_to_select"
        
        # ゲーム中のみパドル操作を受け付ける
        if self.game_state == "playing":
            # マウスの位置でパドルを操作
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.paddle.move_to_mouse(mouse_x)
            
            # キーボードでの操作も維持
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.paddle.move("left")
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.paddle.move("right")
            
            # スペースキーでパドルショット発射
            if keys[pygame.K_SPACE] and self.paddle_shot_count > 0:
                self.fire_paddle_shot()
        
        return True
    
    def pause_game(self):
        """ゲームをポーズする"""
        if self.game_state == "playing":
            self.game_state = "paused"
            self.pause_start_time = pygame.time.get_ticks()
            print("ゲームをポーズしました")
    
    def resume_game(self):
        """ゲームを再開する"""
        if self.game_state == "paused":
            self.game_state = "playing"
            # ポーズ時間を累積
            if self.pause_start_time:
                pause_duration = pygame.time.get_ticks() - self.pause_start_time
                self.total_pause_time += pause_duration
                self.pause_start_time = None
            print("ゲームを再開しました")
    
    def update(self):
        # ポーズ中は更新処理をスキップ
        if self.game_state == "paused":
            return
            
        # ステージクリア中のタイマー処理
        if self.game_state == "stage_clear":
            self.stage_clear_timer -= 1
            if self.stage_clear_timer <= 0:
                self.next_stage()
            return
        
        # ゲーム中のみ更新処理を実行
        if self.game_state != "playing":
            return
            
        # 全てのボールを更新
        for ball in self.balls:
            ball.move(self.paddle)
        
        # アイテム効果のタイマー更新
        self.update_item_effects()
        
        # コンボ表示タイマーを更新
        if self.combo_display_timer > 0:
            self.combo_display_timer -= 1
        
        # アイテムの更新
        for item in self.items[:]:  # コピーを作成してループ
            item.update()
            if not item.active:
                self.items.remove(item)
        
        # 弾丸の更新
        for bullet in self.bullets[:]:  # コピーを作成してループ
            bullet.update()
            if not bullet.active:
                self.bullets.remove(bullet)
        
        # 各ボールの物理演算
        balls_to_remove = []
        for ball in self.balls:
            if not ball.stuck_to_paddle:
                ball.bounce_wall()
                
                # パドルとの衝突判定
                if ball.bounce_paddle(self.paddle):
                    # パドルで跳ね返した時にコンボをリセット
                    self.combo_count = 0
                    self.combo_display_timer = 0
                
                # ブロックとの衝突判定
                ball_rect = ball.get_rect()
                for block in self.blocks:
                    if not block.destroyed and ball_rect.colliderect(block.get_rect()):
                        # パワーボール状態の場合は耐久度を2削る
                        if ball.power_ball:
                            block.durability -= 2
                            if block.durability <= 0:
                                block.destroyed = True
                                block_destroyed = True
                            else:
                                block_destroyed = False
                            
                            # パワーボールは貫通するので反射しない
                            
                        else:
                            # 通常のボール：ブロックにヒット
                            block_destroyed = block.hit()
                            
                            # ブロックとの衝突方向を判定して適切に反射
                            block_rect = block.get_rect()
                            ball_center_x = ball.x + ball.size / 2
                            ball_center_y = ball.y + ball.size / 2
                            block_center_x = block_rect.centerx
                            block_center_y = block_rect.centery
                            
                            # 衝突面を判定
                            dx = ball_center_x - block_center_x
                            dy = ball_center_y - block_center_y
                            
                            if abs(dx) > abs(dy):
                                # 左右の面で衝突
                                ball.velocity_x = -ball.velocity_x
                            else:
                                # 上下の面で衝突
                                ball.velocity_y = -ball.velocity_y
                            
                            # 速度を正規化
                            ball.normalize_velocity()
                        
                        # ブロックにヒットした場合はコンボを更新
                        self.combo_count += 1
                        self.combo_display_timer = 30  # 0.5秒間表示（60fps × 0.5秒）
                        
                        # ブロックが破壊された場合のスコア計算
                        if block_destroyed:
                            score_gained = self.calculate_score(is_power_ball=ball.power_ball)
                            self.score += self.apply_score_adjustment(score_gained)
                            self.blocks_destroyed += 1
                            
                            # アイテム出現判定
                            self.check_item_spawn(block.x + BLOCK_SIZE//2, block.y + BLOCK_SIZE//2)
                            
                            # ブロック破壊数に応じて速度を上昇
                            self.check_speed_increase()
                        else:
                            # ブロックが破壊されなかった場合は(10-残り耐久度)点を素点として計算
                            base_damage_score = 10 - block.durability
                            score_gained = self.calculate_score(base_damage_score, is_power_ball=ball.power_ball)
                            self.score += self.apply_score_adjustment(score_gained)
                        
                        # 通常のボールの場合のみ反射処理のためbreak
                        if not ball.power_ball:
                            break
                
                # ボールが画面下に落ちた場合
                if ball.is_out_of_bounds():
                    balls_to_remove.append(ball)
        
        # 弾丸とブロックの衝突判定
        for bullet in self.bullets[:]:
            if bullet.active:
                bullet_rect = bullet.get_rect()
                for block in self.blocks:
                    if not block.destroyed and bullet_rect.colliderect(block.get_rect()):
                        # ブロックにヒット
                        block_destroyed = block.hit()
                        bullet.active = False
                        
                        # ブロックにヒットした場合はコンボを更新
                        self.combo_count += 1
                        self.combo_display_timer = 30  # 0.5秒間表示（60fps × 0.5秒）
                        
                        # ブロックが破壊された場合のスコア計算
                        if block_destroyed:
                            score_gained = self.calculate_score()
                            self.score += self.apply_score_adjustment(score_gained)
                            self.blocks_destroyed += 1
                            
                            # アイテム出現判定
                            self.check_item_spawn(block.x + BLOCK_SIZE//2, block.y + BLOCK_SIZE//2)
                            
                            # ブロック破壊数に応じて速度を上昇
                            self.check_speed_increase()
                        else:
                            # ブロックが破壊されなかった場合は(10-残り耐久度)点を素点として計算
                            base_damage_score = 10 - block.durability
                            score_gained = self.calculate_score(base_damage_score)
                            self.score += self.apply_score_adjustment(score_gained)
                        
                        break
        
        # 画面外に落ちたボールを削除
        for ball in balls_to_remove:
            self.balls.remove(ball)
        
        # 全てのボールが落ちた場合
        if not self.balls:
            if self.lives > 0:
                self.lives -= 1
                # ボール速度を初期値に戻す
                self.current_ball_speed = self.difficulty_settings['initial_ball_speed']
                # ブロック破壊数をリセット
                self.blocks_destroyed = 0
                # コンボカウントをリセット
                self.combo_count = 0
                self.combo_display_timer = 0
                # アイテム効果をすべてリセット
                self.reset_item_effects()
                self.reset_ball()
            else:
                self.game_over()
        
        # アイテムとパドルの衝突判定
        self.check_item_collision()
        
        # すべてのブロックが破壊された場合
        if all(block.destroyed for block in self.blocks):
            # 最終ステージかどうかを判定
            if self.current_stage_index + 1 < len(self.stage_data):
                # 最終ステージではない場合
                self.stage_clear()
            else:
                # 最終ステージの場合
                self.game_clear()
    
    def check_item_spawn(self, x, y):
        # スコア100点ごとにアイテムを出現させる
        if self.score - self.last_item_score >= ITEM_SCORE_THRESHOLD:
            self.last_item_score = self.score
            
            # 難易度設定に基づいてアイテムタイプを選択
            available_items = self.difficulty_settings['items_enable']
            if available_items:  # 利用可能なアイテムがある場合のみ
                item_type = random.choice(available_items)
                
                # アイテムを作成
                item = Item(x, y, item_type)
                self.items.append(item)
    
    def check_item_collision(self):
        paddle_rect = self.paddle.get_rect()
        for item in self.items[:]:
            if item.active and item.get_rect().colliderect(paddle_rect):
                self.activate_item_effect(item.item_type)
                item.active = False
                self.items.remove(item)
    
    def activate_item_effect(self, item_type):
        # ボールが固定されている場合は効果を待機リストに追加
        if any(ball.stuck_to_paddle for ball in self.balls):
            self.pending_item_effects.append(item_type)
            return
        
        if item_type == "wide_paddle":
            # パドルを30%拡大、10秒間
            self.paddle.width = int(self.original_paddle_width * 1.3)  # paddleのwidthプロパティを使用
            self.paddle_wide_timer = 600  # 60fps × 10秒
            
        elif item_type == "multi_ball":
            # マルチボール効果：新しいボールを追加
            if len(self.balls) < 5:  # 最大5個まで
                new_ball = Ball(self.paddle.x, self.current_ball_speed)
                new_ball.stuck_to_paddle = False  # 即座に動き出す
                # 異なる角度で発射
                angle = random.uniform(-math.pi/3, math.pi/3)
                new_ball.velocity_x = new_ball.current_speed * math.sin(angle)
                new_ball.velocity_y = -new_ball.current_speed * math.cos(angle)
                self.balls.append(new_ball)
            # すでに5個以上ボールがある場合、ライフ+1（HardやExtremeでは行わない）
            elif self.difficulty_settings['name'] == "Easy" or self.difficulty_settings['name'] != "Normal":
                self.lives += 1
            
        elif item_type == "slow_ball":
            # ボール速度を30%低下、8秒間
            for ball in self.balls:
                ball.current_speed *= 0.7
                ball.normalize_velocity()
            self.ball_slow_timer = 480  # 60fps × 8秒
            
        elif item_type == "extra_life":
            # ライフ+1
            self.lives += 1
            
        elif item_type == "bonus_score":
            # ボーナススコア
            # 現在のスピード* 25点を加算
            bonus_score = int(self.current_ball_speed * 25)
            self.score += self.apply_score_adjustment(bonus_score)
            
        elif item_type == "power_ball":
            # パワーボール効果：ボールの破壊力アップ、6秒間
            for ball in self.balls:
                ball.power_ball = True
            self.power_ball_timer = 360  # 60fps × 6秒
            
        elif item_type == "paddle_shot":
            # パドルショット効果：6回分の弾丸を追加（最大6発まで）
            self.paddle_shot_count = min(self.paddle_shot_count + 6, 6)
    
    def update_item_effects(self):
        # パドル拡大効果のタイマー
        if self.paddle_wide_timer > 0:
            self.paddle_wide_timer -= 1
            if self.paddle_wide_timer == 0:
                self.paddle.width = self.original_paddle_width  # paddleのwidthプロパティを使用
        
        # ボール減速効果のタイマー
        if self.ball_slow_timer > 0:
            self.ball_slow_timer -= 1
            if self.ball_slow_timer == 0:
                for ball in self.balls:
                    ball.current_speed = self.current_ball_speed
                    ball.normalize_velocity()
        
        # パワーボール効果のタイマー
        if self.power_ball_timer > 0:
            self.power_ball_timer -= 1
            if self.power_ball_timer == 0:
                # 全ボールのパワーボール効果を解除
                for ball in self.balls:
                    ball.power_ball = False
    
    def reset_item_effects(self):
        """ミス時にすべてのアイテム効果をリセットする"""
        # パドル拡大効果のリセット
        self.paddle.width = self.original_paddle_width
        self.paddle_wide_timer = 0
        
        # ボール減速効果のリセット
        self.ball_slow_timer = 0
        for ball in self.balls:
            ball.current_speed = self.current_ball_speed
            ball.normalize_velocity()
        
        # パワーボール効果のリセット
        self.power_ball_timer = 0
        for ball in self.balls:
            ball.power_ball = False
        
        # パドルショット効果のリセット
        self.paddle_shot_count = 0
        self.bullets = []
        
        # 待機中のアイテム効果もリセット
        self.pending_item_effects.clear()
    
    def fire_paddle_shot(self):
        """パドルから弾丸を発射する"""
        if self.paddle_shot_count > 0:
            # マウスのX座標から弾丸を発射
            mouse_x, mouse_y = pygame.mouse.get_pos()
            bullet_x = mouse_x
            bullet_y = self.paddle.y
            bullet = Bullet(bullet_x, bullet_y)
            self.bullets.append(bullet)
            self.paddle_shot_count -= 1
    
    def calculate_score(self, base_score=10, is_power_ball=False):
        # 基本スコア（引数で指定可能、デフォルトは10）
        
        # スピードボーナス（初期速度からの増加分×5）
        speed_bonus = (self.current_ball_speed - self.difficulty_settings['initial_ball_speed']) * 5
        
        # コンボボーナス（連続破壊数×2）
        combo_bonus = (self.combo_count - 1) * 2
        
        total_score = base_score + speed_bonus + combo_bonus
        
        # パワーボール有効時はスコアを半分にする
        if is_power_ball:
            total_score = total_score // 2
        
        return max(total_score, base_score // 2 if is_power_ball else base_score)  # 最低スコアもパワーボール時は半分
    
    def apply_score_adjustment(self, score):
        """難易度設定に基づいてスコアを調整"""
        return int(score * self.difficulty_settings['score_adjustment'])
    
    def check_speed_increase(self):
        # ブロック破壊数に応じてボール速度を上昇させる
        speed_level = self.blocks_destroyed // BLOCKS_PER_SPEED_UP
        new_speed = min(self.difficulty_settings['initial_ball_speed'] + (speed_level * BALL_SPEED_INCREMENT), self.max_ball_speed)
        
        if new_speed > self.current_ball_speed:
            self.current_ball_speed = new_speed
            for ball in self.balls:
                # slow_ball効果が適用中の場合は、新しい速度に0.7倍を適用
                if self.ball_slow_timer > 0:
                    ball.current_speed = new_speed * 0.7
                else:
                    ball.current_speed = new_speed
                ball.normalize_velocity()
            print(f"ボール速度が上昇しました！ 現在の速度: {self.current_ball_speed}")
    
    def reset_ball(self):
        self.balls = [Ball(self.paddle.x, self.current_ball_speed)]
    
    def game_over(self):
        self.game_state = "game_over"
        self.end_time = pygame.time.get_ticks()
        
        # セーブデータを更新（ハイスコア更新も含む）
        self.update_save_data()
        
        print(f"ゲームオーバー！ スコア: {self.score}")
    
    def game_clear(self):
        self.game_state = "game_clear"
        self.end_time = pygame.time.get_ticks()
        
        # クリア時のボーナススコア計算
        bonus_score = self.calculate_clear_bonus()
        self.last_bonus_score = bonus_score  # ボーナススコア情報を保存
        self.score += self.apply_score_adjustment(bonus_score)
        
        # セーブデータを更新
        self.update_save_data()
        
        print(f"ゲームクリア！ 最終スコア: {self.score}")
    
    def show_special_reward_screen(self):
        """特別報酬画面を表示する"""
        self.game_state = "special_reward"
        
        # セーブデータを更新（特別報酬画面表示時）
        self.update_save_data()
        
        # 最初のボーナス画像を表示
        self.current_bonus_type = "bonus"
        self.load_bonus_image()
        
        print("特別報酬画面を表示します！")
    
    def load_bonus_image(self):
        """現在のボーナス種類に応じて画像を読み込む"""
        try:
            bonus_key = self.current_bonus_type
            bonus_filename = self.current_stage_config.get(bonus_key, "")
            
            if bonus_filename:
                bonus_path = f"{self.current_stage_config['folder']}/{bonus_filename}"
                self.background = pygame.image.load(bonus_path)
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print(f"{bonus_key}画像を読み込みました: {bonus_filename}")
            else:
                raise pygame.error(f"{bonus_key}画像が設定されていません")
        except (pygame.error, FileNotFoundError) as e:
            print(f"ボーナス画像の読み込みに失敗しました: {e}")
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill(YELLOW)  # 黄色い背景をフォールバックとして使用
    
    def can_show_next_bonus(self):
        """次のボーナス画像を表示できるかどうかを判定"""
        # bonus2とtarget_score2が設定されており、まだbonus2を表示していない場合
        if (self.current_bonus_type == "bonus" and 
            self.current_stage_config.get("bonus2", "") and 
            self.current_stage_config.get("target_score2", 0) > 0 and
            self.score >= self.current_stage_config["target_score2"]):
            return True
        return False
    
    def show_next_bonus(self):
        """次のボーナス画像を表示する"""
        if self.can_show_next_bonus():
            self.current_bonus_type = "bonus2"
            self.load_bonus_image()
            
            # ボーナス画像2表示時にセーブデータを更新
            self.update_save_data_for_bonus2()
            
            return True
        return False
    
    def stage_clear(self):
        """ステージクリア処理"""
        self.game_state = "stage_clear"
        self.stage_clear_timer = 180  # 3秒間（60fps × 3）
        self.end_time = pygame.time.get_ticks()
        
        # ステージクリア時のボーナススコア計算
        bonus_score = self.calculate_clear_bonus()
        self.last_bonus_score = bonus_score  # ボーナススコア情報を保存
        self.score += self.apply_score_adjustment(bonus_score)
        
        # セーブデータを更新
        self.update_save_data()
        
        print(f"ステージ{self.current_stage}クリア！")
    
    def next_stage(self):
        """次のステージに進む"""
        # 次のステージインデックスを計算
        if self.current_stage_index + 1 < len(self.stage_data):
            self.current_stage_index += 1
        else:
            # 全ステージクリアの場合
            print("全ステージクリア！")
            return
        
        # 新しいステージ設定を読み込み
        self.load_current_stage_config()
        self.current_stage = self.current_stage_config["stage"]
        
        # ウィンドウタイトルを更新
        self.update_window_title()
        
        # ステージの画像を読み込み
        try:
            foreground_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['foreground']}"
            self.foreground = pygame.image.load(foreground_path)
            self.foreground = pygame.transform.scale(self.foreground, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"前景画像が見つかりません。白い前景を使用します。")
            self.foreground = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.foreground.fill(WHITE)
        
        try:
            background_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['background']}"
            self.background = pygame.image.load(background_path)
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"背景画像が見つかりません。")
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill(BLACK)
        
        # ゲーム状態をリセット（スコアと残りボールは引き継ぎ）
        self.paddle = Paddle()
        self.items = []
        self.blocks_destroyed = 0
        self.current_ball_speed = self.difficulty_settings['initial_ball_speed']
        self.balls = [Ball(self.paddle.x, self.current_ball_speed)]
        self.combo_count = 0
        self.combo_display_timer = 0
        
        # アイテム効果のリセット
        self.paddle_wide_timer = 0
        self.ball_slow_timer = 0
        self.power_ball_timer = 0
        self.paddle_shot_count = 0
        self.bullets = []
        self.paddle.width = self.original_paddle_width
        self.pending_item_effects.clear()
        
        # ゲーム状態管理のリセット
        self.game_state = "playing"
        self.current_bonus_type = "bonus"  # ボーナス画像の種類をリセット
        self.pause_start_time = None
        self.total_pause_time = 0
        
        # 新しいステージ開始時にタイマーをリセット
        self.start_time = pygame.time.get_ticks()
        
        # ブロックを再作成
        self.blocks = []
        self.create_blocks()
        
        print(f"ステージ{self.current_stage}開始！")
    
    def retry_stage(self):
        """現在のステージをリトライ"""
        # スコア・残りボール数・ステージはリセット
        self.score = 0
        self.last_item_score = 0
        self.lives = self.difficulty_settings['balls'] - 1
        
        # その他は次のステージと同じ処理
        self.paddle = Paddle()
        self.items = []
        self.blocks_destroyed = 0
        self.current_ball_speed = self.difficulty_settings['initial_ball_speed']
        self.balls = [Ball(self.paddle.x, self.current_ball_speed)]
        self.combo_count = 0
        self.combo_display_timer = 0
        
        # アイテム効果のリセット
        self.paddle_wide_timer = 0
        self.ball_slow_timer = 0
        self.power_ball_timer = 0
        self.paddle_shot_count = 0
        self.bullets = []
        self.paddle.width = self.original_paddle_width
        self.pending_item_effects.clear()
        
        # ゲーム状態管理のリセット
        self.game_state = "playing"
        self.current_bonus_type = "bonus"  # ボーナス画像の種類をリセット
        self.start_time = pygame.time.get_ticks()
        self.end_time = None
        self.pause_start_time = None
        self.total_pause_time = 0
        
        # ブロックを再作成
        self.blocks = []
        self.create_blocks()
        
        print(f"ステージ{self.current_stage}リトライ！")
    
    def reset_game(self):
        """ゲームを初期状態にリセットする（ステージ1から開始）"""
        # ステージを最初に戻す
        self.current_stage_index = 0
        self.load_current_stage_config()
        self.current_stage = self.current_stage_config["stage"]
        
        # ウィンドウタイトルを更新
        self.update_window_title()
        
        # ステージ1の画像を読み込み
        try:
            foreground_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['foreground']}"
            self.foreground = pygame.image.load(foreground_path)
            self.foreground = pygame.transform.scale(self.foreground, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"前景画像が見つかりません。白い前景を使用します。")
            self.foreground = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.foreground.fill(WHITE)
        
        try:
            background_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['background']}"
            self.background = pygame.image.load(background_path)
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"背景画像が見つかりません。")
            try:
                self.background = pygame.image.load("back.png")
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except (pygame.error, FileNotFoundError):
                self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background.fill(BLACK)
        
        # ゲームオブジェクトの初期化
        self.paddle = Paddle()
        self.items = []
        
        # スコアとゲーム状態のリセット
        self.score = 0
        self.last_item_score = 0
        self.lives = self.difficulty_settings['balls'] - 1
        self.blocks_destroyed = 0
        self.current_ball_speed = self.difficulty_settings['initial_ball_speed']
        self.balls = [Ball(self.paddle.x, self.current_ball_speed)]
        self.combo_count = 0
        self.combo_display_timer = 0
        
        # アイテム効果のリセット
        self.paddle_wide_timer = 0
        self.ball_slow_timer = 0
        self.power_ball_timer = 0
        self.paddle_shot_count = 0
        self.bullets = []
        self.original_paddle_width = PADDLE_WIDTH
        self.paddle.width = self.original_paddle_width
        self.pending_item_effects.clear()  # 待機中のアイテム効果もリセット
        
        # ゲーム状態管理のリセット
        self.game_state = "playing"
        self.stage_clear_timer = 0
        self.start_time = pygame.time.get_ticks()
        self.end_time = None
        self.show_special_reward = False
        self.current_bonus_type = "bonus"  # ボーナス画像の種類をリセット
        self.pause_start_time = None
        self.total_pause_time = 0
        
        # ブロックを再作成
        self.blocks = []
        self.create_blocks()
    
    def calculate_clear_bonus(self):
        """クリア時のボーナススコアを計算"""
        # 残りライフボーナス（1ライフあたり500点、Hardでは5000点）
        life_bonus = 0
        if self.game_state == "game_clear" and self.difficulty_settings['name'] == "Hard":
            life_bonus = self.lives * 5000
        elif self.game_state == "game_clear" and self.difficulty_settings['name'] == "Extreme":
            life_bonus = 0
        elif self.game_state == "game_clear":
            life_bonus = self.lives * 500
        
        # 時間ボーナス（ゲーム時間が短いほど高得点）
        if self.end_time:
            # ポーズ時間を除いた実プレイ時間を計算
            game_time_seconds = (self.end_time - self.start_time - self.total_pause_time) / 1000
        else:
            # end_timeが設定されていない場合のフォールバック
            current_time = pygame.time.get_ticks()
            game_time_seconds = (current_time - self.start_time - self.total_pause_time) / 1000
        # 各ステージの基準時間以内なら時間ボーナス、それ以上は0
        target_time = self.current_stage_config["target_time"]
        if game_time_seconds <= target_time:
            # time_bonus_multiplierを使用してボーナス計算
            time_bonus_multiplier = self.current_stage_config["time_bonus_multiplier"]
            time_bonus = int((target_time - game_time_seconds) * time_bonus_multiplier)
        else:
            time_bonus = 0
        
        total_bonus = life_bonus + time_bonus
        print(f"クリアボーナス: ライフボーナス={life_bonus}, 時間ボーナス={time_bonus} ({game_time_seconds} sec), 合計={total_bonus}")
        return max(total_bonus, 0)
    
    def draw(self):
        # 背景画像を描画
        self.screen.blit(self.background, (0, 0))
        
        # CSVファイルからブロック配置を読み込み
        csv_path = f"{self.current_stage_config['folder']}/{self.current_stage_config['definition']}.csv"
        block_layout = self.load_block_layout_from_csv(csv_path)
        
        # ブロックがある場所に前景画像の該当部分を描画
        for row in range(len(block_layout)):
            for col in range(len(block_layout[row])):
                durability = block_layout[row][col]
                if durability != 0:  # ブロックがある場所
                    x = col * BLOCK_SIZE
                    y = row * BLOCK_SIZE + GAME_AREA_Y
                    rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
                    
                    # 該当するブロックが破壊されているかチェック
                    block_exists = False
                    for block in self.blocks:
                        if block.x == x and block.y == y and not block.destroyed:
                            block_exists = True
                            break
                    
                    # ブロックが存在する場合のみ前景画像を描画
                    if block_exists:
                        # 画像境界を超えないように矩形をクリップ
                        clipped_rect = rect.clip(self.foreground.get_rect())
                        if clipped_rect.width > 0 and clipped_rect.height > 0:
                            fg_section = self.foreground.subsurface(clipped_rect)
                            self.screen.blit(fg_section, (clipped_rect.x, clipped_rect.y))
        
        # セーフエリアの描画
        self.draw_safe_area()
        
        # ゲームクリア時と特別報酬時とポーズ時以外はゲームオブジェクトを描画
        if self.game_state not in ["stage_clear", "game_clear", "special_reward", "paused"]:
            # ゲームオブジェクトの描画
            self.paddle.draw(self.screen)
            for ball in self.balls:
                ball.draw(self.screen)
            
            # ブロックの描画（耐久性表示含む）
            for block in self.blocks:
                block.draw(self.screen)
            
            # アイテムの描画
            for item in self.items:
                item.draw(self.screen)
            
            # 弾丸の描画
            for bullet in self.bullets:
                bullet.draw(self.screen)
        elif self.game_state == "paused":
            # ポーズ中はブロックのみ描画（耐久度表示なし）
            for block in self.blocks:
                block.draw_paused(self.screen)
        
        pygame.display.flip()
    
    def draw_safe_area(self):
        # セーフエリアの背景を描画（半透明の暗いグレー）
        safe_area_surface = pygame.Surface((SCREEN_WIDTH, SAFE_AREA_HEIGHT))
        safe_area_surface.set_alpha(180)  # 半透明
        safe_area_surface.fill((50, 50, 50))
        self.screen.blit(safe_area_surface, (0, 0))
        
        # セーフエリアの境界線を描画
        pygame.draw.line(self.screen, WHITE, (0, SAFE_AREA_HEIGHT), (SCREEN_WIDTH, SAFE_AREA_HEIGHT), 2)
        
        # 特別報酬画面では専用メッセージのみ表示
        if self.game_state == "special_reward":
            # 特別報酬画面のメッセージをセーフエリア内に表示
            congratulations_text = self.font.render("Congratulations!!", True, YELLOW)
            congratulations_rect = congratulations_text.get_rect()
            self.screen.blit(congratulations_text, ((SCREEN_WIDTH - congratulations_rect.width) // 2, 15))
            
            # クリック待機メッセージ（次のボーナス画像があるかどうかで分岐）
            if self.can_show_next_bonus():
                click_text = self.small_font.render("Click to Next Bonus", True, WHITE)
            elif self.current_stage_index + 1 < len(self.stage_data):
                click_text = self.small_font.render("Click to Next Stage", True, WHITE)
            else:
                click_text = self.small_font.render("Click to Character Select", True, WHITE)
            click_rect = click_text.get_rect()
            self.screen.blit(click_text, ((SCREEN_WIDTH - click_rect.width) // 2, 40))
            return
        
        # ポーズ画面では専用メッセージのみ表示
        if self.game_state == "paused":
            # ポーズメッセージをセーフエリア内に表示
            pause_text = self.font.render("PAUSED", True, YELLOW)
            pause_rect = pause_text.get_rect()
            self.screen.blit(pause_text, ((SCREEN_WIDTH - pause_rect.width) // 2, 10))
            
            # 操作説明
            resume_text = self.small_font.render("Press any key or click to resume", True, WHITE)
            resume_rect = resume_text.get_rect()
            self.screen.blit(resume_text, ((SCREEN_WIDTH - resume_rect.width) // 2, 30))
            
            exit_text = self.small_font.render("Press ESC to exit to stage select", True, WHITE)
            exit_rect = exit_text.get_rect()
            self.screen.blit(exit_text, ((SCREEN_WIDTH - exit_rect.width) // 2, 50))
            return
        
        # スコアとライフの表示（セーフエリア内）
        score_text = self.font.render(f"SCORE: {self.score}", True, WHITE)
        lives_text = self.font.render(f"BALL: {self.lives}", True, WHITE)
        stage_text = self.small_font.render(f"{self.difficulty_settings['name']} STAGE: {self.current_stage}", True, WHITE)
        
        # スコアを左側に表示
        self.screen.blit(score_text, (15, 15))
        
        # 残りボール数を右側に表示
        lives_rect = lives_text.get_rect()
        self.screen.blit(lives_text, (SCREEN_WIDTH - lives_rect.width - 15, 15))
        
        # ステージ情報を左下に表示
        self.screen.blit(stage_text, (15, 40))
        
        # プレイ時間を右下に表示（ゲーム中のみ）
        if self.game_state == "playing":
            current_time = pygame.time.get_ticks()
            # ポーズ時間を除いた実プレイ時間を計算
            play_time_seconds = (current_time - self.start_time - self.total_pause_time) // 1000
            minutes = play_time_seconds // 60
            seconds = play_time_seconds % 60
            time_text = self.small_font.render(f"TIME: {minutes:02d}:{seconds:02d}", True, WHITE)
            time_rect = time_text.get_rect()
            self.screen.blit(time_text, (SCREEN_WIDTH - time_rect.width - 15, 40))
        
        # アイテム効果の残り時間を中央に表示（ゲーム中のみ）
        if self.game_state == "playing":
            # ボールがパドルに固定されている場合は指示テキストを表示
            if any(ball.stuck_to_paddle for ball in self.balls):
                instruction_text = self.font.render("CLICK TO SHOOT BALL !!", True, YELLOW)
                instruction_rect = instruction_text.get_rect()
                self.screen.blit(instruction_text, ((SCREEN_WIDTH - instruction_rect.width) // 2, 15))
            else:
                item_effects = []
                if self.paddle_wide_timer > 0:
                    item_effects.append(f"WIDE: {self.paddle_wide_timer//60}s")
                if self.ball_slow_timer > 0:
                    item_effects.append(f"SLOW: {self.ball_slow_timer//60}s")
                if self.power_ball_timer > 0:
                    item_effects.append(f"POWER: {self.power_ball_timer//60}s")
                if self.paddle_shot_count > 0:
                    item_effects.append(f"SHOT: {self.paddle_shot_count}")
                
                if item_effects:
                    effect_text = " | ".join(item_effects)
                    effect_surface = self.small_font.render(effect_text, True, CYAN)
                else:
                    effect_surface = self.small_font.render("NO ITEM", True, WHITE)
                
                effect_rect = effect_surface.get_rect()
                self.screen.blit(effect_surface, ((SCREEN_WIDTH - effect_rect.width) // 2, 15))

        # コンボカウントとアイテム効果はゲーム中のみ表示
        if self.game_state == "playing":
            # 緊急ステージクリアが可能な場合は優先して表示
            if self.can_emergency_clear():
                emergency_text = self.small_font.render("Press 'O' to Stage Clear!", True, YELLOW)
                emergency_rect = emergency_text.get_rect()
                self.screen.blit(emergency_text, ((SCREEN_WIDTH - emergency_rect.width) // 2, 40))
            # コンボカウントを表示（コンボが2以上でタイマーが有効な場合のみ）
            elif self.combo_count >= 2 and self.combo_display_timer > 0:
                combo_text = self.small_font.render(f"COMBO x{self.combo_count}", True, YELLOW)
                combo_rect = combo_text.get_rect()
                self.screen.blit(combo_text, ((SCREEN_WIDTH - combo_rect.width) // 2, 40))
            else:
                # コンボが表示されていないときは現在のボールスピードをゲージで表示
                speed_percentage = self.get_speed_percentage()
                speed_text = self.small_font.render(f"BALL SPEED: ", True, CYAN)
                speed_rect = speed_text.get_rect()
                speed_x = (SCREEN_WIDTH - speed_rect.width) // 2
                self.screen.blit(speed_text, (speed_x, 40))
                
                # スピードゲージを描画（テキストの右側に表示）
                gauge_x = speed_x + speed_rect.width + 5
                gauge_y = 40 + (speed_rect.height - 12) // 2  # テキストの高さに合わせて中央揃え
                gauge_width = 60
                gauge_height = 12
                
                # ゲージの背景（グレー）
                pygame.draw.rect(self.screen, (100, 100, 100), (gauge_x, gauge_y, gauge_width, gauge_height))
                
                # ゲージの中身（スピードとslow_ball状態に応じて色が変化）
                if speed_percentage > 0:
                    fill_width = int((gauge_width - 2) * (speed_percentage / 100))
                    
                    # slow_ball適用中は緑色、100%時は赤色、通常時は黄色
                    if self.ball_slow_timer > 0:
                        gauge_color = (0, 255, 0)  # slow_ball適用中：緑
                    elif speed_percentage >= 100:
                        gauge_color = (255, 0, 0)  # 100%：赤
                    else:
                        gauge_color = (255, 255, 0)  # 通常時：黄
                    
                    pygame.draw.rect(self.screen, gauge_color, (gauge_x + 1, gauge_y + 1, fill_width, gauge_height - 2))
                
                # ゲージの枠線（白）
                pygame.draw.rect(self.screen, WHITE, (gauge_x, gauge_y, gauge_width, gauge_height), 1)
        
        # ゲーム終了時のメッセージ表示
        elif self.game_state == "game_over":
            # ゲームオーバーメッセージ
            game_over_text = self.font.render("GAME OVER", True, RED)
            game_over_rect = game_over_text.get_rect()
            self.screen.blit(game_over_text, ((SCREEN_WIDTH - game_over_rect.width) // 2, 15))
            
            # リトライメッセージ
            if self.difficulty_settings["name"] == "Extreme":
                retry_text = self.small_font.render("Click to Retry", True, WHITE)
            else:
                retry_text = self.small_font.render("Click to Retry Stage", True, WHITE)
            retry_rect = retry_text.get_rect()
            self.screen.blit(retry_text, ((SCREEN_WIDTH - retry_rect.width) // 2, 40))
        
        elif self.game_state == "stage_clear":
            # ステージクリアメッセージ
            stage_clear_text = self.font.render(f"STAGE {self.current_stage} CLEAR!", True, YELLOW)
            stage_clear_rect = stage_clear_text.get_rect()
            self.screen.blit(stage_clear_text, ((SCREEN_WIDTH - stage_clear_rect.width) // 2, 6))
            
            # ボーナススコア詳細を表示
            if hasattr(self, 'last_bonus_score'):
                bonus_info = f"Bonus: {self.last_bonus_score}"
                bonus_text = self.small_font.render(bonus_info, True, CYAN)
                bonus_rect = bonus_text.get_rect()
                self.screen.blit(bonus_text, ((SCREEN_WIDTH - bonus_rect.width) // 2, 28))
            
            # 次のステージメッセージ
            next_text = self.small_font.render("Going to next stage...", True, WHITE)
            next_rect = next_text.get_rect()
            self.screen.blit(next_text, ((SCREEN_WIDTH - next_rect.width) // 2, 43))
        
        elif self.game_state == "game_clear":
            # ゲームクリアメッセージ
            you_win_text = self.font.render("YOU WIN", True, YELLOW)
            you_win_rect = you_win_text.get_rect()
            self.screen.blit(you_win_text, ((SCREEN_WIDTH - you_win_rect.width) // 2, 6))
            
            # ボーナススコア詳細を表示
            if hasattr(self, 'last_bonus_score'):
                bonus_info = f"Bonus: {self.last_bonus_score}"
                bonus_text = self.small_font.render(bonus_info, True, CYAN)
                bonus_rect = bonus_text.get_rect()
                self.screen.blit(bonus_text, ((SCREEN_WIDTH - bonus_rect.width) // 2, 28))
                
                # クリック待機メッセージ（目標スコア以上でボーナス画像があれば特別メッセージ）
                if self.score >= self.current_stage_config["target_score"] and self.current_stage_config["bonus"]:
                    click_text = self.small_font.render("Click to NEXT", True, WHITE)
                else:
                    click_text = self.small_font.render("Click to Character Select", True, WHITE)
                click_rect = click_text.get_rect()
                self.screen.blit(click_text, ((SCREEN_WIDTH - click_rect.width) // 2, 43))
            else:
                # クリック待機メッセージ
                click_text = self.small_font.render("Click to Character Select", True, WHITE)
                click_rect = click_text.get_rect()
                self.screen.blit(click_text, ((SCREEN_WIDTH - click_rect.width) // 2, 40))
    
    def run(self):
        while True:
            event_result = self.handle_events()
            if event_result == False:
                break
            elif event_result == "back_to_select":
                # キャラクター選択画面に戻る
                return "back_to_select"
            
            self.update()
            self.draw()
            self.clock.tick(60)
        
        # ゲーム終了時の最終メッセージ
        if self.game_state == "game_over":
            print(f"最終スコア: {self.score}")
        elif self.game_state == "game_clear":
            print(f"おめでとうございます！最終スコア: {self.score}")
        elif self.game_state == "special_reward":
            print(f"特別報酬獲得！最終スコア: {self.score}")
        
        return "exit"
    
    def load_stage_data(self):
        """選択されたキャラクターのステージデータを読み込む（SaveManagerに移行済み）"""
        return self.save_manager.load_stage_data(self.selected_chara["folder"])
    
    def load_current_stage_config(self):
        """現在のステージ設定を読み込む"""
        stage_data = self.stage_data[self.current_stage_index]
        
        # ステージ設定を格納
        self.current_stage_config = {
            "chara_name": self.selected_chara["name"],
            "folder": self.selected_chara["folder"],
            "stage": stage_data["stage"],
            "definition": stage_data["definition"],
            "foreground": stage_data["foreground"],
            "background": stage_data["background"],
            "bonus": stage_data["bonus"],
            "target_score": stage_data["target_score"],
            "target_time": stage_data["target_time"],
            "time_bonus_multiplier": stage_data.get("time_bonus_multiplier", 20),
            "bonus2": stage_data.get("bonus2", ""),
            "target_score2": stage_data.get("target_score2", 0)
        }
    
    def load_block_layout_from_csv(self, csv_path):
        """CSVファイルからブロック配置を読み込む"""
        block_layout = []
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_reader = csv.reader(f)
                for row in csv_reader:
                    # 各要素を整数に変換（空白を除去）
                    layout_row = [int(cell.strip()) for cell in row if cell.strip()]
                    if layout_row:  # 空行でない場合のみ追加
                        block_layout.append(layout_row)
        except (FileNotFoundError, ValueError, csv.Error) as e:
            print(f"CSVファイルの読み込みに失敗しました: {e}")
            # デフォルトのブロック配置を返す（空の配置）
            block_layout = [[0 for _ in range(21)] for _ in range(23)]
        
        return block_layout
    
    def load_save_data(self):
        """セーブデータを読み込む（SaveManagerに移行済み）"""
        # 互換性のため残しておくが、実際はSaveManagerを使用
        return self.save_manager.save_data
    
    def save_game_data(self):
        """ゲームデータをセーブファイルに書き込む（SaveManagerに移行済み）"""
        # SaveManagerのsave_game_dataメソッドを呼び出し
        self.save_manager.save_game_data()
    
    def get_current_chara_save_key(self):
        """現在のキャラクターのセーブデータキーを取得（SaveManagerに移行済み）"""
        return self.save_manager.get_chara_save_key(self.selected_chara["folder"])
    
    def update_save_data(self):
        """現在のプレイ結果でセーブデータを更新"""
        chara_folder = self.selected_chara["folder"]
        save_data = self.save_manager.get_chara_data(chara_folder)
        
        # ハイスコア更新（最終ステージクリア時またはゲームオーバー時のみ）
        is_final_clear = self.game_state == "game_clear" or (self.game_state == "special_reward" and self.current_stage_index + 1 >= len(self.stage_data))
        is_game_over = self.game_state == "game_over"
        
        update_data = {}
        
        if (is_final_clear or is_game_over) and self.score > save_data["hi_score"]:
            update_data["hi_score"] = self.score
            print(f"ハイスコア更新！: {self.score}")
        
        # 全ステージクリア判定
        if is_final_clear:
            update_data["clear"] = 1
            print("全ステージクリア記録を更新しました")
        
        # データが更新される場合のみSaveManagerを呼び出し
        if update_data:
            if "hi_score" in update_data:
                self.save_manager.update_chara_data(chara_folder, hi_score=update_data["hi_score"])
            if "clear" in update_data:
                self.save_manager.update_chara_data(chara_folder, clear=update_data["clear"])
        
        # ボーナス画像フラグ更新（目標スコア以上でボーナス画像があり、難易度設定でボーナス画像が有効なステージ）
        if (self.game_state in ["stage_clear", "game_clear", "special_reward"] and 
            self.score >= self.current_stage_config["target_score"] and 
            self.current_stage_config["bonus"] and
            self.difficulty_settings['get_bonus_image']):
            
            # 既にボーナス画像2フラグ（2）が設定されている場合は維持、そうでなければボーナス画像1フラグ（1）を設定
            bonus_index = self.current_stage - 1
            if 0 <= bonus_index < len(save_data["bonus_flags"]) and save_data["bonus_flags"][bonus_index] != 2:
                self.save_manager.update_bonus_flag(chara_folder, self.current_stage, 1)
    
    def update_save_data_for_bonus2(self):
        """ボーナス画像2表示時のセーブデータ更新"""
        chara_folder = self.selected_chara["folder"]
        
        # ボーナス画像2フラグ更新（目標スコア2以上でボーナス画像2があり、難易度設定でボーナス画像が有効なステージ）
        if (self.score >= self.current_stage_config.get("target_score2", 0) and 
            self.current_stage_config.get("bonus2", "") and
            self.difficulty_settings['get_bonus_image']):
            
            self.save_manager.update_bonus_flag(chara_folder, self.current_stage, 2)
