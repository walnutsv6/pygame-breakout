import pygame
import json
import os
from constants.constants import *
from select_logics.base import BaseSelector

class DifficultySelect(BaseSelector):
    def __init__(self, selected_chara):
        """難易度選択画面を初期化"""
        self.selected_chara = selected_chara
        super().__init__(title="難易度セレクト", subtitle="")
        
        # 難易度データを読み込み（SaveManagerを使用）
        all_difficulties = self.save_manager.load_difficulty_data()
        
        # 選択されたキャラクターの利用可能な難易度を取得
        available_difficulties = self.selected_chara.get("available_difficulties", list(all_difficulties.keys()))
        
        # 利用可能な難易度のみを抽出
        self.difficulties = {key: all_difficulties[key] for key in available_difficulties if key in all_difficulties}
        self.difficulty_keys = list(self.difficulties.keys())
        
        # キャラ数が1人だけの場合は戻るボタンをCG閲覧ボタンにする
        try:
            with open(os.path.join("settings", "charas.json"), encoding="utf-8") as f:
                charas_data = json.load(f)
            if isinstance(charas_data, dict) and "charas" in charas_data:
                chara_count = len(charas_data["charas"])
            elif isinstance(charas_data, list):
                chara_count = len(charas_data)
            else:
                chara_count = 1
        except Exception:
            chara_count = 1
        self.back_button_mode = "quit" if chara_count == 1 else "back"
        
        # 選択状態
        # Normalが利用可能ならそれを、なければ最初の難易度を選択
        if "normal" in self.difficulty_keys:
            self.selected_difficulty_index = self.difficulty_keys.index("normal")
        else:
            self.selected_difficulty_index = 0
        self.selected_item_type = "difficulty"  # "difficulty", "back", "quit"
        
        # ボタンの配置
        self.setup_buttons()
        
        # ホバー時の説明文表示用
        self.show_description = False
        self.description_text = ""

    def setup_buttons(self):
        """ボタンの配置を設定"""
        self.difficulty_buttons = []
        button_width = 150
        button_height = 60
        
        # 難易度ボタンを3列配置に変更
        cols = 3
        rows = (len(self.difficulties) + cols - 1) // cols
        
        # グリッドの開始位置を計算
        grid_width = cols * button_width + (cols - 1) * 30
        grid_height = rows * button_height + (rows - 1) * 20
        start_x = (SCREEN_WIDTH - grid_width) // 2
        start_y = 420  # キャラクター情報の下に配置
        
        for i, (key, difficulty) in enumerate(self.difficulties.items()):
            row = i // cols
            col = i % cols
            x = start_x + col * (button_width + 30)
            y = start_y + row * (button_height + 20)
            button_rect = pygame.Rect(x, y, button_width, button_height)
            self.difficulty_buttons.append({
                'rect': button_rect,
                'key': key,
                'name': difficulty['name'],
                'description': difficulty['description']
            })
        
        # 戻る/CG閲覧ボタン
        self.back_button_rect = pygame.Rect(self.button_positions["back"]["x"], 
                                           self.button_positions["back"]["y"], 
                                           self.button_positions["back"]["width"], 
                                           self.button_positions["back"]["height"])

    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.back_button_mode == "quit":
                        return "quit"
                    else:
                        return "back"
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.selected_item_type == "difficulty":
                        selected_key = self.difficulty_keys[self.selected_difficulty_index]
                        return {
                            'chara': self.selected_chara,
                            'difficulty': selected_key,
                            'difficulty_settings': self.difficulties[selected_key]
                        }
                    elif self.selected_item_type == "back":
                        if self.back_button_mode == "quit":
                            return "quit"
                        else:
                            return "back"
                elif event.key == pygame.K_UP:
                    if self.selected_item_type == "difficulty":
                        # 3列配置での上移動
                        if self.selected_difficulty_index >= 3:
                            self.selected_difficulty_index -= 3
                        else:
                            # 最上段の場合は戻る/CG閲覧ボタンに移動
                            self.selected_item_type = "back"
                    elif self.selected_item_type == "back":
                        # 戻る/CG閲覧ボタンから難易度選択の最下段に移動
                        self.selected_item_type = "difficulty"
                        # 最下段の適切な位置を計算
                        max_index = len(self.difficulty_keys) - 1
                        if max_index >= 3:
                            # 現在の列を維持しつつ最下段に移動
                            self.selected_difficulty_index = max_index - (max_index % 3) + min(1, max_index % 3)
                        else:
                            self.selected_difficulty_index = max_index
                elif event.key == pygame.K_DOWN:
                    if self.selected_item_type == "difficulty":
                        # 3列配置での下移動
                        if self.selected_difficulty_index + 3 < len(self.difficulty_keys):
                            self.selected_difficulty_index += 3
                        else:
                            # 最下段の場合は戻る/CG閲覧ボタンに移動
                            self.selected_item_type = "back"
                    elif self.selected_item_type == "back":
                        # 戻る/CG閲覧ボタンから難易度選択の最上段に移動
                        self.selected_item_type = "difficulty"
                        self.selected_difficulty_index = 0
                elif event.key == pygame.K_LEFT:
                    if self.selected_item_type == "difficulty":
                        # 3列配置での左移動
                        if self.selected_difficulty_index % 3 > 0:
                            self.selected_difficulty_index -= 1
                elif event.key == pygame.K_RIGHT:
                    if self.selected_item_type == "difficulty":
                        # 3列配置での右移動
                        if (self.selected_difficulty_index % 3 < 2 and 
                            self.selected_difficulty_index + 1 < len(self.difficulty_keys)):
                            self.selected_difficulty_index += 1
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # 難易度ボタンのクリック判定
                    for i, button in enumerate(self.difficulty_buttons):
                        if button['rect'].collidepoint(mouse_pos):
                            selected_key = button['key']
                            return {
                                'chara': self.selected_chara,
                                'difficulty': selected_key,
                                'difficulty_settings': self.difficulties[selected_key]
                            }
                    
                    # 戻る/終了ボタンのクリック判定
                    if self.back_button_rect.collidepoint(mouse_pos):
                        if self.back_button_mode == "quit":
                            return "quit"
                        else:
                            return "back"
            
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                self.show_description = False
                
                # マウスホバー時の処理
                for i, button in enumerate(self.difficulty_buttons):
                    if button['rect'].collidepoint(mouse_pos):
                        self.selected_item_type = "difficulty"
                        self.selected_difficulty_index = i
                        self.show_description = True
                        self.description_text = button['description']
                        break
                
                if self.back_button_rect.collidepoint(mouse_pos):
                    self.selected_item_type = "back"
                    self.show_description = False
        
        return None

    def draw(self):
        """画面描画"""
        self.screen.blit(self.background, (0, 0))
        
        # タイトルを描画
        self.draw_title()
        
        # キャラクター情報エリア
        char_area_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 110, 600, 220)
        pygame.draw.rect(self.screen, (40, 40, 60), char_area_rect)
        pygame.draw.rect(self.screen, self.colors["text_normal"], char_area_rect, 2)
        
        # キャラクターアイコンの表示
        icon_size = (160, 200)
        icon_x = char_area_rect.x + 10
        icon_y = char_area_rect.y + 10
        
        # セーブデータからクリア状態を取得
        save_info = self.save_manager.get_chara_data(self.selected_chara["folder"])
        is_cleared = save_info["clear"] == 1
        
        # キャラクター画像を描画
        icon_rect = pygame.Rect(icon_x, icon_y, icon_size[0], icon_size[1])
        self.draw_character_icon(self.selected_chara, icon_rect, is_cleared, False, True, (icon_x, icon_y))
        
        # キャラクター名（クリア状態で色を変える）
        if is_cleared:
            name_color = self.colors["text_cleared"]  # 金色（クリア済み）
        else:
            name_color = self.colors["text_normal"]  # 白色（未クリア）
        
        char_text = self.small_font.render(self.selected_chara['name'], True, name_color)
        char_text_x = icon_x + icon_size[0] + 15
        char_text_y = icon_y + 10
        self.screen.blit(char_text, (char_text_x, char_text_y))
        
        # クリア状態の表示
        if is_cleared:
            clear_text = self.description_font.render("♥CLEARED♥", True, self.colors["text_cleared"])
            clear_text_x = char_text_x
            clear_text_y = char_text_y + 30
            self.screen.blit(clear_text, (clear_text_x, clear_text_y))
        else:
            status_text = self.description_font.render("未クリア", True, self.colors["text_disabled"])
            status_text_x = char_text_x
            status_text_y = char_text_y + 30
            self.screen.blit(status_text, (status_text_x, status_text_y))
        
        # ステージ数の表示
        try:
            stage_data = self.save_manager.load_stage_data(self.selected_chara["folder"])
            stage_count_text = self.description_font.render(f"{len(stage_data)}ステージ", True, self.colors["text_normal"])
            stage_count_x = char_text_x
            stage_count_y = char_text_y + 55
            self.screen.blit(stage_count_text, (stage_count_x, stage_count_y))
        except:
            # ステージデータが読み込めない場合はスキップ
            pass

        # キャラクターの説明の表示（仮）
        description_text = self.selected_chara.get("description", "このキャラクターの説明はありません。")
        description_lines = description_text.split('\n')
        description_count_x = char_text_x
        description_count_y = char_text_y + 90
        
        # 各行を個別に描画
        for i, line in enumerate(description_lines):
            description_count_text = self.description_font.render(line, True, self.colors["text_normal"])
            line_y = description_count_y + i * 20
            self.screen.blit(description_count_text, (description_count_x, line_y))

        
        # 難易度ボタン
        for i, button in enumerate(self.difficulty_buttons):
            # ボタンの色を決定
            if self.selected_item_type == "difficulty" and i == self.selected_difficulty_index:
                button_color = self.colors["button_selected"]  # 選択時は青
                text_color = self.colors["text_normal"]
            else:
                button_color = self.colors["button_normal"]  # 通常時は暗い色
                text_color = self.colors["text_disabled"]
            
            # ボタンを描画
            pygame.draw.rect(self.screen, button_color, button['rect'])
            pygame.draw.rect(self.screen, self.colors["text_normal"], button['rect'], 2)
            
            # ボタンテキストを描画
            text_surface = self.small_font.render(button['name'], True, text_color)
            text_rect = text_surface.get_rect(center=button['rect'].center)
            self.screen.blit(text_surface, text_rect)
        
        # 戻る/終了ボタン
        back_label = "終了" if self.back_button_mode == "quit" else "戻る"
        back_color = self.colors["button_selected"] if self.selected_item_type == "back" else self.colors["button_normal"]
        text_color = self.colors["text_normal"] if self.selected_item_type == "back" else self.colors["text_disabled"]
        
        pygame.draw.rect(self.screen, back_color, self.back_button_rect)
        pygame.draw.rect(self.screen, self.colors["text_normal"], self.back_button_rect, 2)
        
        back_text = self.small_font.render(back_label, True, text_color)
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_text, back_text_rect)
        
        # 説明文の表示（現在選択されている難易度の説明を常に表示）
        if self.selected_item_type == "difficulty" and self.difficulty_keys:
            # 現在選択されている難易度の説明を取得
            selected_key = self.difficulty_keys[self.selected_difficulty_index]
            current_description = self.difficulties[selected_key]['description']
            
            # 説明文の背景（難易度ボタンの下に配置）
            desc_bg_rect = pygame.Rect(50, 640, SCREEN_WIDTH - 100, 80)
            pygame.draw.rect(self.screen, (40, 40, 60), desc_bg_rect)
            pygame.draw.rect(self.screen, self.colors["text_normal"], desc_bg_rect, 2)
            
            # 説明文を複数行に分割して表示
            words = current_description.split()
            lines = []
            current_line = ""
            max_width = desc_bg_rect.width - 20
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                text_width = self.description_font.size(test_line)[0]
                if text_width > max_width and current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            
            if current_line:
                lines.append(current_line)
            
            # 各行を描画
            for i, line in enumerate(lines):
                line_surface = self.description_font.render(line, True, self.colors["text_normal"])
                line_y = desc_bg_rect.y + 10 + i * 20
                self.screen.blit(line_surface, (desc_bg_rect.x + 10, line_y))
        
        # 操作説明
        self.draw_help_text()
        
        pygame.display.flip()
    
    def run(self):
        """難易度選択画面のメインループ"""
        while True:
            result = self.handle_events()
            if result is not None:
                return result
            
            self.draw()
            self.clock.tick(60)

def select_difficulty(selected_chara):
    """難易度選択画面を表示"""
    difficulty_select = DifficultySelect(selected_chara)
    return difficulty_select.run()
