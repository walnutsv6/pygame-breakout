import pygame
from game_logics.game import Game
from select_logics.stageselect import select_chara
from select_logics.difficultyselect import select_difficulty
from gallery_logics.gallery import show_gallery

# 初期化
pygame.init()

def main():
    """メインゲームループ"""
    stage_select_state = None  # ステージ選択の状態を保持
    
    while True:
        # キャラクター選択
        selected_result = select_chara(stage_select_state)
        stage_select_state = None  # 一度使用したら状態をリセット
        
        if selected_result:
            if isinstance(selected_result, dict):
                # 通常のキャラクターが選択された場合は難易度選択画面を表示
                difficulty_result = select_difficulty(selected_result)
                
                if isinstance(difficulty_result, dict):
                    # 難易度が選択された場合はゲーム開始
                    game = Game(difficulty_result)
                    result = game.run()
                    
                    # ゲームからの戻り値をチェック
                    if result == "back_to_select":
                        # キャラクター選択画面に戻る（pygame再初期化なし）
                        continue
                    else:
                        # ゲーム終了
                        break
                elif difficulty_result == "back":
                    # 難易度選択から戻った場合は、選択していたキャラクターのページを復元
                    from select_logics.stageselect import StageSelect
                    temp_stage_select = StageSelect()
                    stage_select_state = temp_stage_select.get_page_state_for_chara(selected_result)
                    continue
                else:
                    # その他の場合は終了
                    break
            else:
                # 予期しない結果の場合は終了
                break
        else:
            # キャンセルされた場合は終了
            print("ゲームを終了します。")
            break
    
    pygame.quit()

# ゲームの実行
if __name__ == "__main__":
    main()