import pygame
import sys
import json
import csv
import os
from constants.block_colors import BLOCK_COLORS
from constants.constants import WHITE

# 初期化
pygame.init()

# 定数
SCREEN_WIDTH = 672
SCREEN_HEIGHT = 864
BLOCK_SIZE = 32

# セーフエリアの定義
SAFE_AREA_TOP = 2    # 上部セーフエリア（2列分）
SAFE_AREA_BOTTOM = 3 # 下部セーフエリア（3列分）
GAME_AREA_START_Y = SAFE_AREA_TOP * BLOCK_SIZE  # ゲームエリア開始Y座標（64px）
GAME_AREA_END_Y = SCREEN_HEIGHT - (SAFE_AREA_BOTTOM * BLOCK_SIZE)  # ゲームエリア終了Y座標

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

class LayoutViewer:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ブロック配置ビューアー")
        self.clock = pygame.time.Clock()
        
        # charas.jsonからキャラクターデータを読み込み
        self.charas_data = self.load_charas_data()
        
        # バンク機能の初期化
        self.chars_per_bank = 6  # 1バンクあたりのキャラクター数
        self.current_bank = 0
        self.total_banks = max(1, (len(self.charas_data) + self.chars_per_bank - 1) // self.chars_per_bank)
        
        self.current_chara_index = 0
        self.current_stage_index = 0
        
        # 現在選択中のキャラクターとステージデータを読み込み
        self.current_chara = self.charas_data[self.current_chara_index] if self.charas_data else None
        self.stages_data = self.load_stages_data() if self.current_chara else []
        
        # 現在のステージ情報
        self.current_stage_config = self.stages_data[self.current_stage_index] if self.stages_data else None
        
        # フォントの読み込み
        try:
            self.font = pygame.font.Font("PixelMplus12-Regular.ttf", 16)
        except (pygame.error, FileNotFoundError):
            print("PixelMplus12-Regular.ttfが見つかりません。デフォルトフォントを使用します。")
            self.font = pygame.font.Font(None, 18)
        
        # 画像とレイアウトの読み込み
        self.foreground_image = None
        self.background_image = None
        self.current_layout = None
        
        if self.current_stage_config:
            self.load_current_stage_resources()
        else:
            # デフォルトの空レイアウト
            self.current_layout = [[0 for _ in range(21)] for _ in range(23)]
            self.foreground_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.foreground_image.fill(WHITE)
            self.background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background_image.fill(BLACK)
        
        # ドラッグ機能のための変数
        self.dragging = False
        self.drag_color_direction = 0  # 1: 色を進める, -1: 色を戻す
        self.last_changed_block = None  # 最後に変更したブロックの位置
        
        # 半透明表示の設定
        self.transparent_mode = False
        
        # ファイル保存状態の表示用
        self.save_message = ""
        self.save_message_timer = 0
        
        # 情報画面の表示制御
        self.show_info = True

    def switch_chara(self, chara_index):
        """キャラクターを切り替える"""
        if 0 <= chara_index < len(self.charas_data):
            self.current_chara_index = chara_index
            self.current_chara = self.charas_data[self.current_chara_index]
            self.current_stage_index = 0  # ステージを1番目にリセット
            
            # 新しいキャラクターのステージデータを読み込み
            self.stages_data = self.load_stages_data()
            if self.stages_data:
                self.current_stage_config = self.stages_data[self.current_stage_index]
                self.load_current_stage_resources()
            else:
                # ステージデータがない場合のデフォルト
                self.current_stage_config = None
                self.current_layout = [[0 for _ in range(21)] for _ in range(23)]
                self.foreground_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.foreground_image.fill(WHITE)
                self.background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background_image.fill(BLACK)
            
            chara_name = self.current_chara["name"]
            print(f"キャラクター '{chara_name}' に切り替えました")
            self.save_message = f"キャラクター: {chara_name}"
            self.save_message_timer = 120
        else:
            print(f"無効なキャラクターインデックス: {chara_index}")

    def switch_chara_with_bank_update(self, chara_index):
        """キャラクターを切り替えてバンクも自動更新"""
        if 0 <= chara_index < len(self.charas_data):
            self.current_chara_index = chara_index
            
            # バンクも自動更新
            self.current_bank = chara_index // self.chars_per_bank
            
            self.current_chara = self.charas_data[self.current_chara_index]
            self.current_stage_index = 0  # ステージを1番目にリセット
            
            # 新しいキャラクターのステージデータを読み込み
            self.stages_data = self.load_stages_data()
            if self.stages_data:
                self.current_stage_config = self.stages_data[self.current_stage_index]
                self.load_current_stage_resources()
            else:
                # ステージデータがない場合のデフォルト
                self.current_stage_config = None
                self.current_layout = [[0 for _ in range(21)] for _ in range(23)]
                self.foreground_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.foreground_image.fill(WHITE)
                self.background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background_image.fill(BLACK)
            
            chara_name = self.current_chara["name"]
            print(f"キャラクター '{chara_name}' に切り替えました (バンク {self.current_bank + 1})")
            self.save_message = f"キャラクター: {chara_name} (バンク {self.current_bank + 1})"
            self.save_message_timer = 120
        else:
            print(f"無効なキャラクターインデックス: {chara_index}")

    def switch_stage(self, stage_index):
        """ステージを切り替える"""
        if 0 <= stage_index < len(self.stages_data):
            self.current_stage_index = stage_index
            self.current_stage_config = self.stages_data[self.current_stage_index]
            self.load_current_stage_resources()
            stage_num = self.current_stage_config["stage"]
            print(f"ステージ{stage_num}に切り替えました")
            self.save_message = f"ステージ{stage_num}に切り替え"
            self.save_message_timer = 120
        else:
            print(f"無効なステージインデックス: {stage_index}")

    def get_current_layout(self):
        """現在のステージのレイアウトを取得"""
        return self.current_layout

    def get_current_foreground(self):
        """現在のステージの前景画像を取得"""
        return self.foreground_image

    def get_current_background(self):
        """現在のステージの背景画像を取得"""
        return self.background_image

    def get_current_stage_data(self):
        """現在のステージのデータを取得"""
        return self.current_stage_config
    
    def draw_grid(self):
        """グリッド線を描画"""
        # 縦線
        for x in range(0, SCREEN_WIDTH + 1, BLOCK_SIZE):
            pygame.draw.line(self.screen, LIGHT_GRAY, (x, 0), (x, SCREEN_HEIGHT), 1)
        
        # 横線
        for y in range(0, SCREEN_HEIGHT + 1, BLOCK_SIZE):
            pygame.draw.line(self.screen, LIGHT_GRAY, (0, y), (SCREEN_WIDTH, y), 1)
    
    def draw_blocks(self):
        """ブロック配置を描画"""
        current_layout = self.get_current_layout()
        current_foreground = self.get_current_foreground()
        current_background = self.get_current_background()
        
        # 全画面に背景画像を描画
        for row in range(SCREEN_HEIGHT // BLOCK_SIZE):
            for col in range(SCREEN_WIDTH // BLOCK_SIZE):
                x = col * BLOCK_SIZE
                y = row * BLOCK_SIZE
                rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
                
                # セーフエリア（上部2列、下部3列）の場合は背景画像のみ表示
                if row < SAFE_AREA_TOP or row >= (SCREEN_HEIGHT // BLOCK_SIZE) - SAFE_AREA_BOTTOM:
                    # セーフエリア：背景画像を表示
                    clipped_rect = rect.clip(current_background.get_rect())
                    if clipped_rect.width > 0 and clipped_rect.height > 0:
                        bg_section = current_background.subsurface(clipped_rect)
                        self.screen.blit(bg_section, (clipped_rect.x, clipped_rect.y))
                    
                    # セーフエリアを示すグリッド線（より薄く）
                    pygame.draw.rect(self.screen, (150, 150, 150), rect, 1)
                else:
                    # ゲームエリア：ブロック配置に従って表示
                    layout_row = row - SAFE_AREA_TOP  # ブロック配列のインデックスに変換
                    if 0 <= layout_row < len(current_layout) and col < len(current_layout[layout_row]):
                        color_id = current_layout[layout_row][col]
                        
                        if color_id == 0:
                            # ブロックがない場合：背景画像の該当部分を表示
                            clipped_rect = rect.clip(current_background.get_rect())
                            if clipped_rect.width > 0 and clipped_rect.height > 0:
                                bg_section = current_background.subsurface(clipped_rect)
                                self.screen.blit(bg_section, (clipped_rect.x, clipped_rect.y))
                            
                            # グリッド線を表示（編集モードでの視認性向上）
                            pygame.draw.rect(self.screen, LIGHT_GRAY, rect, 1)
                            
                            # 中央に"0"を表示（編集時の参考用）
                            text = self.font.render("0", True, LIGHT_GRAY)
                            text_rect = text.get_rect(center=rect.center)
                            self.screen.blit(text, text_rect)
                        else:
                            # ブロックがある場合
                            if not self.transparent_mode:
                                # 通常モード：前景画像の該当部分を表示
                                clipped_rect = rect.clip(current_foreground.get_rect())
                                if clipped_rect.width > 0 and clipped_rect.height > 0:
                                    fg_section = current_foreground.subsurface(clipped_rect)
                                    self.screen.blit(fg_section, (clipped_rect.x, clipped_rect.y))
                                
                                # ブロック境界を表示
                                pygame.draw.rect(self.screen, BLACK, rect, 2)
                            else:
                                # 半透明モード：背景画像を表示してから半透明のブロック色を重ねる
                                clipped_rect = rect.clip(current_background.get_rect())
                                if clipped_rect.width > 0 and clipped_rect.height > 0:
                                    bg_section = current_background.subsurface(clipped_rect)
                                    self.screen.blit(bg_section, (clipped_rect.x, clipped_rect.y))
                                
                                # 半透明のブロック色を重ねる
                                transparent_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
                                transparent_surface.set_alpha(128)
                                transparent_surface.fill(BLOCK_COLORS.get(color_id, WHITE))
                                self.screen.blit(transparent_surface, (x, y))
                                pygame.draw.rect(self.screen, BLACK, rect, 2)
                            
                            # 中央に色番号を表示（編集時の参考用）
                            text_color = WHITE if self.transparent_mode else BLACK
                            text = self.font.render(str(color_id), True, text_color)
                            text_rect = text.get_rect(center=rect.center)
                            self.screen.blit(text, text_rect)
                    else:
                        # 配列の範囲外：背景画像を表示
                        clipped_rect = rect.clip(current_background.get_rect())
                        if clipped_rect.width > 0 and clipped_rect.height > 0:
                            bg_section = current_background.subsurface(clipped_rect)
                            self.screen.blit(bg_section, (clipped_rect.x, clipped_rect.y))
    
    def save_layout_to_csv(self, filename=None):
        """現在のブロック配置をCSVファイルに保存"""
        if not self.current_stage_config or not self.current_chara:
            self.save_message = "保存エラー: ステージデータがありません"
            self.save_message_timer = 180
            return False
        
        if filename is None:
            # デフォルトのファイル名（タイムスタンプ付き）
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            definition_name = self.current_stage_config["definition"]
            filename = f"{definition_name}_{timestamp}.csv"
        
        try:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                csv_writer = csv.writer(f)
                for row in self.current_layout:
                    # 各行の末尾にカンマを追加
                    row_with_comma = [str(cell) for cell in row] + ['']
                    csv_writer.writerow(row_with_comma)
            
            stage_num = self.current_stage_config["stage"]
            print(f"ステージ{stage_num}のブロック配置を '{filename}' に保存しました。")
            self.save_message = f"ステージ{stage_num}保存完了: {filename}"
            self.save_message_timer = 180  # 3秒間表示（60fps * 3秒）
            return True
        except Exception as e:
            print(f"CSV保存エラー: {e}")
            self.save_message = f"CSV保存エラー: {str(e)}"
            self.save_message_timer = 180
            return False

    def clear_all_blocks(self):
        """現在のステージの全ブロックを0（透明）にする"""
        if self.current_layout:
            for row in range(len(self.current_layout)):
                for col in range(len(self.current_layout[row])):
                    self.current_layout[row][col] = 0
    
    def count_blocks(self):
        """現在のレイアウトのブロック数を計算"""
        if not self.current_layout:
            return 0, {}
        
        total_blocks = 0
        durability_counts = {}
        
        for row in self.current_layout:
            for cell in row:
                if cell > 0:  # 耐久度1以上のブロック
                    total_blocks += 1
                    durability_counts[cell] = durability_counts.get(cell, 0) + 1
        
        return total_blocks, durability_counts
    
    def draw_info(self):
        """画面情報を描画"""
        if not self.show_info:
            # 情報画面が非表示の場合は保存メッセージのみ表示
            if self.save_message_timer > 0:
                # メッセージ背景
                msg_bg = pygame.Surface((400, 40))
                msg_bg.set_alpha(200)
                msg_bg.fill((0, 100, 0) if "保存完了" in self.save_message else (100, 0, 0))
                self.screen.blit(msg_bg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 60))
                
                # メッセージテキスト
                msg_text = self.font.render(self.save_message, True, WHITE)
                msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
                self.screen.blit(msg_text, msg_rect)
                
                self.save_message_timer -= 1
            return
        
        if not self.current_stage_config or not self.current_chara:
            return
        
        current_stage_data = self.get_current_stage_data()
        current_layout = self.get_current_layout()
        
        stage_num = current_stage_data["stage"]
        chara_name = self.current_chara["name"]

        info_display_y = 720
        
        # ブロック数の情報を取得
        total_blocks, durability_counts = self.count_blocks()
        # ブロックの総耐久度を取得
        total_blocks_durability = 0

        
        info_texts = [
            f"キャラクター: {chara_name} ({self.current_chara_index + 1}/{len(self.charas_data)})",
            # f"現在のステージ: {stage_num}",
            f"ステージ: {self.current_stage_index + 1}/{len(self.stages_data)}",
            "",
            f"総ブロック数: {total_blocks}個",
            "耐久度別ブロック数:",
        ]
        
        # 耐久度別のブロック数を追加（耐久度1～7まで表示）
        for durability in range(1, 8):  # 1～7の耐久度
            count = durability_counts.get(durability, 0)
            total_blocks_durability += count * durability
            info_texts.append(f"  耐久度{durability}: {count}個")

        # 総耐久度により、難易度目安を判定（ゲーム中では使用されない）
        if total_blocks_durability <= 150:
            difficulty_text = "Easy"
        elif total_blocks_durability <= 300:
            difficulty_text = "Normal"
        elif total_blocks_durability <= 450:
            difficulty_text = "Hard"
        else:
            difficulty_text = "Extreme"
        
        info_texts.extend([
            f"総耐久度: {total_blocks_durability} pts ({difficulty_text})",
            "",
            f"利用可能キャラクター (バンク {self.current_bank + 1}/{self.total_banks}):",
        ])
        
        # 現在のバンク内のキャラクター一覧を追加
        bank_chars = self.get_current_bank_chars()
        for i, chara in enumerate(bank_chars):
            chara_index = self.current_bank * self.chars_per_bank + i
            prefix = "→ " if chara_index == self.current_chara_index else "  "
            info_texts.append(f"{prefix}{i+1}. {chara['name']}")
            info_display_y += 20
        
        if current_stage_data["bonus"]:
            # ボーナス画像の情報を追加
            bonus_info = f"ボーナス画像: {current_stage_data['bonus']} (目標スコア: {current_stage_data['target_score']}点)"
        else:
            bonus_info = "ボーナス画像: なし"
        
        info_texts.extend([
            "",
            # f"画面サイズ: {SCREEN_WIDTH} x {SCREEN_HEIGHT}",
            # f"ブロックサイズ: {BLOCK_SIZE} x {BLOCK_SIZE}",
            # f"グリッド: {len(current_layout[0])} x {len(current_layout)}",
            # f"ゲームエリア: Y={GAME_AREA_START_Y}-{GAME_AREA_END_Y}",
            f"前景画像: {current_stage_data['foreground']}",
            f"背景画像: {current_stage_data['background']}",
            bonus_info,
            f"制限時間: {current_stage_data['target_time']}秒",
            f"タイムボーナス: {current_stage_data['time_bonus_multiplier']}点/秒",
            # "",
            # "表示方法:",
            # "ブロックあり: 前景画像を表示",
            # "ブロックなし: 背景画像を表示",
            # "セーフエリア: 背景画像固定",
            "",
            "操作方法:",
            "左クリック/ドラッグ: ブロックを配置 or 耐久性を1増加",
            "右クリック/ドラッグ: 耐久性を1戻す or ブロックを消去",
            "←/→キー: ステージ切り替え",
            "1-6キー: バンク内キャラクター切り替え",
            "PageUp/PageDownキー: バンク切り替え",
            "Nキー: 全ブロック消去",
            "Sキー: CSV形式で保存",
            "Tキー: 半透明表示ON/OFF",
            "Iキー: 情報画面表示ON/OFF",
            f"半透明モード: {'ON' if self.transparent_mode else 'OFF'}",
            f"情報表示: {'ON' if self.show_info else 'OFF'}",
            "ESCキー: 終了"
        ])
        
        # 半透明の背景
        info_bg = pygame.Surface((450, info_display_y))
        info_bg.set_alpha(180)
        info_bg.fill(BLACK)
        self.screen.blit(info_bg, (10, 10))
        
        # テキスト描画
        for i, text in enumerate(info_texts):
            if text:  # 空文字列でない場合のみ描画
                rendered_text = self.font.render(text, True, WHITE)
                self.screen.blit(rendered_text, (20, 20 + i * 20))
        
        # 保存メッセージの表示
        if self.save_message_timer > 0:
            # メッセージ背景
            msg_bg = pygame.Surface((400, 40))
            msg_bg.set_alpha(200)
            msg_bg.fill((0, 100, 0) if "保存完了" in self.save_message else (100, 0, 0))
            self.screen.blit(msg_bg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 60))
            
            # メッセージテキスト
            msg_text = self.font.render(self.save_message, True, WHITE)
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
            self.screen.blit(msg_text, msg_rect)
            
            self.save_message_timer -= 1
    
    def get_block_position(self, mouse_pos):
        """マウス位置からブロックの行・列を取得（ゲームエリアのみ）"""
        if not self.current_layout:
            return None, None
        
        x, y = mouse_pos
        col = x // BLOCK_SIZE
        row = y // BLOCK_SIZE
        
        # セーフエリアの場合は無効
        if row < SAFE_AREA_TOP or row >= (SCREEN_HEIGHT // BLOCK_SIZE) - SAFE_AREA_BOTTOM:
            return None, None
        
        # ゲームエリア内での位置に変換
        layout_row = row - SAFE_AREA_TOP
        
        # 範囲チェック
        if 0 <= layout_row < len(self.current_layout) and 0 <= col < len(self.current_layout[0]):
            return layout_row, col
        return None, None
    
    def change_block_color(self, row, col, direction):
        """ブロックの色を変更"""
        if row is None or col is None:
            return
        
        current_layout = self.get_current_layout()
        current_color = current_layout[row][col]
        max_color = max(BLOCK_COLORS.keys())
        
        if direction == 1:  # 左クリック: 色を1進める
            new_color = current_color + 1
            if new_color > max_color:
                new_color = 0
        else:  # 右クリック: 色を1戻す
            new_color = current_color - 1
            if new_color < 0:
                new_color = max_color
                
        current_layout[row][col] = new_color
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_n:
                    # Nキー: 全ブロック消去
                    self.clear_all_blocks()
                elif event.key == pygame.K_LEFT:
                    # 左矢印キー: 前のステージに切り替え
                    if self.current_stage_index > 0:
                        self.switch_stage(self.current_stage_index - 1)
                elif event.key == pygame.K_RIGHT:
                    # 右矢印キー: 次のステージに切り替え
                    if self.current_stage_index < len(self.stages_data) - 1:
                        self.switch_stage(self.current_stage_index + 1)
                elif event.key == pygame.K_1:
                    # 1キー: バンク内キャラクター1に切り替え
                    bank_start = self.current_bank * self.chars_per_bank
                    if bank_start < len(self.charas_data):
                        self.switch_chara(bank_start)
                elif event.key == pygame.K_2:
                    # 2キー: バンク内キャラクター2に切り替え
                    bank_start = self.current_bank * self.chars_per_bank
                    if bank_start + 1 < len(self.charas_data):
                        self.switch_chara(bank_start + 1)
                elif event.key == pygame.K_3:
                    # 3キー: バンク内キャラクター3に切り替え
                    bank_start = self.current_bank * self.chars_per_bank
                    if bank_start + 2 < len(self.charas_data):
                        self.switch_chara(bank_start + 2)
                elif event.key == pygame.K_4:
                    # 4キー: バンク内キャラクター4に切り替え
                    bank_start = self.current_bank * self.chars_per_bank
                    if bank_start + 3 < len(self.charas_data):
                        self.switch_chara(bank_start + 3)
                elif event.key == pygame.K_5:
                    # 5キー: バンク内キャラクター5に切り替え
                    bank_start = self.current_bank * self.chars_per_bank
                    if bank_start + 4 < len(self.charas_data):
                        self.switch_chara(bank_start + 4)
                elif event.key == pygame.K_6:
                    # 6キー: バンク内キャラクター6に切り替え
                    bank_start = self.current_bank * self.chars_per_bank
                    if bank_start + 5 < len(self.charas_data):
                        self.switch_chara(bank_start + 5)
                elif event.key == pygame.K_s:
                    # Sキー: ブロック配置をファイル保存
                    keys = pygame.key.get_pressed()
                    # S: CSV形式で保存
                    self.save_layout_to_csv()
                elif event.key == pygame.K_t:
                    # Tキー: 半透明表示ON/OFF
                    self.transparent_mode = not self.transparent_mode
                elif event.key == pygame.K_i:
                    # Iキー: 情報画面表示ON/OFF
                    self.show_info = not self.show_info
                elif event.key == pygame.K_PAGEUP:
                    # PageUp: バンクを前に切り替え
                    self.switch_bank(-1)
                elif event.key == pygame.K_PAGEDOWN:
                    # PageDown: バンクを次に切り替え
                    self.switch_bank(1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                row, col = self.get_block_position(event.pos)
                if event.button == 1:  # 左クリック
                    self.dragging = True
                    self.drag_color_direction = 1
                    self.last_changed_block = (row, col)
                    self.change_block_color(row, col, 1)
                elif event.button == 3:  # 右クリック
                    self.dragging = True
                    self.drag_color_direction = -1
                    self.last_changed_block = (row, col)
                    self.change_block_color(row, col, -1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in [1, 3]:  # 左クリック or 右クリック
                    self.dragging = False
                    self.drag_color_direction = 0
                    self.last_changed_block = None
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    # ドラッグ中はマウス位置のブロックの色を変更（同じブロックは1回だけ）
                    row, col = self.get_block_position(event.pos)
                    current_block = (row, col)
                    if current_block != self.last_changed_block and row is not None and col is not None:
                        self.change_block_color(row, col, self.drag_color_direction)
                        self.last_changed_block = current_block
        return True
    
    def handle_bank_keyboard_input(self, event):
        """バンク機能のキーボード入力処理"""
        if event.key == pygame.K_UP:
            # 上矢印キー: バンク内で前のキャラクターに切り替え
            self.switch_chara_in_bank(-1)
        elif event.key == pygame.K_DOWN:
            # 下矢印キー: バンク内で次のキャラクターに切り替え
            self.switch_chara_in_bank(1)
        elif event.key == pygame.K_1:
            # 1キー: バンク内キャラクター1に切り替え
            bank_start = self.current_bank * self.chars_per_bank
            if bank_start < len(self.charas_data):
                self.switch_chara(bank_start)
        elif event.key == pygame.K_2:
            # 2キー: バンク内キャラクター2に切り替え
            bank_start = self.current_bank * self.chars_per_bank
            if bank_start + 1 < len(self.charas_data):
                self.switch_chara(bank_start + 1)
        elif event.key == pygame.K_3:
            # 3キー: バンク内キャラクター3に切り替え
            bank_start = self.current_bank * self.chars_per_bank
            if bank_start + 2 < len(self.charas_data):
                self.switch_chara(bank_start + 2)
        elif event.key == pygame.K_4:
            # 4キー: バンク内キャラクター4に切り替え
            bank_start = self.current_bank * self.chars_per_bank
            if bank_start + 3 < len(self.charas_data):
                self.switch_chara(bank_start + 3)
        elif event.key == pygame.K_5:
            # 5キー: バンク内キャラクター5に切り替え
            bank_start = self.current_bank * self.chars_per_bank
            if bank_start + 4 < len(self.charas_data):
                self.switch_chara(bank_start + 4)
        elif event.key == pygame.K_6:
            # 6キー: バンク内キャラクター6に切り替え
            bank_start = self.current_bank * self.chars_per_bank
            if bank_start + 5 < len(self.charas_data):
                self.switch_chara(bank_start + 5)
        elif event.key == pygame.K_PAGEUP:
            # PageUp: バンクを前に切り替え
            self.switch_bank(-1)
        elif event.key == pygame.K_PAGEDOWN:
            # PageDown: バンクを次に切り替え
            self.switch_bank(1)

    def load_charas_data(self):
        """charas.jsonからキャラクターデータを読み込む"""
        try:
            with open("settings/charas.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["charas"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"charas.jsonの読み込みに失敗しました: {e}")
            # デフォルトデータを返す
            return [{
                "name": "TEST-chan",
                "folder": "test"
            }]
    
    def load_stages_data(self):
        """現在のキャラクターのステージデータを読み込む"""
        if not self.current_chara:
            return []
        
        try:
            stage_json_path = os.path.join(self.current_chara["folder"], "stage.json")
            with open(stage_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["stages"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"{self.current_chara['folder']}/stage.jsonの読み込みに失敗しました: {e}")
            # デフォルトのステージデータを返す
            return [
                {
                    "stage": 1,
                    "definition": "block_layout_stage1",
                    "foreground": "stage1.png",
                    "background": "back.png",
                    "bonus": "gohoubi.png",
                    "target_score": 5000,
                    "target_time": 30,
                    "time_bonus_multiplier": 100
                }
            ]
    
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
    
    def load_foreground_image(self):
        """前景画像を読み込む。画像がない場合は、ブロック配置に基づいて色付きの前景を生成"""
        try:
            foreground_path = os.path.join(self.current_chara["folder"], self.current_stage_config["foreground"])
            if self.current_stage_config["foreground"]:  # 前景画像のファイル名が指定されている場合
                foreground = pygame.image.load(foreground_path)
                return pygame.transform.scale(foreground, (SCREEN_WIDTH, SCREEN_HEIGHT))
            else:
                # 前景画像が指定されていない場合は、色付きの前景を生成
                return self.create_colored_foreground()
        except (pygame.error, FileNotFoundError):
            print(f"前景画像が見つかりません: {foreground_path}")
            return self.create_colored_foreground()
    
    def create_colored_foreground(self):
        """ブロック配置に基づいて色付きの前景画像を生成"""
        # 前景画像のベースサーフェスを作成
        foreground = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        foreground.fill(WHITE)  # 基本は白で塗りつぶし
        
        # CSVファイルからブロック配置を読み込み
        csv_path = os.path.join(self.current_chara["folder"], f"{self.current_stage_config['definition']}.csv")
        block_layout = self.load_block_layout_from_csv(csv_path)
        
        # stage.jsonにforeground_colorsが定義されている場合はそれを使用
        foreground_colors = self.current_stage_config.get('foreground_colors', {})
        if isinstance(foreground_colors, list):
            # リスト形式の場合は辞書に変換
            color_dict = {}
            for item in foreground_colors:
                for key, value in item.items():
                    color_dict[int(key)] = tuple(value)
            foreground_colors = color_dict
        
        # ブロック配置に基づいて各ブロックの色を設定
        for row in range(len(block_layout)):
            for col in range(len(block_layout[row])):
                durability = block_layout[row][col]
                if durability != 0:  # ブロックがある場所
                    x = col * BLOCK_SIZE
                    y = row * BLOCK_SIZE + GAME_AREA_START_Y
                    
                    # 色を決定（foreground_colorsが優先、なければBLOCK_COLORS）
                    if durability in foreground_colors:
                        color = foreground_colors[durability]
                    else:
                        color = BLOCK_COLORS.get(durability, WHITE)
                    
                    if color:  # Noneでない場合のみ描画
                        pygame.draw.rect(foreground, color, (x, y, BLOCK_SIZE, BLOCK_SIZE))
        
        return foreground
    
    def load_current_stage_resources(self):
        """現在のステージのリソースを読み込む"""
        if not self.current_stage_config or not self.current_chara:
            return
        
        # 前景画像の読み込み
        self.foreground_image = self.load_foreground_image()
        
        # 背景画像の読み込み
        try:
            background_path = os.path.join(self.current_chara["folder"], self.current_stage_config["background"])
            self.background_image = pygame.image.load(background_path)
            self.background_image = pygame.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"背景画像が見つかりません: {background_path}")
            self.background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background_image.fill(BLACK)
        
        # ブロック配置の読み込み
        csv_path = os.path.join(self.current_chara["folder"], f"{self.current_stage_config['definition']}.csv")
        self.current_layout = self.load_block_layout_from_csv(csv_path)
    
    def get_current_bank_chars(self):
        """現在のバンクのキャラクターリストを取得"""
        start_idx = self.current_bank * self.chars_per_bank
        end_idx = min(start_idx + self.chars_per_bank, len(self.charas_data))
        return self.charas_data[start_idx:end_idx]
    
    def switch_bank(self, direction):
        """バンクを切り替える（direction: 1で次へ、-1で前へ）"""
        new_bank = self.current_bank + direction
        if 0 <= new_bank < self.total_banks:
            self.current_bank = new_bank
            
            # 現在のキャラクターが新しいバンクに含まれていない場合、
            # バンクの最初のキャラクターに切り替える
            bank_start = self.current_bank * self.chars_per_bank
            bank_end = min(bank_start + self.chars_per_bank, len(self.charas_data))
            
            if not (bank_start <= self.current_chara_index < bank_end):
                self.switch_chara(bank_start)
            
            print(f"バンク {self.current_bank + 1}/{self.total_banks} に切り替えました")
            self.save_message = f"バンク {self.current_bank + 1}/{self.total_banks}"
            self.save_message_timer = 120
        else:
            print(f"無効なバンク: {new_bank + 1}")

    def switch_chara_in_bank(self, direction):
        """現在のバンク内でキャラクターを切り替える（direction: 1で次へ、-1で前へ）"""
        bank_start = self.current_bank * self.chars_per_bank
        bank_end = min(bank_start + self.chars_per_bank, len(self.charas_data))
        bank_chars = list(range(bank_start, bank_end))
        
        if not bank_chars:
            return
            
        try:
            current_pos = bank_chars.index(self.current_chara_index)
            new_pos = (current_pos + direction) % len(bank_chars)
            self.switch_chara(bank_chars[new_pos])
        except ValueError:
            # 現在のキャラクターがバンクに含まれていない場合
            self.switch_chara(bank_chars[0])

    def get_current_bank_info(self):
        """現在のバンク情報を取得"""
        return {
            'current_bank': self.current_bank,
            'total_banks': self.total_banks,
            'bank_start': self.current_bank * self.chars_per_bank,
            'bank_chars': self.get_current_bank_chars()
        }
    
    def run(self):
        """メインループ"""
        running = True
        while running:
            running = self.handle_events()
            
            # 画面クリア - 最初に背景全体を描画
            current_background = self.get_current_background()
            self.screen.blit(current_background, (0, 0))
            
            # 描画
            self.draw_grid()
            self.draw_blocks()
            self.draw_info()
            
            # 画面更新
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    viewer = LayoutViewer()
    viewer.run()
