#!/usr/bin/env python3
"""
五子棋 (15x15)
- 支持本地双人对战 和 人机对战（可选先后手）
- 棋盘大小 15x15，行列编号均为三位数字（001..015）
- 每下一子都会打印棋盘，并在上方编号上方用下箭头 ▼ 指示最新落子，在左侧对应行的左边显示 ▶。
- 使用栈实现悔棋（人机对战的悔棋相当于一次性悔两步）
- 每次下棋时打印“执X棋...”，每一步都打印刚刚什么棋在哪下了；悔棋只打印“已悔棋”而不说明回退多少步

运行: python3 五子棋.py
"""

import sys
import random

SIZE = 15
EMPTY = '.'
BLACK = '●'  # player 1
WHITE = '○'  # player 2 / AI

class Game:
    def __init__(self, mode, human_is_black=True):
        self.board = [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]
        self.stack = []  # stack of moves: (r,c,player)
        self.last_move = None
        self.mode = mode  # 'pvp' or 'pve'
        self.human_is_black = human_is_black
        self.current = BLACK  # BLACK always starts

    def inside(self, r, c):
        return 0 <= r < SIZE and 0 <= c < SIZE

    def place(self, r, c, stone):
        if not self.inside(r,c) or self.board[r][c] != EMPTY:
            return False
        self.board[r][c] = stone
        self.stack.append((r,c,stone))
        self.last_move = (r,c,stone)
        self.current = WHITE if stone == BLACK else BLACK
        return True

    def undo(self, steps=1):
        if steps <= 0: return
        for _ in range(steps):
            if not self.stack: break
            r,c,stone = self.stack.pop()
            self.board[r][c] = EMPTY
        self.last_move = self.stack[-1] if self.stack else None
        self.current = BLACK if (not self.stack or self.stack[-1][2] == WHITE) else WHITE

    def check_win(self, r, c, stone):
        dirs = [(1,0),(0,1),(1,1),(1,-1)]
        for dr,dc in dirs:
            cnt = 1
            for s in (1, -1):
                nr, nc = r, c
                while True:
                    nr += dr*s; nc += dc*s
                    if not self.inside(nr,nc) or self.board[nr][nc] != stone:
                        break
                    cnt += 1
            if cnt >= 5:
                return True
        return False

    def available_moves(self):
        moves = []
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] == EMPTY:
                    moves.append((r,c))
        return moves

    def ai_move(self, difficulty='medium'):
        # difficulty: 'easy' (random), 'medium' (heuristic), 'hard' (heuristic + scoring)
        ai_stone = self.current
        opp = BLACK if ai_stone == WHITE else WHITE

        moves = self.available_moves()
        if difficulty == 'easy':
            return random.choice(moves)

        # medium & hard: try winning
        for r,c in moves:
            self.board[r][c] = ai_stone
            if self.check_win(r,c,ai_stone):
                self.board[r][c] = EMPTY
                return r,c
            self.board[r][c] = EMPTY
        # block opponent
        for r,c in moves:
            self.board[r][c] = opp
            if self.check_win(r,c,opp):
                self.board[r][c] = EMPTY
                return r,c
            self.board[r][c] = EMPTY

        if difficulty == 'medium':
            # choose random near existing stones
            candidates = []
            for r in range(SIZE):
                for c in range(SIZE):
                    if self.board[r][c] != EMPTY:
                        for dr in range(-2,3):
                            for dc in range(-2,3):
                                nr,nc = r+dr,c+dc
                                if self.inside(nr,nc) and self.board[nr][nc]==EMPTY:
                                    candidates.append((nr,nc))
            if candidates:
                return random.choice(candidates)
            return random.choice(moves)

        # hard: score moves
        best = None
        best_score = -1e9
        center_r = center_c = (SIZE-1)/2.0
        for r,c in moves:
            score = 0
            # proximity to existing same-color stones
            for dr in range(-2,3):
                for dc in range(-2,3):
                    nr, nc = r+dr, c+dc
                    if not self.inside(nr,nc): continue
                    if self.board[nr][nc] == ai_stone:
                        score += 10
                    elif self.board[nr][nc] == opp:
                        score += 5
            # center preference
            dist = abs(r-center_r) + abs(c-center_c)
            score -= dist * 0.1
            if score > best_score:
                best_score = score
                best = (r,c)
        if best:
            return best
        return random.choice(moves)

    def print_board(self):
        # Make cells square in monospace: use multiple text lines per cell
        # user-requested spacing: column cell width = 3 chars, row spacing = 2 lines
        cell_width = 3
        cell_height = 2
        row_label_width = 3
        col_nums = [f"{i+1:03d}" for i in range(SIZE)]
        # prepare top arrows centered in cell area
        arrow_top = [' ' * cell_width for _ in range(SIZE)]
        if self.last_move:
            _, lc, _ = self.last_move
            arrow_top[lc] = '▼'.center(cell_width)
        # compute left padding so column numbers are centered over cells and not directly above row numbers
        # left area = cell_width (left arrow area) + 1 (space) + row_label_width + 1 (space)
        left_pad = ' ' * (cell_width + 1 + row_label_width + 1)
        # print arrow row
        print(left_pad + ' '.join(arrow_top))
        # print column numbers centered under arrows (in the middle line of cell_height)
        print(left_pad + ' '.join(num.center(cell_width) for num in col_nums))
        # for each board row, print cell_height lines
        for r in range(SIZE):
            # print middle line first to avoid extra blank line between column numbers and first row
            left_arrow_area = ' ' * cell_width
            if self.last_move and self.last_move[0] == r:
                left_arrow_area = '▶'.center(cell_width)
            row_num = f"{r+1:03d}"
            row_cells = ' '.join(self.board[r][c].center(cell_width) for c in range(SIZE))
            print(f"{left_arrow_area} {row_num} {row_cells}")
            # then print remaining padding lines (if any) below the row to maintain cell_height
            for _ in range(cell_height - 1):
                print(' ' * cell_width + ' ' + ' ' * row_label_width + ' ' + ' '.join(' '.center(cell_width) for _ in range(SIZE)))
        print()

def parse_move(text):
    parts = text.strip().split()
    if len(parts) != 2: return None
    try:
        r = int(parts[0]) - 1
        c = int(parts[1]) - 1
        return (r,c)
    except:
        return None


def prompt_mode():
    print('请选择模式:')
    print('1. 双人对战')
    print('2. 人机对战')
    while True:
        c = input('输入 1 或 2: \n').strip()
        if c == '1': return 'pvp'
        if c == '2': return 'pve'
        print('无效输入')


def main():
    mode = prompt_mode()
    human_is_black = True
    difficulty = 'medium'
    if mode == 'pve':
        print('人机对战：选择先手或后手:')
        print('1. 先手 (黑)')
        print('2. 后手 (白)')
        while True:
            c = input('输入 1 或 2: \n').strip()
            if c == '1':
                human_is_black = True; break
            if c == '2':
                human_is_black = False; break
            print('无效输入')
        print('选择 AI 难度:')
        print('1. 简单')
        print('2. 中等')
        print('3. 困难')
        while True:
            d = input('输入 1/2/3: \n').strip()
            if d == '1':
                difficulty = 'easy'; break
            if d == '2':
                difficulty = 'medium'; break
            if d == '3':
                difficulty = 'hard'; break
            print('无效输入')
    game = Game(mode, human_is_black)

    while True:
        game.print_board()
        if mode == 'pvp':
            player = '黑(●)' if game.current == BLACK else '白(○)'
            print(f"执{player}...")
            cmd = input('输入 row col 下子，或 u 悔棋，q 退出: ').strip()
            if cmd.lower() == 'q':
                print('退出')
                break
            if cmd.lower() == 'u':
                game.undo(1)
                print('已悔棋')
                continue
            mv = parse_move(cmd)
            if not mv:
                print('无效输入，示例: 10 11')
                continue
            r,c = mv
            if not game.place(r,c,game.current):
                print('无法下子：位置无效或已被占用')
                continue
            print(f'刚刚执{player} 在 {r+1:03d} {c+1:03d} 下子')
            if game.check_win(r,c, game.board[r][c]):
                game.print_board()
                winner = '白(○)' if game.board[r][c]==WHITE else '黑(●)'
                print('游戏结束，获胜者:', winner)
                break
        else:
            human_turn = (game.current == BLACK and game.human_is_black) or (game.current == WHITE and not game.human_is_black)
            if human_turn:
                player = '你(黑●)' if game.current==BLACK else '你(白○)'
                display = '黑(●)' if game.current==BLACK else '白(○)'
                print(f"执{display}...")
                cmd = input('输入 row col 下子，或 u 悔棋，q 退出: ').strip()
                if cmd.lower() == 'q':
                    print('退出')
                    break
                if cmd.lower() == 'u':
                    game.undo(2)
                    print('已悔棋')
                    continue
                mv = parse_move(cmd)
                if not mv:
                    print('无效输入，示例: 10 11')
                    continue
                r,c = mv
                if not game.place(r,c,game.current):
                    print('无法下子：位置无效或已被占用')
                    continue
                display_player = '黑(●)' if game.board[r][c]==BLACK else '白(○)'
                print(f'刚刚执{display_player} 在 {r+1:03d} {c+1:03d} 下子')
                if game.check_win(r,c, game.board[r][c]):
                    game.print_board()
                    winner = '你' if game.board[r][c] == (BLACK if game.human_is_black else WHITE) else '电脑'
                    print('游戏结束，获胜者:', winner)
                    break
            else:
                display = '黑(●)' if game.current==BLACK else '白(○)'
                print(f"执{display}...")
                print('电脑思考中...')
                r,c = game.ai_move(difficulty)
                game.place(r,c,game.current)
                display_player = '黑(●)' if game.board[r][c]==BLACK else '白(○)'
                print(f'刚刚执{display_player} 在 {r+1:03d} {c+1:03d} 下子')
                if game.check_win(r,c, game.board[r][c]):
                    game.print_board()
                    winner = '电脑'
                    print('游戏结束，获胜者:', winner)
                    break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n中断，退出')
