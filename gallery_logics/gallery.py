import pygame
import os
import json
import csv
from constants.constants import *

class Gallery:
    def __init__(self, chara):
        """画像閲覧モードを初期化"""
        self.chara = chara
        self.screen = pygame.display.get_surface()
        if self.screen is None:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption(f"画像閲覧 - {chara['name']}")
        self.clock = pygame.time.Clock()
        
        # フォントの設定
        try:
            self.font = pygame.font.Font("PixelMplus12-Regular.ttf", 32)
            self.small_font = pygame.font.Font("PixelMplus12-Regular.ttf", 24)
            self.tiny_font = pygame.font.Font("PixelMplus12-Regular.ttf", 18)
        except (pygame.error, FileNotFoundError):
            self.font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 24)
            self.tiny_font = pygame.font.Font(None, 18)
        
        # セーブデータを読み込み
        self.save_data = self.load_save_data()
        
        # ステージデータを読み込み
        self.stages_data = self.load_stages_data()
        
        # ゲーム順序で画像リストを作成
        self.image_list = self.create_ordered_image_list()
        
        self.current_index = 0
        self.current_image = None
        
        # 情報ウィンドウの表示制御
        self.show_info = True
        
        # 背景
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background.fill((10, 10, 20))
    
    def load_save_data(self):
        """セーブデータを読み込む"""
        save_data = {}
        try:
            with open("save/save.dat", "r", encoding="utf-8") as f:
                csv_reader = csv.reader(f)
                header = next(csv_reader)  # ヘッダー行をスキップ
                
                # charas.jsonからキャラクターの順序を取得
                charas_data = self.load_charas_data()
                chara_index = None
                for i, g in enumerate(charas_data):
                    if g["folder"] == self.chara["folder"]:
                        chara_index = i
                        break
                
                if chara_index is not None:
                    # 該当するキャラクターの行を読み込み
                    for i, row in enumerate(csv_reader):
                        if i == chara_index and len(row) >= 8:
                            save_data = {
                                "clear": int(row[0]) if row[0] else 0,
                                "hi_score": int(row[1]) if row[1] else 0,
                                "bonus_flags": [int(row[j]) if row[j] else 0 for j in range(2, 8)]
                            }
                            break
                    else:
                        # データがない場合はデフォルト値
                        save_data = {
                            "clear": 0,
                            "hi_score": 0,
                            "bonus_flags": [0, 0, 0, 0, 0, 0]
                        }
                else:
                    save_data = {
                        "clear": 0,
                        "hi_score": 0,
                        "bonus_flags": [0, 0, 0, 0, 0, 0]
                    }
        except (FileNotFoundError, csv.Error) as e:
            print(f"セーブデータの読み込みに失敗しました: {e}")
            save_data = {
                "clear": 0,
                "hi_score": 0,
                "bonus_flags": [0, 0, 0, 0, 0, 0]
            }
        
        return save_data
    
    def load_charas_data(self):
        """charas.jsonからキャラクターデータを読み込む"""
        try:
            with open("settings/charas.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["charas"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"charas.jsonの読み込みに失敗しました: {e}")
            return []
    
    def load_stages_data(self):
        """ステージデータを読み込む"""
        try:
            stage_json_path = os.path.join(self.chara["folder"], "stage.json")
            with open(stage_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["stages"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"{self.chara['folder']}/stage.jsonの読み込みに失敗しました: {e}")
            return []
    
    def create_ordered_image_list(self):
        """ゲーム順序で画像リストを作成"""
        image_list = []
        
        for stage_index, stage in enumerate(self.stages_data):
            # 前景画像
            foreground_path = os.path.join(self.chara["folder"], stage["foreground"])
            if os.path.exists(foreground_path):
                image_list.append({
                    "path": foreground_path,
                    "type": "foreground",
                    "stage": stage["stage"],
                    "filename": stage["foreground"],
                    "description": f"ステージ{stage['stage']} 前景"
                })
            
            # 背景画像
            background_path = os.path.join(self.chara["folder"], stage["background"])
            if os.path.exists(background_path):
                image_list.append({
                    "path": background_path,
                    "type": "background",
                    "stage": stage["stage"],
                    "filename": stage["background"],
                    "description": f"ステージ{stage['stage']} 背景"
                })
            
            # ボーナス画像（フラグチェック）
            if "bonus" in stage:
                bonus_path = os.path.join(self.chara["folder"], stage["bonus"])
                if os.path.exists(bonus_path):
                    # ボーナスフラグをチェック（ステージインデックスに対応）
                    if stage_index < len(self.save_data["bonus_flags"]) and self.save_data["bonus_flags"][stage_index] >= 1:
                        image_list.append({
                            "path": bonus_path,
                            "type": "bonus",
                            "stage": stage["stage"],
                            "filename": stage["bonus"],
                            "description": f"ステージ{stage['stage']} ボーナス画像"
                        })
            
            # ボーナス画像2（フラグチェック）
            if "bonus2" in stage:
                bonus2_path = os.path.join(self.chara["folder"], stage["bonus2"])
                if os.path.exists(bonus2_path):
                    # ボーナス画像2フラグをチェック（フラグが2の場合のみ表示）
                    if stage_index < len(self.save_data["bonus_flags"]) and self.save_data["bonus_flags"][stage_index] == 2:
                        image_list.append({
                            "path": bonus2_path,
                            "type": "bonus2",
                            "stage": stage["stage"],
                            "filename": stage["bonus2"],
                            "description": f"ステージ{stage['stage']} ボーナス画像2"
                        })
        
        return image_list
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_i:
                    # Iキーで情報ウィンドウの表示切り替え
                    self.show_info = not self.show_info
                elif event.key == pygame.K_LEFT and self.current_index > 0:
                    self.current_index -= 1
                    self.current_image = None
                elif event.key == pygame.K_RIGHT and self.current_index < len(self.image_list) - 1:
                    self.current_index += 1
                    self.current_image = None
        return True
    
    def load_current_image(self):
        """現在の画像を読み込み"""
        if self.current_image is None and self.image_list:
            try:
                image_info = self.image_list[self.current_index]
                self.current_image = pygame.image.load(image_info["path"])
                # 画面サイズに合わせてスケール（全画面表示）
                self.current_image = pygame.transform.scale(self.current_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except (pygame.error, FileNotFoundError):
                self.current_image = None
    
    def draw(self):
        """画面描画"""
        # 背景を描画
        self.screen.blit(self.background, (0, 0))
        
        if self.image_list:
            # 現在の画像を読み込み
            self.load_current_image()
            
            # 画像を全画面表示
            if self.current_image:
                self.screen.blit(self.current_image, (0, 0))
            
            # 情報ウィンドウを表示（Iキーで切り替え可能）
            if self.show_info:
                self.draw_info_window()
        else:
            # 画像がない場合
            no_image_text = self.font.render("表示できる画像がありません", True, WHITE)
            no_image_rect = no_image_text.get_rect()
            no_image_x = (SCREEN_WIDTH - no_image_rect.width) // 2
            no_image_y = (SCREEN_HEIGHT - no_image_rect.height) // 2
            self.screen.blit(no_image_text, (no_image_x, no_image_y))
            
            instruction_text = self.small_font.render("ESC: 戻る", True, (150, 150, 150))
            instruction_rect = instruction_text.get_rect()
            instruction_x = (SCREEN_WIDTH - instruction_rect.width) // 2
            self.screen.blit(instruction_text, (instruction_x, no_image_y + 50))
        
        pygame.display.flip()
    
    def draw_info_window(self):
        """情報ウィンドウを描画"""
        if not self.image_list:
            return
        
        # 情報ウィンドウの背景（半透明）
        info_width = 400
        info_height = 140
        info_x = (SCREEN_WIDTH - info_width) // 2
        info_y = SCREEN_HEIGHT - info_height - 20
        
        # 半透明の背景
        info_surface = pygame.Surface((info_width, info_height))
        info_surface.set_alpha(200)
        info_surface.fill((20, 20, 40))
        self.screen.blit(info_surface, (info_x, info_y))
        
        # 枠線
        pygame.draw.rect(self.screen, WHITE, (info_x, info_y, info_width, info_height), 2)
        
        # タイトル（ボーナス画像表示時は特別表示）
        if self.image_list and self.image_list[self.current_index]["type"] == "bonus2":
            # ボーナス画像2表示時：ピンク色で両横にハート2個ずつ
            title_text = f"♥♥ {self.chara['name']} ♥♥"
            title_color = (255, 150, 200)  # ピンク色
        elif self.image_list and self.image_list[self.current_index]["type"] == "bonus":
            # ボーナス画像1表示時：ピンク色で両横にハート1個ずつ
            title_text = f"♥ {self.chara['name']} ♥"
            title_color = (255, 150, 200)  # ピンク色
        else:
            # 通常表示
            title_text = self.chara["name"]
            title_color = WHITE
        
        title_surface = self.small_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect()
        title_x = info_x + (info_width - title_rect.width) // 2
        self.screen.blit(title_surface, (title_x, info_y + 10))
        
        # ページ情報
        page_text = self.small_font.render(f"{self.current_index + 1} / {len(self.image_list)}", True, (200, 200, 200))
        page_rect = page_text.get_rect()
        page_x = info_x + (info_width - page_rect.width) // 2
        self.screen.blit(page_text, (page_x, info_y + 40))
        
        # 操作説明
        controls = []
        if len(self.image_list) > 1:
            controls.append("←→: 画像切り替え")
        controls.extend(["I: 情報表示切り替え", "ESC: 戻る"])
        
        for i, control in enumerate(controls):
            control_text = self.tiny_font.render(control, True, (120, 120, 120))
            control_rect = control_text.get_rect()
            control_x = info_x + (info_width - control_rect.width) // 2
            control_y = info_y + 65 + i * 20
            self.screen.blit(control_text, (control_x, control_y))
    
    def run(self):
        """メインループ"""
        while True:
            if not self.handle_events():
                break
            
            self.draw()
            self.clock.tick(60)

def show_gallery(chara):
    """画像閲覧モードを表示（関数インターフェース）"""
    gallery = Gallery(chara)
    gallery.run()
