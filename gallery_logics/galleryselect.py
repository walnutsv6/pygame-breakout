import pygame
import json
import os
from constants.constants import *
from select_logics.base import BaseSelector

class GalleryCharacterSelect(BaseSelector):
    def __init__(self, restore_state=None):
        """画像閲覧モード用キャラクター選択画面を初期化"""
        super().__init__(title="ＣＧを見たいキャラクターを選んでください", subtitle="※クリア済みのキャラクターのみ選択可能")
        
        # キャラクターデータを読み込み（SaveManagerを使用）
        # 読み込みする前にセーブデータのチェックと拡張を行う
        self.save_manager.check_and_extend_save_data()
        self.charas_data = self.save_manager.load_charas_data()
        
        # 選択状態
        self.selected_chara_index = 0  # selected_indexからselected_chara_indexに変更
        self.selected_item_type = "chara"  # "chara", "back"
        self.chara_buttons = []
        
        # アンロックされたキャラクターとクリア済みキャラクターを取得
        self.unlocked_charas = self.get_unlocked_charas()
        self.cleared_charas = self.get_cleared_charas()
        
        # 選択可能なキャラクターのインデックスリストを作成
        self.selectable_indices = []
        for i, chara in enumerate(self.unlocked_charas):
            if chara in self.cleared_charas:
                self.selectable_indices.append(i)
        
        # ページネーションを設定
        self.setup_pagination(len(self.unlocked_charas))
        
        # 状態復元がある場合は適用
        if restore_state:
            self.restore_page_state(restore_state)
        
        # 初期選択位置を選択可能なキャラクターに設定
        if self.selectable_indices:
            # 復元された選択インデックスが有効かチェック
            current_page_start = self.current_page * self.chars_per_page
            current_page_end = current_page_start + len(self.get_current_page_items(self.unlocked_charas))
            if not (current_page_start <= self.selected_chara_index < current_page_end and self.selected_chara_index in self.selectable_indices):
                self.selected_chara_index = self.selectable_indices[0]
        else:
            self.selected_item_type = "back"
        
        # ボタンの配置を計算
        self.calculate_button_positions()
    
        # 背景色を紫系に変更
        self.background.fill((30, 15, 40))  # 濃い紫色
    
    def get_unlocked_charas(self):
        """アンロックされているキャラクターのリストを取得（SaveManagerに移行済み）"""
        unlocked_charas = []
        for chara in self.charas_data:
            if self.save_manager.is_chara_unlocked(chara, self.charas_data):
                unlocked_charas.append(chara)
        return unlocked_charas
    
    def get_cleared_charas(self):
        """クリア済みのキャラクターのリストを取得"""
        cleared_charas = []
        for chara in self.unlocked_charas:
            if self.is_chara_cleared(chara):
                cleared_charas.append(chara)
        return cleared_charas
    
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
        
        # 戻るボタンの配置
        self.back_button_rect = pygame.Rect(self.button_positions["back"]["x"], 
                                           self.button_positions["back"]["y"], 
                                           self.button_positions["back"]["width"], 
                                           self.button_positions["back"]["height"])
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_q:  # Qキーで前のページ
                    if self.go_prev_page():
                        self.selected_chara_index = 0
                        self.calculate_button_positions()
                elif event.key == pygame.K_e:  # Eキーで次のページ
                    if self.go_next_page():
                        self.selected_chara_index = 0
                        self.calculate_button_positions()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # ページボタンのクリック判定
                    page_result = self.handle_page_button_click(mouse_pos)
                    if page_result:
                        self.selected_chara_index = 0
                        self.calculate_button_positions()
                        continue
                    
                    # 戻るボタンのクリック判定
                    if self.back_button_rect.collidepoint(mouse_pos):
                        return None
                    
                    # キャラクターボタンのクリック判定
                    for button in self.chara_buttons:
                        if button["rect"].collidepoint(mouse_pos):
                            # クリア済みのキャラクターのみ選択可能
                            if button["chara"] in self.cleared_charas:
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
                    # 戻るボタンのホバー判定
                    if self.back_button_rect.collidepoint(mouse_pos):
                        self.selected_item_type = "back"
        
        return "continue"
    
    def move_selection(self, direction):
        """左右キーでの選択移動"""
        if self.selected_item_type == "chara":
            if self.selectable_indices:
                # 現在の選択インデックスが選択可能なリストの何番目かを見つける
                try:
                    current_pos = self.selectable_indices.index(self.selected_chara_index)
                    new_pos = current_pos + direction
                    
                    if 0 <= new_pos < len(self.selectable_indices):
                        self.selected_chara_index = self.selectable_indices[new_pos]
                    elif direction > 0:
                        # 右端から戻るボタンへ
                        self.selected_item_type = "back"
                    elif direction < 0:
                        # 左端から戻るボタンへ
                        self.selected_item_type = "back"
                except ValueError:
                    # 現在のインデックスが選択可能でない場合、最初の選択可能なインデックスに移動
                    if self.selectable_indices:
                        self.selected_chara_index = self.selectable_indices[0]
                    else:
                        self.selected_item_type = "back"
            else:
                # 選択可能なキャラクターがいない場合は戻るボタンのみ
                self.selected_item_type = "back"
        elif self.selected_item_type == "back":
            if self.selectable_indices:
                # 戻るボタンから最初/最後の選択可能なキャラクターに移動
                if direction > 0:
                    self.selected_chara_index = self.selectable_indices[0]
                else:
                    self.selected_chara_index = self.selectable_indices[-1]
                self.selected_item_type = "chara"
    
    def move_selection_vertical(self, direction):
        """上下キーでの選択移動"""
        if self.selected_item_type == "chara":
            if direction > 0:
                # 下キー：戻るボタンへ
                self.selected_item_type = "back"
        elif self.selected_item_type == "back":
            if direction < 0 and self.selectable_indices:
                # 上キー：最初の選択可能なキャラクターへ
                self.selected_chara_index = self.selectable_indices[0]
                self.selected_item_type = "chara"
    
    def activate_selected_item(self):
        """選択中の項目をアクティベート"""
        if self.selected_item_type == "chara":
            # 選択可能なキャラクターかチェック
            if self.selected_chara_index in self.selectable_indices:
                return self.unlocked_charas[self.selected_chara_index]
        elif self.selected_item_type == "back":
            return None
        return "continue"
    
    def draw(self):
        """画面描画"""
        # 背景を描画
        self.screen.blit(self.background, (0, 0))
        
        # タイトルを描画
        self.draw_title()
        
        # キャラクターボタンを描画
        for i, button in enumerate(self.chara_buttons):
            rect = button["rect"]
            chara = button["chara"]
            
            # キャラクターの状態を判定
            is_cleared = chara in self.cleared_charas
            is_selectable = is_cleared
            
            # ボタンの背景色
            if i == self.selected_chara_index and self.selected_item_type == "chara":
                if is_selectable:
                    button_color = self.colors["button_special"]  # 紫（選択中・選択可能）
                    border_color = self.colors["border_selected"]
                    border_width = 3
                else:
                    button_color = self.colors["button_disabled"]  # グレー（選択中・選択不可）
                    border_color = (200, 200, 200)
                    border_width = 3
            else:
                if is_selectable:
                    button_color = (80, 60, 120)   # 暗い紫（非選択・選択可能）
                    border_color = self.colors["border_normal"]
                    border_width = 2
                else:
                    button_color = self.colors["button_disabled"]    # 暗いグレー（非選択・選択不可）
                    border_color = self.colors["border_disabled"]
                    border_width = 1
            
            # ボタンの描画
            pygame.draw.rect(self.screen, button_color, rect)
            pygame.draw.rect(self.screen, border_color, rect, border_width)
            
            # キャラクター画像を描画
            self.draw_character_icon(chara, rect, is_cleared, i == self.selected_chara_index and self.selected_item_type == "chara", is_selectable)
            
            # キャラクター名と状態を描画
            self.draw_character_name_and_status(chara, rect, is_cleared, is_selectable)
        
        # 戻るボタン
        back_color = self.colors["button_selected"] if self.selected_item_type == "back" else self.colors["button_normal"]
        back_border = self.colors["border_selected"] if self.selected_item_type == "back" else self.colors["border_normal"]
        back_border_width = 3 if self.selected_item_type == "back" else 2
        
        pygame.draw.rect(self.screen, back_color, self.back_button_rect)
        pygame.draw.rect(self.screen, back_border, self.back_button_rect, back_border_width)
        back_text = self.small_font.render("戻る", True, self.colors["text_normal"])
        back_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, back_rect)
        
        # ページ切り替えボタンを描画
        self.draw_page_buttons(self.selected_item_type)
        
        # 操作説明
        if self.total_pages > 1:
            self.draw_help_text("矢印キー: 選択  Enter/Space: 決定  Q/E: ページ切替  ESC: 戻る")
        else:
            self.draw_help_text("矢印キー: 選択  Enter/Space: 決定  ESC: 戻る")
        
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

def select_gallery_character(restore_state=None):
    """画像閲覧用キャラクター選択メイン関数"""
    gallery_select = GalleryCharacterSelect(restore_state)
    result = gallery_select.run()
    
    # 結果と現在の状態を両方返す
    if result is None:
        # キャンセルされた場合、現在の状態も一緒に返す
        return None, gallery_select.get_page_state()
    else:
        # キャラクターが選択された場合
        return result, gallery_select.get_page_state()
