import pygame
import json
import os
from constants.constants import *
from save_manager import SaveManager

class BaseSelector:
    """選択画面の基底クラス"""
    
    def __init__(self, title="選択画面", subtitle=""):
        """基底選択画面を初期化"""
        self.screen = pygame.display.get_surface()
        if self.screen is None:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        
        # タイトルとサブタイトル
        self.title = title
        self.subtitle = subtitle
        
        # フォントの設定
        try:
            self.font = pygame.font.Font("PixelMplus12-Regular.ttf", 32)
            self.small_font = pygame.font.Font("PixelMplus12-Regular.ttf", 24)
            self.tiny_font = pygame.font.Font("PixelMplus12-Regular.ttf", 18)
            self.description_font = pygame.font.Font("PixelMplus12-Regular.ttf", 18)
        except (pygame.error, FileNotFoundError):
            self.font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 24)
            self.tiny_font = pygame.font.Font(None, 18)
            self.description_font = pygame.font.Font(None, 18)
        
        # セーブデータ管理クラスの初期化
        self.save_manager = SaveManager()
        
        # 共通の背景設定
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background.fill((20, 20, 40))  # 統一された背景色
        
        # ページネーション設定
        self.chars_per_page = 6  # 1ページあたりのキャラクター数
        self.current_page = 0
        self.total_pages = 1
        
        # ボタン配置の標準設定
        self.button_positions = {
            "back": {"x": 50, "y": SCREEN_HEIGHT - 90, "width": 150, "height": 50},
            "center": {"x": (SCREEN_WIDTH - 150) // 2, "y": SCREEN_HEIGHT - 90, "width": 150, "height": 50},
            "right": {"x": SCREEN_WIDTH - 200, "y": SCREEN_HEIGHT - 90, "width": 150, "height": 50},
            "page_prev": {"x": (SCREEN_WIDTH // 2) - 120, "y": SCREEN_HEIGHT - 90, "width": 60, "height": 50},
            "page_next": {"x": (SCREEN_WIDTH // 2) + 60, "y": SCREEN_HEIGHT - 90, "width": 60, "height": 50}
        }
        
        # 標準の配色設定
        self.colors = {
            "background": (20, 20, 40),
            "button_normal": (60, 80, 120),
            "button_selected": (100, 150, 255),
            "button_disabled": (60, 60, 60),
            "button_special": (150, 100, 200),  # 特別なボタン（紫系）
            "text_normal": WHITE,
            "text_disabled": (150, 150, 150),
            "text_cleared": (255, 215, 0),  # 金色
            "border_normal": (150, 150, 150),
            "border_selected": WHITE,
            "border_disabled": (100, 100, 100)
        }
        
        # 共通ボタンの管理
        self.buttons = {}
        self.selected_item_type = ""
        self.selected_index = 0
        
        # 確認ダイアログの管理
        self.show_confirm_dialog = False
        self.confirm_title = ""
        self.confirm_message = ""
        self.confirm_selected = "no"
        self.confirm_callback = None
    
    def add_button(self, button_id, rect, text="", callback=None, enabled=True, style="normal"):
        """ボタンを追加"""
        self.buttons[button_id] = {
            "rect": rect,
            "text": text,
            "callback": callback,
            "enabled": enabled,
            "style": style  # "normal", "selected", "disabled", "special"
        }
    
    def create_standard_button(self, position_key, text, callback=None, enabled=True):
        """標準位置にボタンを作成"""
        pos = self.button_positions[position_key]
        rect = pygame.Rect(pos["x"], pos["y"], pos["width"], pos["height"])
        return {"rect": rect, "text": text, "callback": callback, "enabled": enabled}
    
    def draw_title(self, y_offset=32):
        """タイトルを描画"""
        title_text = self.font.render(self.title, True, self.colors["text_normal"])
        title_rect = title_text.get_rect()
        title_x = (SCREEN_WIDTH - title_rect.width) // 2
        self.screen.blit(title_text, (title_x, y_offset))
        
        if self.subtitle:
            subtitle_text = self.small_font.render(self.subtitle, True, self.colors["text_disabled"])
            subtitle_rect = subtitle_text.get_rect()
            subtitle_x = (SCREEN_WIDTH - subtitle_rect.width) // 2
            self.screen.blit(subtitle_text, (subtitle_x, y_offset + 40))
    
    def draw_button(self, button_id, is_selected=False):
        """ボタンを描画"""
        if button_id not in self.buttons:
            return
            
        button = self.buttons[button_id]
        rect = button["rect"]
        
        # ボタンの状態に応じた色を決定
        if not button["enabled"]:
            button_color = self.colors["button_disabled"]
            text_color = self.colors["text_disabled"]
            border_color = self.colors["border_disabled"]
            border_width = 1
        elif is_selected:
            if button["style"] == "special":
                button_color = self.colors["button_special"]
            else:
                button_color = self.colors["button_selected"]
            text_color = self.colors["text_normal"]
            border_color = self.colors["border_selected"]
            border_width = 3
        else:
            if button["style"] == "special":
                button_color = (80, 60, 120)  # 暗い紫
            else:
                button_color = self.colors["button_normal"]
            text_color = self.colors["text_normal"]
            border_color = self.colors["border_normal"]
            border_width = 2
        
        # ボタンを描画
        pygame.draw.rect(self.screen, button_color, rect)
        pygame.draw.rect(self.screen, border_color, rect, border_width)
        
        # テキストを描画
        if button["text"]:
            text_surface = self.small_font.render(button["text"], True, text_color)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def draw_character_icon(self, chara, rect, is_cleared=False, is_selected=False, is_enabled=True, icon_display=(None, None)):
        """キャラクターアイコンを描画（共通処理）"""
        # アイコンサイズを計算
        icon_size = (160, 200)
        if icon_display[0] is not None:
            icon_x = icon_display[0]
        else: 
            icon_x = rect.x + (rect.width - icon_size[0]) // 2
        if icon_display[1] is not None:
            icon_y = icon_display[1]
        else:
            icon_y = rect.y + 25
        
        try:
            # クリア済みの場合はicon_clear.pngを優先、なければicon.pngを使用
            if is_cleared:
                clear_icon_path = f"{chara['folder']}/icon_clear.png"
                if os.path.exists(clear_icon_path):
                    icon_path = clear_icon_path
                else:
                    icon_path = f"{chara['folder']}/icon.png"
            else:
                icon_path = f"{chara['folder']}/icon.png"
            
            # アイコン画像があれば表示
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                icon = pygame.transform.scale(icon, icon_size)
                self.screen.blit(icon, (icon_x, icon_y))
            else:
                # アイコンがない場合はプレースホルダー
                placeholder_rect = pygame.Rect(icon_x, icon_y, icon_size[0], icon_size[1])
                pygame.draw.rect(self.screen, (40, 40, 40), placeholder_rect)
                pygame.draw.rect(self.screen, self.colors["border_normal"], placeholder_rect, 1)
                
                # "No Image"テキスト
                no_image_text = self.tiny_font.render("No Image", True, self.colors["text_disabled"])
                no_image_rect = no_image_text.get_rect(center=placeholder_rect.center)
                self.screen.blit(no_image_text, no_image_rect)
        except (pygame.error, FileNotFoundError):
            # 画像読み込みエラーの場合はプレースホルダー
            placeholder_rect = pygame.Rect(icon_x, icon_y, icon_size[0], icon_size[1])
            pygame.draw.rect(self.screen, (40, 40, 40), placeholder_rect)
            pygame.draw.rect(self.screen, self.colors["border_normal"], placeholder_rect, 1)
        
        # 選択不可の場合は半透明オーバーレイ
        if not is_enabled:
            overlay = pygame.Surface((rect.width, rect.height))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, rect.topleft)
    
    def draw_character_name_and_status(self, chara, rect, is_cleared=False, is_enabled=True):
        """キャラクター名と状態を描画"""
        # キャラクター名（状態で色を変える）
        if is_cleared:
            name_color = self.colors["text_cleared"]  # 金色（クリア済み）
        elif is_enabled:
            name_color = self.colors["text_normal"]  # 白色
        else:
            name_color = self.colors["text_disabled"]  # グレー（選択不可）
        
        name_text = self.small_font.render(chara["name"], True, name_color)
        name_rect = name_text.get_rect()
        name_x = rect.centerx - name_rect.width // 2
        name_y = rect.bottom - 75
        self.screen.blit(name_text, (name_x, name_y))
        
        # 状態表示
        if is_cleared:
            status_text = self.tiny_font.render("♥CLEARED♥", True, self.colors["text_cleared"])
            status_rect = status_text.get_rect()
            status_x = rect.centerx - status_rect.width // 2
            status_y = rect.bottom - 30
            self.screen.blit(status_text, (status_x, status_y))
        elif not is_enabled:
            status_text = self.tiny_font.render("ロック中", True, self.colors["text_disabled"])
            status_rect = status_text.get_rect()
            status_x = rect.centerx - status_rect.width // 2
            status_y = rect.bottom - 30
            self.screen.blit(status_text, (status_x, status_y))
        else:
            status_text = self.tiny_font.render("未クリア", True, self.colors["text_disabled"])
            status_rect = status_text.get_rect()
            status_x = rect.centerx - status_rect.width // 2
            status_y = rect.bottom - 30
            self.screen.blit(status_text, (status_x, status_y))
    
    def show_confirmation_dialog(self, title, message, callback):
        """確認ダイアログを表示"""
        self.show_confirm_dialog = True
        self.confirm_title = title
        self.confirm_message = message
        self.confirm_callback = callback
        self.confirm_selected = "no"
    
    def draw_confirmation_dialog(self):
        """確認ダイアログを描画"""
        if not self.show_confirm_dialog:
            return
        
        # 背景の半透明オーバーレイ
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # ダイアログボックス
        dialog_width = 400
        dialog_height = 200
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        pygame.draw.rect(self.screen, (40, 40, 60), dialog_rect)
        pygame.draw.rect(self.screen, WHITE, dialog_rect, 3)
        
        # タイトル
        title_text = self.small_font.render(self.confirm_title, True, WHITE)
        title_rect = title_text.get_rect()
        title_x = dialog_x + (dialog_width - title_rect.width) // 2
        title_y = dialog_y + 20
        self.screen.blit(title_text, (title_x, title_y))
        
        # メッセージ
        message_lines = self.confirm_message.split('\n')
        for i, line in enumerate(message_lines):
            message_text = self.tiny_font.render(line, True, WHITE)
            message_rect = message_text.get_rect()
            message_x = dialog_x + (dialog_width - message_rect.width) // 2
            message_y = dialog_y + 60 + i * 25
            self.screen.blit(message_text, (message_x, message_y))
        
        # ボタン
        button_width = 100
        button_height = 40
        button_y = dialog_y + dialog_height - 60
        
        yes_rect = pygame.Rect(dialog_x + 80, button_y, button_width, button_height)
        no_rect = pygame.Rect(dialog_x + 220, button_y, button_width, button_height)
        
        # はいボタン
        yes_color = self.colors["button_selected"] if self.confirm_selected == "yes" else self.colors["button_normal"]
        yes_border = self.colors["border_selected"] if self.confirm_selected == "yes" else self.colors["border_normal"]
        yes_border_width = 3 if self.confirm_selected == "yes" else 2
        
        pygame.draw.rect(self.screen, yes_color, yes_rect)
        pygame.draw.rect(self.screen, yes_border, yes_rect, yes_border_width)
        yes_text = self.small_font.render("はい", True, WHITE)
        yes_text_rect = yes_text.get_rect(center=yes_rect.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # いいえボタン
        no_color = self.colors["button_selected"] if self.confirm_selected == "no" else self.colors["button_normal"]
        no_border = self.colors["border_selected"] if self.confirm_selected == "no" else self.colors["border_normal"]
        no_border_width = 3 if self.confirm_selected == "no" else 2
        
        pygame.draw.rect(self.screen, no_color, no_rect)
        pygame.draw.rect(self.screen, no_border, no_rect, no_border_width)
        no_text = self.small_font.render("いいえ", True, WHITE)
        no_text_rect = no_text.get_rect(center=no_rect.center)
        self.screen.blit(no_text, no_text_rect)
        
        # 確認ダイアログのボタン矩形を保存
        self.confirm_yes_rect = yes_rect
        self.confirm_no_rect = no_rect
    
    def handle_confirmation_dialog_events(self, event):
        """確認ダイアログのイベント処理"""
        if not self.show_confirm_dialog:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_confirm_dialog = False
                self.confirm_selected = "no"
                return True
            elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                self.confirm_selected = "yes" if self.confirm_selected == "no" else "no"
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.confirm_selected == "yes" and self.confirm_callback:
                    self.confirm_callback()
                self.show_confirm_dialog = False
                self.confirm_selected = "no"
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左クリック
                mouse_pos = pygame.mouse.get_pos()
                if hasattr(self, 'confirm_yes_rect') and self.confirm_yes_rect.collidepoint(mouse_pos):
                    if self.confirm_callback:
                        self.confirm_callback()
                    self.show_confirm_dialog = False
                    self.confirm_selected = "no"
                    return True
                elif hasattr(self, 'confirm_no_rect') and self.confirm_no_rect.collidepoint(mouse_pos):
                    self.show_confirm_dialog = False
                    self.confirm_selected = "no"
                    return True
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            if hasattr(self, 'confirm_yes_rect') and self.confirm_yes_rect.collidepoint(mouse_pos):
                self.confirm_selected = "yes"
                return True
            elif hasattr(self, 'confirm_no_rect') and self.confirm_no_rect.collidepoint(mouse_pos):
                self.confirm_selected = "no"
                return True
        
        return False
    
    def draw_help_text(self, text="矢印キー: 選択  Enter/Space: 決定  ESC: 戻る"):
        """操作説明テキストを描画"""
        help_text_surface = self.tiny_font.render(text, True, self.colors["text_disabled"])
        help_rect = help_text_surface.get_rect()
        help_x = (SCREEN_WIDTH - help_rect.width) // 2
        self.screen.blit(help_text_surface, (help_x, SCREEN_HEIGHT - 30))
    
    def setup_pagination(self, total_items):
        """ページネーションを設定"""
        self.total_pages = max(1, (total_items + self.chars_per_page - 1) // self.chars_per_page)
        self.current_page = 0
        
    def get_current_page_items(self, items):
        """現在のページのアイテムを取得"""
        start_index = self.current_page * self.chars_per_page
        end_index = min(start_index + self.chars_per_page, len(items))
        return items[start_index:end_index]
    
    def can_go_prev_page(self):
        """前のページに移動可能か判定"""
        return self.current_page > 0
    
    def can_go_next_page(self):
        """次のページに移動可能か判定"""
        return self.current_page < self.total_pages - 1
    
    def go_prev_page(self):
        """前のページに移動"""
        if self.can_go_prev_page():
            self.current_page -= 1
            return True
        return False
    
    def go_next_page(self):
        """次のページに移動"""
        if self.can_go_next_page():
            self.current_page += 1
            return True
        return False
    
    def draw_page_buttons(self, selected_item_type=""):
        """ページ切り替えボタンを描画"""
        if self.total_pages <= 1:
            return
        
        # 前のページボタン
        prev_pos = self.button_positions["page_prev"]
        prev_rect = pygame.Rect(prev_pos["x"], prev_pos["y"], prev_pos["width"], prev_pos["height"])
        
        prev_enabled = self.can_go_prev_page()
        if selected_item_type == "page_prev":
            prev_color = self.colors["button_selected"] if prev_enabled else self.colors["button_disabled"]
            prev_border = self.colors["border_selected"]
            prev_border_width = 3
        else:
            prev_color = self.colors["button_normal"] if prev_enabled else self.colors["button_disabled"]
            prev_border = self.colors["border_normal"] if prev_enabled else self.colors["border_disabled"]
            prev_border_width = 2
        
        pygame.draw.rect(self.screen, prev_color, prev_rect)
        pygame.draw.rect(self.screen, prev_border, prev_rect, prev_border_width)
        
        prev_text_color = self.colors["text_normal"] if prev_enabled else self.colors["text_disabled"]
        prev_text = self.small_font.render("◀", True, prev_text_color)
        prev_text_rect = prev_text.get_rect(center=prev_rect.center)
        self.screen.blit(prev_text, prev_text_rect)
        
        # 次のページボタン
        next_pos = self.button_positions["page_next"]
        next_rect = pygame.Rect(next_pos["x"], next_pos["y"], next_pos["width"], next_pos["height"])
        
        next_enabled = self.can_go_next_page()
        if selected_item_type == "page_next":
            next_color = self.colors["button_selected"] if next_enabled else self.colors["button_disabled"]
            next_border = self.colors["border_selected"]
            next_border_width = 3
        else:
            next_color = self.colors["button_normal"] if next_enabled else self.colors["button_disabled"]
            next_border = self.colors["border_normal"] if next_enabled else self.colors["border_disabled"]
            next_border_width = 2
        
        pygame.draw.rect(self.screen, next_color, next_rect)
        pygame.draw.rect(self.screen, next_border, next_rect, next_border_width)
        
        next_text_color = self.colors["text_normal"] if next_enabled else self.colors["text_disabled"]
        next_text = self.small_font.render("▶", True, next_text_color)
        next_text_rect = next_text.get_rect(center=next_rect.center)
        self.screen.blit(next_text, next_text_rect)
        
        # ページ番号表示
        page_info_text = f"{self.current_page + 1}/{self.total_pages}"
        page_info_surface = self.tiny_font.render(page_info_text, True, self.colors["text_disabled"])
        page_info_rect = page_info_surface.get_rect()
        page_info_x = (prev_rect.right + next_rect.left) // 2 - page_info_rect.width // 2
        page_info_y = prev_rect.centery - page_info_rect.height // 2
        self.screen.blit(page_info_surface, (page_info_x, page_info_y))
        
        # ページボタンの矩形を保存
        self.page_prev_rect = prev_rect
        self.page_next_rect = next_rect
    
    def handle_page_button_click(self, mouse_pos):
        """ページボタンのクリック処理"""
        if self.total_pages <= 1:
            return None
        
        if hasattr(self, 'page_prev_rect') and self.page_prev_rect.collidepoint(mouse_pos):
            if self.can_go_prev_page():
                self.go_prev_page()
                return "page_prev"
        elif hasattr(self, 'page_next_rect') and self.page_next_rect.collidepoint(mouse_pos):
            if self.can_go_next_page():
                self.go_next_page()
                return "page_next"
        
        return None
    
    def handle_page_button_hover(self, mouse_pos):
        """ページボタンのホバー処理"""
        if self.total_pages <= 1:
            return None
        
        if hasattr(self, 'page_prev_rect') and self.page_prev_rect.collidepoint(mouse_pos):
            if self.can_go_prev_page():
                return "page_prev"
        elif hasattr(self, 'page_next_rect') and self.page_next_rect.collidepoint(mouse_pos):
            if self.can_go_next_page():
                return "page_next"
        
        return None
    
    def get_page_state_for_chara(self, target_chara):
        """指定されたキャラクターが表示されるページ状態を取得"""
        if not hasattr(self, 'unlocked_charas'):
            return None
            
        try:
            # キャラクターのインデックスを取得
            chara_index = None
            for i, chara in enumerate(self.unlocked_charas):
                if chara.get('folder') == target_chara.get('folder'):
                    chara_index = i
                    break
            
            if chara_index is None:
                return None
            
            # そのキャラクターがどのページにあるかを計算
            target_page = chara_index // self.chars_per_page
            page_chara_index = chara_index % self.chars_per_page
            
            return {
                "current_page": target_page,
                "selected_chara_index": page_chara_index,
                "selected_item_type": "chara"
            }
        except:
            return None
    
    def get_page_state(self):
        """現在のページ状態を取得"""
        return {
            "current_page": self.current_page,
            "selected_chara_index": getattr(self, 'selected_chara_index', 0),
            "selected_item_type": self.selected_item_type
        }
    
    def restore_page_state(self, page_state):
        """ページ状態を復元"""
        if page_state:
            self.current_page = page_state.get("current_page", 0)
            if hasattr(self, 'selected_chara_index'):
                self.selected_chara_index = page_state.get("selected_chara_index", 0)
            self.selected_item_type = page_state.get("selected_item_type", "chara")
            
            # ページが範囲外になっていないかチェック
            if self.current_page >= self.total_pages:
                self.current_page = max(0, self.total_pages - 1)
    
    def load_charas_data(self):
        """charas.jsonからキャラクターデータを読み込む（共通処理）"""
        try:
            with open("settings/charas.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["charas"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"charas.jsonの読み込みに失敗しました: {e}")
            raise SystemExit(f"必須ファイル charas.json の読み込みに失敗しました: {e}")
    
    def is_chara_unlocked(self, chara, charas_data):
        """キャラクターがアンロックされているかチェック（共通処理）"""
        # unlock項目がない場合は最初からアンロックされている
        if "unlock" not in chara:
            return True
        
        # unlock項目がある場合、指定されたキャラクターがすべてクリア済みかチェック
        required_charas = chara["unlock"]
        for required_chara_name in required_charas:
            # 必要なキャラクターを検索
            required_chara = None
            for g in charas_data:
                if g["name"] == required_chara_name:
                    required_chara = g
                    break
            
            if required_chara is None:
                # 必要なキャラクターが見つからない場合はロック
                return False
            
            # セーブデータをチェック
            save_info = self.save_manager.get_chara_data(required_chara["folder"])
            
            if save_info["clear"] != 1:
                # 1つでもクリアしていないキャラクターがあればロック
                return False
        
        # すべての必要なキャラクターをクリアしている場合はアンロック
        return True
    
    def is_chara_cleared(self, chara):
        """キャラクターがクリア済みかチェック（共通処理）"""
        save_info = self.save_manager.get_chara_data(chara["folder"])
        return save_info["clear"] == 1
    
    def run(self):
        """メインループ（サブクラスでオーバーライド）"""
        raise NotImplementedError("サブクラスでrunメソッドを実装してください")
    
    def handle_events(self):
        """イベント処理（サブクラスでオーバーライド）"""
        raise NotImplementedError("サブクラスでhandle_eventsメソッドを実装してください")
    
    def draw(self):
        """画面描画（サブクラスでオーバーライド）"""
        raise NotImplementedError("サブクラスでdrawメソッドを実装してください")
