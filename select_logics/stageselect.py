import pygame
import json
import os
from constants.constants import *
from gallery_logics.galleryselect import select_gallery_character, GalleryCharacterSelect
from select_logics.base import BaseSelector
from save_manager import SaveManager

class StageSelect(BaseSelector):
    def __init__(self, restore_state=None):
        """ステージセレクト画面を初期化"""
        super().__init__(title="ステージセレクト", subtitle="遊びたいキャラクターを選択してください")
        
        # セーブデータ管理クラスの初期化（親クラスでも初期化されるが、早めに初期化）
        if not hasattr(self, 'save_manager'):
            self.save_manager = SaveManager()
        
        # キャラクターデータを読み込み（SaveManagerを使用）
        # 読み込みする前にセーブデータのチェックと拡張を行う
        self.save_manager.check_and_extend_save_data()
        self.charas_data = self.save_manager.load_charas_data()
        
        # 選択状態
        self.selected_chara_index = 0
        self.selected_item_type = "chara"  # "chara", "back", "reset", "gallery"
        self.chara_buttons = []
        
        # アンロックされたキャラクターのみを取得
        self.unlocked_charas = self.get_unlocked_charas()
        
        # ページネーションを設定
        self.setup_pagination(len(self.unlocked_charas))
        
        # 状態復元がある場合は適用
        if restore_state:
            self.restore_page_state(restore_state)
        
        # キャラクターボタンの配置を計算
        self.calculate_button_positions()
    
    def load_stage_data(self, chara_folder):
        """指定されたキャラクターのステージデータを読み込む（SaveManagerに移行済み）"""
        return self.save_manager.load_stage_data(chara_folder)
    
    def get_unlocked_charas(self):
        """アンロックされているキャラクターのリストを取得（SaveManagerに移行済み）"""
        unlocked_charas = []
        for chara in self.charas_data:
            if self.save_manager.is_chara_unlocked(chara, self.charas_data):
                unlocked_charas.append(chara)
        return unlocked_charas
    
    def reset_save_data(self):
        """セーブデータを初期化"""
        if self.save_manager.reset_all_save_data():
            # アンロックされたキャラクターのリストを再読み込み
            self.unlocked_charas = self.get_unlocked_charas()
            
            # ページネーションを再設定
            self.setup_pagination(len(self.unlocked_charas))
            
            # ボタン配置を再計算
            self.calculate_button_positions()
            
            # 選択インデックスを安全な範囲にリセット
            if len(self.unlocked_charas) > 0:
                self.selected_chara_index = 0
                self.selected_item_type = "chara"
            else:
                # アンロックされたキャラクターがいない場合は適切なボタンを選択
                self.selected_item_type = "gallery"
            
            return True
        else:
            return False
    
    def calculate_button_positions(self):
        """キャラクターボタンの配置を計算"""
        self.chara_buttons = []
        
        # 現在のページに表示するキャラクターを取得
        current_page_charas = self.get_current_page_items(self.unlocked_charas)
        
        if len(current_page_charas) <= 3:
            # 3人以下の場合は横に並べる
            button_width = 200
            button_height = 300
            total_width = len(current_page_charas) * button_width + (len(current_page_charas) - 1) * 20
            start_x = (SCREEN_WIDTH - total_width) // 2
            y = SCREEN_HEIGHT // 2 - button_height // 2
            
            for i, chara in enumerate(current_page_charas):
                x = start_x + i * (button_width + 20)
                rect = pygame.Rect(x, y, button_width, button_height)
                self.chara_buttons.append({
                    "rect": rect,
                    "chara": chara,
                    "index": i
                })
        else:
            # 4人以上の場合はグリッド状に配置（最大6人まで）
            cols = 3
            rows = min(2, (len(current_page_charas) + cols - 1) // cols)
            button_width = 200
            button_height = 300
            
            grid_width = cols * button_width + (cols - 1) * 15
            grid_height = rows * button_height + (rows - 1) * 15
            start_x = (SCREEN_WIDTH - grid_width) // 2
            start_y = (SCREEN_HEIGHT - grid_height) // 2
            
            for i, chara in enumerate(current_page_charas):
                row = i // cols
                col = i % cols
                x = start_x + col * (button_width + 15)
                y = start_y + row * (button_height + 15)
                rect = pygame.Rect(x, y, button_width, button_height)
                self.chara_buttons.append({
                    "rect": rect,
                    "chara": chara,
                    "index": i
                })

        # 画像閲覧ボタンの配置（左側に移動）
        self.gallery_button_rect = pygame.Rect(self.button_positions["back"]["x"], 
                                             self.button_positions["back"]["y"], 
                                             self.button_positions["back"]["width"], 
                                             self.button_positions["back"]["height"])
        
        # セーブデータ初期化ボタンの配置（右側はそのまま）
        self.reset_button_rect = pygame.Rect(self.button_positions["right"]["x"], 
                                           self.button_positions["right"]["y"], 
                                           self.button_positions["right"]["width"], 
                                           self.button_positions["right"]["height"])
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            # 確認ダイアログのイベント処理を優先
            if self.handle_confirmation_dialog_events(event):
                continue
                
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_LEFT:
                    if self.selected_item_type == "chara":
                        self.move_selection(-1)
                    else:
                        self.move_selection(-1)
                elif event.key == pygame.K_RIGHT:
                    if self.selected_item_type == "chara":
                        self.move_selection(1)
                    else:
                        self.move_selection(1)
                elif event.key == pygame.K_UP:
                    self.move_selection_vertical(-1)
                elif event.key == pygame.K_DOWN:
                    self.move_selection_vertical(1)
                elif event.key == pygame.K_q:  # Qキーで前のページ
                    if self.go_prev_page():
                        self.selected_chara_index = 0
                        self.calculate_button_positions()
                elif event.key == pygame.K_e:  # Eキーで次のページ
                    if self.go_next_page():
                        self.selected_chara_index = 0
                        self.calculate_button_positions()
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    result = self.activate_selected_item()
                    if result != "continue":
                        return result
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # ページボタンのクリック判定
                    page_result = self.handle_page_button_click(mouse_pos)
                    if page_result:
                        self.selected_chara_index = 0
                        self.calculate_button_positions()
                        continue
                    
                    # 初期化ボタンのクリック判定
                    if self.reset_button_rect.collidepoint(mouse_pos):
                        self.show_confirmation_dialog("セーブデータ初期化", 
                                                    "全てのセーブデータを初期化しますか？\nこの操作は取り消せません。", 
                                                    self.reset_save_data)
                    
                    # 画像閲覧ボタンのクリック判定
                    if self.gallery_button_rect.collidepoint(mouse_pos):
                        return "gallery"
                    
                    # キャラクターボタンのクリック判定
                    for button in self.chara_buttons:
                        if button["rect"].collidepoint(mouse_pos):
                            return button["chara"]
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                
                # ページボタンのホバー判定
                page_hover = self.handle_page_button_hover(mouse_pos)
                if page_hover:
                    self.selected_item_type = page_hover
                    continue
                
                # キャラクターボタンのホバー判定
                for button in self.chara_buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self.selected_item_type = "chara"
                        self.selected_chara_index = button["index"]
                        break
                else:
                    # 初期化ボタンのホバー判定
                    if self.reset_button_rect.collidepoint(mouse_pos):
                        self.selected_item_type = "reset"
                    # 画像閲覧ボタンのホバー判定
                    elif self.gallery_button_rect.collidepoint(mouse_pos):
                        self.selected_item_type = "gallery"
        
        return "continue"
    
    def move_selection(self, direction):
        """左右キーでの選択移動"""
        current_page_charas = self.get_current_page_items(self.unlocked_charas)
        
        if self.selected_item_type == "chara":
            new_index = self.selected_chara_index + direction
            if 0 <= new_index < len(current_page_charas):
                self.selected_chara_index = new_index
            elif direction > 0:
                # 右端から下のボタンへ
                if self.total_pages > 1:
                    self.selected_item_type = "page_prev"
                else:
                    self.selected_item_type = "gallery"
            elif direction < 0:
                # 左端から右下のボタンへ
                self.selected_item_type = "reset"
        elif self.selected_item_type == "gallery":
            if direction > 0:
                if self.total_pages > 1:
                    self.selected_item_type = "page_prev"
                else:
                    self.selected_item_type = "reset"
            else:
                # 最後のキャラクターに戻る
                self.selected_item_type = "chara"
                self.selected_chara_index = len(current_page_charas) - 1
        elif self.selected_item_type == "page_prev":
            if direction > 0:
                self.selected_item_type = "page_next"
            else:
                self.selected_item_type = "gallery"
        elif self.selected_item_type == "page_next":
            if direction > 0:
                self.selected_item_type = "reset"
            else:
                self.selected_item_type = "page_prev"
        elif self.selected_item_type == "reset":
            if direction < 0:
                if self.total_pages > 1:
                    self.selected_item_type = "page_next"
                else:
                    self.selected_item_type = "gallery"
            else:
                # 最初のキャラクターに戻る
                self.selected_item_type = "chara"
                self.selected_chara_index = 0
    
    def move_selection_vertical(self, direction):
        """上下キーでの選択移動"""
        current_page_charas = self.get_current_page_items(self.unlocked_charas)
        
        if self.selected_item_type == "chara":
            if direction > 0:
                # 下キー：ボタンエリアへ
                self.selected_item_type = "gallery"
            # 上キーは何もしない（既に最上部）
        elif self.selected_item_type in ["gallery", "page_prev", "page_next", "reset"]:
            if direction < 0:
                # 上キー：キャラクターエリアへ
                self.selected_item_type = "chara"
                # 現在のボタンに近いキャラクターを選択
                if self.selected_item_type == "gallery":
                    self.selected_chara_index = 0
                elif self.selected_item_type in ["page_prev", "page_next"]:
                    self.selected_chara_index = min(len(current_page_charas) - 1, 1)
                else:  # reset
                    self.selected_chara_index = min(len(current_page_charas) - 1, 2)
            # 下キーは何もしない（既に最下部）
    
    def is_hard_character(self, chara):
        """キャラクターの難易度選択をチェック"""
        # available_difficultiesが設定されていない場合は全難易度利用可能（通常キャラクター）
        if "available_difficulties" not in chara:
            return False
        
        available_difficulties = chara["available_difficulties"]

        # Medleyのみが設定されている場合はメドレーキャラクター
        if "medley" in available_difficulties:
            return "medley"
        # EasyとNormalの両方が利用できない場合はボスキャラクター
        if "easy" not in available_difficulties and "normal" not in available_difficulties:
            return "boss"
        # Hardが利用可能な場合は難しいキャラクター
        elif "hard" in available_difficulties:
            return "hard"
        
        return False
    
    def is_boss_character(self, chara):
        """キャラクターがボスキャラクター（EasyとNormalが選択できない）かどうかをチェック"""
        # available_difficultiesが設定されていない場合は全難易度利用可能（通常キャラクター）
        if "available_difficulties" not in chara:
            return False
        
        available_difficulties = chara["available_difficulties"]
        
        
        
        return False
    
    def activate_selected_item(self):
        """選択中の項目をアクティベート"""
        current_page_charas = self.get_current_page_items(self.unlocked_charas)
        
        if self.selected_item_type == "chara":
            return current_page_charas[self.selected_chara_index]
        elif self.selected_item_type == "gallery":
            return "gallery"
        elif self.selected_item_type == "reset":
            self.show_confirmation_dialog("セーブデータ初期化", 
                                        "全てのセーブデータを初期化しますか？\nこの操作は取り消せません。", 
                                        self.reset_save_data)
            return "continue"
        elif self.selected_item_type == "page_prev":
            if self.go_prev_page():
                self.selected_chara_index = 0
                self.calculate_button_positions()
            return "continue"
        elif self.selected_item_type == "page_next":
            if self.go_next_page():
                self.selected_chara_index = 0
                self.calculate_button_positions()
            return "continue"
        return "continue"
    
    def draw(self):
        """画面描画"""
        # 背景を描画
        self.screen.blit(self.background, (0, 0))
        
        # タイトルを描画
        self.draw_title()
        
        # キャラクターボタンを描画
        current_page_charas = self.get_current_page_items(self.unlocked_charas)
        for i, button in enumerate(self.chara_buttons):
            rect = button["rect"]
            chara = button["chara"]
            
            # セーブデータを取得
            save_info = self.save_manager.get_chara_data(chara["folder"])
            is_cleared = save_info["clear"] == 1
            hi_score = save_info["hi_score"]
            
            # 難易度チェック
            is_hard_character = self.is_hard_character(chara)
            
            # ボタンの背景色（選択状態とキャラクタータイプで色を変える）
            if i == self.selected_chara_index and self.selected_item_type == "chara":
                if is_hard_character == "boss":
                    button_color = (160, 80, 80)   # 赤系（選択中・ボスキャラクター）
                elif is_hard_character in ["hard","medley"]:
                    button_color = (120, 80, 140)  # 紫系（選択中・難しいキャラクター）
                else:
                    button_color = self.colors["button_selected"]  # 明るい青（選択中・通常キャラクター）
                border_color = self.colors["border_selected"]
                border_width = 3
            else:
                if is_hard_character == "boss":
                    button_color = (100, 50, 50)   # 暗い赤（非選択・ボスキャラクター）
                    border_color = (160, 80, 80)
                elif is_hard_character in ["hard","medley"]:
                    button_color = (80, 50, 100)   # 暗い紫（非選択・難しいキャラクター）
                    border_color = (120, 80, 140)
                else:
                    button_color = self.colors["button_normal"]   # 暗い青（非選択・通常キャラクター）
                    border_color = self.colors["border_normal"]
                border_width = 2
            
            # ボタンの描画
            pygame.draw.rect(self.screen, button_color, rect)
            pygame.draw.rect(self.screen, border_color, rect, border_width)
            
            # キャラクター画像を描画
            self.draw_character_icon(chara, rect, is_cleared, i == self.selected_chara_index and self.selected_item_type == "chara", True)
            
            # キャラクター名を描画
            if is_cleared:
                name_color = self.colors["text_cleared"]  # 金色（クリア済み）
            elif is_hard_character == "boss":
                name_color = (255, 180, 180)  # 薄い赤色（ボスキャラクター）
            elif is_hard_character in ["hard","medley"]:
                name_color = (200, 150, 220)  # 薄い紫色（難しいキャラクター）
            else:
                name_color = self.colors["text_normal"]   # 白色（通常キャラクター）
            
            name_text = self.small_font.render(chara["name"], True, name_color)
            name_rect = name_text.get_rect()
            name_x = rect.centerx - name_rect.width // 2
            name_y = rect.bottom - 75
            self.screen.blit(name_text, (name_x, name_y))
            
            # ハイスコアの表示
            if hi_score > 0:
                hi_score_text = self.tiny_font.render(f"Hi: {hi_score}", True, WHITE)
                hi_score_rect = hi_score_text.get_rect()
                hi_score_x = rect.centerx - hi_score_rect.width // 2
                hi_score_y = rect.bottom - 50
                self.screen.blit(hi_score_text, (hi_score_x, hi_score_y))
            
            # ステージ数の表示
            stages = self.load_stage_data(chara["folder"])
            stage_count_text = self.tiny_font.render(f"{len(stages)}ステージ", True, WHITE)
            stage_count_rect = stage_count_text.get_rect()
            stage_count_x = rect.centerx - stage_count_rect.width // 2
            stage_count_y = rect.bottom - 30
            self.screen.blit(stage_count_text, (stage_count_x, stage_count_y))
            
            # クリア済みの場合はクリアマークを表示
            if is_cleared:
                clear_text = self.tiny_font.render("♥CLEARED♥", True, self.colors["text_cleared"])
            # クリアしていないならキャラクタータイプ表示
            elif is_hard_character == "boss":
                clear_text = self.tiny_font.render("BOSS", True, (255, 150, 150))
            elif is_hard_character == "hard":
                clear_text = self.tiny_font.render("HARD", True, (200, 150, 220))
            elif is_hard_character == "medley":
                clear_text = self.tiny_font.render("MEDLEY", True, self.colors["text_normal"])
            else:
                clear_text = self.tiny_font.render("NORMAL", True, self.colors["text_normal"])
            clear_rect = clear_text.get_rect()
            clear_x = rect.centerx - clear_rect.width // 2
            clear_y = rect.top + 5
            self.screen.blit(clear_text, (clear_x, clear_y))
        
        # 画像閲覧ボタン（左側に移動）
        gallery_color = self.colors["button_selected"] if self.selected_item_type == "gallery" else self.colors["button_special"]
        gallery_border = self.colors["border_selected"] if self.selected_item_type == "gallery" else self.colors["border_normal"]
        gallery_border_width = 3 if self.selected_item_type == "gallery" else 2
        
        pygame.draw.rect(self.screen, gallery_color, self.gallery_button_rect)
        pygame.draw.rect(self.screen, gallery_border, self.gallery_button_rect, gallery_border_width)
        gallery_text = self.small_font.render("ＣＧ閲覧", True, self.colors["text_normal"])
        gallery_text_rect = gallery_text.get_rect(center=self.gallery_button_rect.center)
        self.screen.blit(gallery_text, gallery_text_rect)
        
        # ページ切り替えボタンを描画
        self.draw_page_buttons(self.selected_item_type)
        
        # セーブデータ初期化ボタン
        reset_color = self.colors["button_selected"] if self.selected_item_type == "reset" else (120, 60, 60)  # 赤系
        reset_border = self.colors["border_selected"] if self.selected_item_type == "reset" else (150, 100, 100)
        reset_border_width = 3 if self.selected_item_type == "reset" else 2
        
        pygame.draw.rect(self.screen, reset_color, self.reset_button_rect)
        pygame.draw.rect(self.screen, reset_border, self.reset_button_rect, reset_border_width)
        reset_text = self.small_font.render("データ初期化", True, self.colors["text_normal"])
        reset_text_rect = reset_text.get_rect(center=self.reset_button_rect.center)
        self.screen.blit(reset_text, reset_text_rect)
        
        # 確認ダイアログを描画
        self.draw_confirmation_dialog()
        
        # 操作説明
        if self.total_pages > 1:
            self.draw_help_text("矢印キー: 選択  Enter/Space: 決定  Q/E: ページ切替  ESC: 終了")
        else:
            self.draw_help_text("矢印キー: 選択  Enter/Space: 決定  ESC: 終了")
        
        pygame.display.flip()
    
    def run(self):
        """メインループ"""
        while True:
            result = self.handle_events()
            
            if result is None:
                # 終了またはキャンセル
                return None
            elif result == "continue":
                # 継続
                pass
            else:
                # キャラクターが選択された
                return result
            
            self.draw()
            self.clock.tick(60)

def select_chara(restore_state=None):
    """キャラクター選択メイン関数"""
    stage_select = StageSelect(restore_state)
    
    # アンロックされたキャラクターが1人だけの場合は自動選択
    if len(stage_select.unlocked_charas) == 1:
        return stage_select.unlocked_charas[0]
    
    # 複数いる場合は選択画面を表示
    result = stage_select.run()
    
    # 画像閲覧モードが選択された場合
    if result == "gallery":
        # 現在のStageSelectの状態を保存
        stage_select_state = stage_select.get_page_state()
        gallery_state = stage_select_state  # 最初はStageSelectの状態を使用
        
        while True:
            # ギャラリー選択画面を表示
            selected_chara, updated_gallery_state = select_gallery_character(gallery_state)
            
            if selected_chara is not None:
                # 画像閲覧モードを開始
                from gallery_logics.gallery import show_gallery
                show_gallery(selected_chara)
                
                # 画像閲覧から戻ってきた場合、ギャラリー選択画面の状態を保持
                gallery_state = updated_gallery_state
                continue
            else:
                # ギャラリー選択画面でキャンセルされた場合、
                # ギャラリー選択画面の現在の状態をStageSelectに反映
                return select_chara(updated_gallery_state)
    
    return result
