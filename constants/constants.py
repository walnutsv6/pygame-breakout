# ゲーム定数管理ファイル

# 画面サイズ
SCREEN_WIDTH = 672
SCREEN_HEIGHT = 864
SAFE_AREA_HEIGHT = 64  # セーフエリアの高さ
GAME_AREA_Y = SAFE_AREA_HEIGHT  # ゲームエリアの開始Y座標

# パドル設定
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20

# ボール設定
BALL_SIZE = 16
BALL_SPEED_INITIAL = 8  # ボールの初期速度
BALL_SPEED_MAX = 18     # ボールの最大速度
BALL_SPEED_INCREMENT = 1  # 速度上昇値
BLOCKS_PER_SPEED_UP = 10  # 速度上昇に必要なブロック破壊数

# ブロック設定
BLOCK_SIZE = 32  # 32x32ピクセルの正方形ブロック

# アイテム関連定数
ITEM_SIZE = 24
ITEM_FALL_SPEED = 3
ITEM_SCORE_THRESHOLD = 200  # アイテム出現に必要なスコア

# 弾丸設定
BULLET_SIZE = 8
BULLET_SPEED = 12

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)

LIGHTGRAY = (200, 200, 200)
GRAY = (120, 120, 120)  # 戻るボタンの色
DARKGRAY = (80, 80, 80)  # 戻るボタンの非アクティブ色

