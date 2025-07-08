import csv
import json
import os

class SaveManager:
    """セーブデータの読み込み・書き込みを管理するクラス"""
    
    def __init__(self):
        self.save_file_path = "save/save.dat"
        self.charas_file_path = "settings/charas.json"
        self.save_data = self.load_save_data()
    
    def load_save_data(self):
        """セーブデータを読み込む"""
        save_data = {}
        try:
            with open(self.save_file_path, "r", encoding="utf-8") as f:
                csv_reader = csv.reader(f)
                header = next(csv_reader)  # ヘッダー行をスキップ
                
                for i, row in enumerate(csv_reader):
                    if len(row) >= 8:  # 最低限のデータがある場合
                        chara_name = f"chara_{i}"  # インデックスでキャラクター名を識別
                        save_data[chara_name] = {
                            "clear": int(row[0]) if row[0] else 0,
                            "hi_score": int(row[1]) if row[1] else 0,
                            "bonus_flags": [int(row[j]) if row[j] else 0 for j in range(2, 8)]
                        }
                    else:
                        # データが不足している場合はデフォルト値
                        chara_name = f"chara_{i}"
                        save_data[chara_name] = {
                            "clear": 0,
                            "hi_score": 0,
                            "bonus_flags": [0, 0, 0, 0, 0, 0]
                        }
        except (FileNotFoundError, csv.Error) as e:
            print(f"セーブデータの読み込みに失敗しました: {e}")
            # charas.jsonからキャラクター数を取得してデフォルトデータを作成
            try:
                charas_data = self.load_charas_data()
                max_charas = len(charas_data)
            except:
                max_charas = 6  # フォールバック値
            
            # デフォルトのセーブデータを作成
            for i in range(max_charas):
                chara_name = f"chara_{i}"
                save_data[chara_name] = {
                    "clear": 0,
                    "hi_score": 0,
                    "bonus_flags": [0, 0, 0, 0, 0, 0]
                }
        
        return save_data
    
    def save_game_data(self):
        """ゲームデータをセーブファイルに書き込む"""
        try:
            # セーブディレクトリが存在しない場合は作成
            os.makedirs("save", exist_ok=True)
            
            # charas.jsonからキャラクター数を取得
            try:
                charas_data = self.load_charas_data()
                max_charas = len(charas_data)
            except:
                # charas.jsonが読み込めない場合は現在のsave_dataの数を使用
                max_charas = max(len(self.save_data), 6)
            
            with open(self.save_file_path, "w", encoding="utf-8", newline="") as f:
                csv_writer = csv.writer(f)
                
                # ヘッダー行を書き込み
                csv_writer.writerow(["Clear", "HiScore", "Bonus1", "Bonus2", "Bonus3", "Bonus4", "Bonus5", "Bonus6"])
                
                # 各キャラクターのデータを書き込み
                for i in range(max_charas):
                    chara_name = f"chara_{i}"
                    if chara_name in self.save_data:
                        data = self.save_data[chara_name]
                        row = [
                            data["clear"],
                            data["hi_score"],
                            *data["bonus_flags"]
                        ]
                    else:
                        # データが存在しない場合はデフォルト値
                        row = [0, 0, 0, 0, 0, 0, 0, 0]
                    csv_writer.writerow(row)
                
            print("セーブデータを保存しました")
        except Exception as e:
            print(f"セーブデータの保存に失敗しました: {e}")
    
    def get_chara_save_key(self, chara_folder):
        """キャラクターのフォルダ名からセーブデータキーを取得"""
        # charas.jsonから記述順を取得してマッピング
        try:
            with open(self.charas_file_path, "r", encoding="utf-8") as f:
                charas_data = json.load(f)
            
            # charas.jsonの記述順に基づいてインデックスを取得
            for i, chara in enumerate(charas_data["charas"]):
                if chara["folder"] == chara_folder:
                    return f"chara_{i}"
            
            # 見つからない場合はデフォルト
            print(f"警告: {chara_folder}がcharas.jsonに見つかりません。デフォルト値を使用します。")
            return "chara_0"
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"charas.jsonの読み込みに失敗しました: {e}")
            # フォールバック：従来のマッピング
            folder_mapping = {
                "sana": "chara_0",
                "ichika_1": "chara_1", 
                "test": "chara_2"
            }
            return folder_mapping.get(chara_folder, "chara_0")
    
    def get_chara_data(self, chara_folder):
        """指定されたキャラクターのセーブデータを取得"""
        chara_key = self.get_chara_save_key(chara_folder)
        
        if chara_key not in self.save_data:
            self.save_data[chara_key] = {
                "clear": 0,
                "hi_score": 0,
                "bonus_flags": [0, 0, 0, 0, 0, 0]
            }
        
        return self.save_data[chara_key]
    
    def update_chara_data(self, chara_folder, clear=None, hi_score=None, bonus_flags=None):
        """指定されたキャラクターのセーブデータを更新"""
        chara_key = self.get_chara_save_key(chara_folder)
        
        if chara_key not in self.save_data:
            self.save_data[chara_key] = {
                "clear": 0,
                "hi_score": 0,
                "bonus_flags": [0, 0, 0, 0, 0, 0]
            }
        
        # 指定された項目のみ更新
        if clear is not None:
            self.save_data[chara_key]["clear"] = clear
        
        if hi_score is not None:
            self.save_data[chara_key]["hi_score"] = hi_score
        
        if bonus_flags is not None:
            self.save_data[chara_key]["bonus_flags"] = bonus_flags[:]  # コピーを作成
        
        # セーブファイルに書き込み
        self.save_game_data()
    
    def update_bonus_flag(self, chara_folder, stage_number, flag_value):
        """指定されたキャラクターの特定ステージのボーナスフラグを更新"""
        chara_key = self.get_chara_save_key(chara_folder)
        
        if chara_key not in self.save_data:
            self.save_data[chara_key] = {
                "clear": 0,
                "hi_score": 0,
                "bonus_flags": [0, 0, 0, 0, 0, 0]
            }
        
        # ステージ番号からボーナスフラグのインデックスを計算（stage1=index0, stage2=index1...）
        bonus_index = stage_number - 1
        if 0 <= bonus_index < len(self.save_data[chara_key]["bonus_flags"]):
            self.save_data[chara_key]["bonus_flags"][bonus_index] = flag_value
            print(f"ステージ{stage_number}のボーナス画像フラグを更新しました: {flag_value}")
            
            # セーブファイルに書き込み
            self.save_game_data()
            return True
        
        return False
    
    def reload_save_data(self):
        """セーブデータを再読み込み"""
        self.save_data = self.load_save_data()
    
    def reset_all_save_data(self):
        """すべてのセーブデータを初期化"""
        try:
            # セーブディレクトリが存在しない場合は作成
            os.makedirs("save", exist_ok=True)
            
            # charas.jsonからキャラクター数を取得
            try:
                charas_data = self.load_charas_data()
                max_charas = len(charas_data)
            except:
                max_charas = 6  # フォールバック値
            
            # save.datファイルを初期化
            with open(self.save_file_path, "w", encoding="utf-8", newline="") as f:
                csv_writer = csv.writer(f)
                
                # ヘッダー行を書き込み
                csv_writer.writerow(["Clear", "HiScore", "Bonus1", "Bonus2", "Bonus3", "Bonus4", "Bonus5", "Bonus6"])
                
                # 各キャラクターのデータを0で初期化
                for i in range(max_charas):
                    csv_writer.writerow([0, 0, 0, 0, 0, 0, 0, 0])
            
            # メモリ上のセーブデータも初期化
            self.save_data = {}
            for i in range(max_charas):
                chara_name = f"chara_{i}"
                self.save_data[chara_name] = {
                    "clear": 0,
                    "hi_score": 0,
                    "bonus_flags": [0, 0, 0, 0, 0, 0]
                }
            
            print("セーブデータを初期化しました")
            return True
        except Exception as e:
            print(f"セーブデータの初期化に失敗しました: {e}")
            return False
    
    def load_charas_data(self):
        """charas.jsonからキャラクターデータを読み込む"""
        try:
            with open(self.charas_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["charas"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"charas.jsonの読み込みに失敗しました: {e}")
            raise SystemExit(f"必須ファイル charas.json の読み込みに失敗しました: {e}")
    
    def load_stage_data(self, chara_folder):
        """指定されたキャラクターのステージデータを読み込む"""
        try:
            stage_json_path = os.path.join(chara_folder, "stage.json")
            with open(stage_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["stages"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"{chara_folder}/stage.jsonの読み込みに失敗しました: {e}")
            raise SystemExit(f"必須ファイル {chara_folder}/stage.json の読み込みに失敗しました: {e}")
    
    def load_difficulty_data(self):
        """難易度データを読み込む"""
        try:
            with open("settings/game_difficulty.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["difficulties"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"難易度設定ファイルの読み込みに失敗しました: {e}")
            # デフォルト設定を返す
            return {
                "normal": {
                    "name": "Normal",
                    "description": "標準的な設定です。",
                    "score_adjustment": 1.0,
                    "balls": 3,
                    "initial_ball_speed": 8,
                    "max_ball_speed": 18,
                    "block_strength_adjustment": 0,
                    "items_enable": ["wide_paddle", "multi_ball", "slow_ball", "extra_life", "bonus_score", "power_ball", "paddle_shot"],
                    "get_bonus_image": True
                }
            }
    
    def is_chara_unlocked(self, chara, charas_data):
        """キャラクターがアンロックされているかチェック"""
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
            save_info = self.get_chara_data(required_chara["folder"])
            
            if save_info["clear"] != 1:
                # 1つでもクリアしていないキャラクターがあればロック
                return False
        
        # すべての必要なキャラクターをクリアしている場合はアンロック
        return True
    
    def check_and_extend_save_data(self, verbose=False):
        """save.datのレコード数をcharas.jsonのキャラクター数に合わせる"""
        try:
            charas_data = self.load_charas_data()
            charas_count = len(charas_data)
            
            # 現在のsave.datのレコード数を取得
            current_save_count = len(self.save_data)
            
            if verbose:
                print(f"charas.jsonのキャラクター数: {charas_count}")
                print(f"save.datの現在のレコード数: {current_save_count}")
            
            if charas_count > current_save_count:
                if verbose:
                    print(f"save.datのレコード数が不足しています。{charas_count - current_save_count}レコード追加します。")
                
                # 不足分のレコードを追加
                for i in range(current_save_count, charas_count):
                    chara_name = f"chara_{i}"
                    self.save_data[chara_name] = {
                        "clear": 0,
                        "hi_score": 0,
                        "bonus_flags": [0, 0, 0, 0, 0, 0]
                    }
                
                # save.datファイルを更新
                self.save_game_data()
                if verbose:
                    print("save.datを更新しました。")
                return True
            elif charas_count < current_save_count:
                if verbose:
                    print("save.datのレコード数の方が多いですが、削除は行いません。")
                return False
            else:
                if verbose:
                    print("save.datのレコード数は適切です。")
                return False
                
        except Exception as e:
            if verbose:
                print(f"save.datの拡張処理でエラーが発生しました: {e}")
            return False

if __name__ == "__main__":
    """save_manager.pyを単体で実行した際の処理"""
    print("=== SaveManager セーブデータ診断 ===")
    
    # SaveManagerのインスタンスを作成
    save_manager = SaveManager()
    
    # save.datとcharas.jsonの項目数をチェックして必要に応じて拡張（詳細出力有効）
    save_manager.check_and_extend_save_data(verbose=True)
    
    print("=== 診断完了 ===")
