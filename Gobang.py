#!/usr/bin/env python3
"""
五子棋 (15x15)
- 支持本地双人对战 和 人机对战（可选先后手）
- 棋盘大小 15x15，行列编号均为三位数字（001..015）
- 每下一子都会打印棋盘，并在上方编号上方用下箭头 ▼ 指示最新落子，在左侧对应行的左边显示 ▶。
- 使用栈实现悔棋（人机对战的悔棋相当于一次性悔两步）
- AI 难度:
  - 简单: 基础模式识别，不会纯随机落子
  - 中等: 模式评分 + 威胁检测
  - 困难: 全面模式评分 + 双重威胁检测 + 防守反击

运行: python3 Gobang.py
"""

import sys
import random

SIZE = 15
EMPTY = '.'
BLACK = '●'  # player 1
WHITE = '○'  # player 2 / AI

# 模式评分
SCORES = {
    'five':      1000000,
    'open_four':  100000,
    'rush_four':   10000,
    'open_three':   5000,
    'rush_three':   1000,
    'open_two':      200,
    'rush_two':       50,
    'one':             5,
}


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
        if not self.inside(r, c) or self.board[r][c] != EMPTY:
            return False
        self.board[r][c] = stone
        self.stack.append((r, c, stone))
        self.last_move = (r, c, stone)
        self.current = WHITE if stone == BLACK else BLACK
        return True

    def undo(self, steps=1):
        if steps <= 0:
            return
        for _ in range(steps):
            if not self.stack:
                break
            r, c, stone = self.stack.pop()
            self.board[r][c] = EMPTY
        self.last_move = self.stack[-1] if self.stack else None
        self.current = BLACK if (not self.stack or self.stack[-1][2] == WHITE) else WHITE

    def check_win(self, r, c, stone):
        dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in dirs:
            cnt = 1
            for s in (1, -1):
                nr, nc = r, c
                while True:
                    nr += dr * s
                    nc += dc * s
                    if not self.inside(nr, nc) or self.board[nr][nc] != stone:
                        break
                    cnt += 1
            if cnt >= 5:
                return True
        return False

    def is_draw(self):
        return len(self.stack) >= SIZE * SIZE

    def _candidate_moves(self):
        """只考虑已有棋子周围2格内的空位，避免扫描全盘"""
        moves = set()
        has_stone = False
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] != EMPTY:
                    has_stone = True
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            nr, nc = r + dr, c + dc
                            if self.inside(nr, nc) and self.board[nr][nc] == EMPTY:
                                moves.add((nr, nc))
        if not moves:
            return [(SIZE // 2, SIZE // 2)]
        return list(moves)

    def available_moves(self):
        moves = []
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] == EMPTY:
                    moves.append((r, c))
        return moves

    def _line_score(self, line, stone):
        """评估一条线上某种棋子的威胁程度。
        line: 5个元素的列表，元素为 stone / opp / EMPTY / OUT_OF_BOUNDS
        返回 (attacker_score, defender_score)
        """
        opp = WHITE if stone == BLACK else BLACK
        cnt = 0
        gaps = 0
        open_ends = 0
        segments = []

        # 统计连续棋子和间隔
        for i, cell in enumerate(line):
            if cell == stone:
                cnt += 1
            elif cell == EMPTY:
                if cnt > 0:
                    segments.append(('piece', cnt))
                    cnt = 0
                gaps += 1
            else:
                if cnt > 0:
                    segments.append(('piece', cnt))
                    cnt = 0
                segments.append(('block', 0))
        if cnt > 0:
            segments.append(('piece', cnt))

        # 简化分析: 找到 stone 的连续段
        # 重新解析，只关注连续段
        runs = []
        current_run = 0
        for cell in line:
            if cell == stone:
                current_run += 1
            else:
                if current_run > 0:
                    runs.append(current_run)
                current_run = 0
                if cell == EMPTY:
                    runs.append(0)  # 空位分隔
        if current_run > 0:
            runs.append(current_run)

        # 合并空位分隔的连续段（允许一个间隔）
        score = 0
        i = 0
        while i < len(runs):
            if runs[i] > 0:
                run_len = runs[i]
                left_open = (i > 0 and runs[i - 1] == 0 and (i - 2 < 0 or runs[i - 2] == 0 or line[i - 2] != opp))
                right_open = (i + 1 < len(runs) and runs[i + 1] == 0 and
                              (i + 2 >= len(runs) or runs[i + 2] == 0 or line[i + 2] != opp))
                open_count = left_open + right_open

                if run_len >= 5:
                    return SCORES['five'], SCORES['five']
                elif run_len == 4:
                    if open_count == 2:
                        score += SCORES['open_four']
                    elif open_count == 1:
                        score += SCORES['rush_four']
                elif run_len == 3:
                    if open_count == 2:
                        score += SCORES['open_three']
                    elif open_count == 1:
                        score += SCORES['rush_three']
                elif run_len == 2:
                    if open_count == 2:
                        score += SCORES['open_two']
                    elif open_count == 1:
                        score += SCORES['rush_two']
                elif run_len == 1:
                    if open_count == 2:
                        score += SCORES['one']
            i += 1

        return score, 0

    def _evaluate_position(self, r, c, stone):
        """评估在 (r,c) 放置 stone 后，该位置的攻防分值"""
        dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]
        attack_score = 0
        defend_score = 0
        opp = WHITE if stone == BLACK else BLACK

        # 临时放置棋子
        self.board[r][c] = stone

        for dr, dc in dirs:
            # 提取这条线上的9格窗口（以 r,c 为中心，向两个方向各取4格）
            line = []
            for i in range(-4, 5):
                nr, nc = r + dr * i, c + dc * i
                if not self.inside(nr, nc):
                    line.append(opp)  # 边界视为对方棋子
                else:
                    line.append(self.board[nr][nc])

            # 攻击分: stone 在这条线上的威胁
            a_score, _ = self._line_score(line, stone)
            attack_score += a_score

            # 防守分: opp 在这条线上的威胁（我们放置 stone 后，opp 还剩多少威胁）
            d_score, _ = self._line_score(line, opp)
            defend_score += d_score

        # 恢复棋盘
        self.board[r][c] = EMPTY

        return attack_score, defend_score

    def _defend_position(self, r, c, ai_stone, opp):
        """额外评估: 在 (r,c) 放置 ai_stone 后，能否削弱 opp 的已有威胁。
        扫描 opp 在当前位置附近的所有棋型，给出防守分。"""
        if self.board[r][c] != EMPTY:
            return 0
        score = 0
        dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]

        # 先临时放置
        self.board[r][c] = ai_stone

        for dr, dc in dirs:
            # 沿线向两个方向找到 opp 的连续段
            for s in (1, -1):
                cnt = 0
                empty_before = False
                nr, nc = r, c
                for step in range(1, 5):
                    nr += dr * s
                    nc += dc * s
                    if not self.inside(nr, nc):
                        break
                    if self.board[nr][nc] == opp:
                        cnt += 1
                    elif self.board[nr][nc] == EMPTY:
                        empty_before = True
                        break
                    else:
                        break
                # opp 的连续段越长，防守分越高
                if cnt >= 4:
                    score += SCORES['five']
                elif cnt == 3:
                    score += SCORES['open_four'] if empty_before else SCORES['rush_four']
                elif cnt == 2:
                    score += SCORES['open_three'] if empty_before else SCORES['rush_three']
                elif cnt == 1:
                    score += SCORES['open_two'] if empty_before else SCORES['rush_two']

        self.board[r][c] = EMPTY
        return score

    def ai_move(self, difficulty='medium'):
        ai_stone = self.current
        opp = BLACK if ai_stone == WHITE else WHITE

        candidates = self._candidate_moves()
        if not candidates:
            return SIZE // 2, SIZE // 2

        # 所有难度都先检查必赢
        for r, c in candidates:
            self.board[r][c] = ai_stone
            if self.check_win(r, c, ai_stone):
                self.board[r][c] = EMPTY
                return r, c
            self.board[r][c] = EMPTY

        # 检查对手必赢: 收集所有对手能赢的位置
        opp_wins = []
        for r, c in candidates:
            self.board[r][c] = opp
            if self.check_win(r, c, opp):
                opp_wins.append((r, c))
            self.board[r][c] = EMPTY

        if len(opp_wins) == 1:
            # 对手只有一个必赢点，直接堵
            return opp_wins[0]
        elif len(opp_wins) >= 2:
            # 对手有两个以上必赢点（活四等），基本无解
            # 但仍尝试: 优先选择能同时堵两个的点（如果存在），否则堵第一个
            # 活四的情况：两个必赢点在同一条线上且相隔5格以内
            # 实际上活四无法同时堵住，只能堵一个
            return opp_wins[0]

        if difficulty == 'easy':
            return self._ai_easy(candidates, ai_stone, opp)
        elif difficulty == 'medium':
            return self._ai_medium(candidates, ai_stone, opp)
        else:
            return self._ai_hard(candidates, ai_stone, opp)

    def _ai_easy(self, candidates, ai_stone, opp):
        """简单模式: 基础评分 + 随机扰动，不会纯随机落子"""
        best = None
        best_score = -1e9

        for r, c in candidates:
            score = 0
            attack, defend = self._evaluate_position(r, c, ai_stone)
            score = attack * 0.4 + defend * 0.6  # 简单模式更偏防守

            # 加一点随机扰动 (±20%)，让简单 AI 不是完全确定性的
            score *= random.uniform(0.8, 1.2)

            # 基础距离分: 离已有棋子近一点
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if self.inside(nr, nc):
                        if self.board[nr][nc] == ai_stone:
                            score += 3
                        elif self.board[nr][nc] == opp:
                            score += 1

            if score > best_score:
                best_score = score
                best = (r, c)

        return best if best else random.choice(candidates)

    def _ai_medium(self, candidates, ai_stone, opp):
        """中等模式: 模式评分 + 双重威胁检测"""
        best = None
        best_score = -1e9

        for r, c in candidates:
            attack, defend = self._evaluate_position(r, c, ai_stone)
            extra_defend = self._defend_position(r, c, ai_stone, opp)
            score = attack * 1.2 + defend * 0.7 + extra_defend * 1.0

            # 双重威胁: 落子后同时产生两个活三或以上
            threat_count = 0
            self.board[r][c] = ai_stone
            for dr2, dc2 in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                line = []
                for i in range(-4, 5):
                    nr, nc = r + dr2 * i, c + dc2 * i
                    if not self.inside(nr, nc):
                        line.append(opp)
                    else:
                        line.append(self.board[nr][nc])
                a, _ = self._line_score(line, ai_stone)
                if a >= SCORES['open_three']:
                    threat_count += 1
            self.board[r][c] = EMPTY

            if threat_count >= 2:
                score += 50000  # 双重威胁加分

            # 中心偏好
            center = (SIZE - 1) / 2.0
            dist = abs(r - center) + abs(c - center)
            score -= dist * 0.5

            if score > best_score:
                best_score = score
                best = (r, c)

        return best if best else random.choice(candidates)

    def _ai_hard(self, candidates, ai_stone, opp):
        """困难模式: 精准攻防评分 + 多重威胁检测"""
        scored_moves = []

        for r, c in candidates:
            attack, defend = self._evaluate_position(r, c, ai_stone)
            extra_defend = self._defend_position(r, c, ai_stone, opp)
            score = attack * 1.2 + defend * 0.9 + extra_defend * 1.2

            # 双重威胁检测: 落子后产生多少个方向的威胁
            threat_count = 0
            self.board[r][c] = ai_stone
            for dr2, dc2 in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                line = []
                for i in range(-4, 5):
                    nr, nc = r + dr2 * i, c + dc2 * i
                    if not self.inside(nr, nc):
                        line.append(opp)
                    else:
                        line.append(self.board[nr][nc])
                a, _ = self._line_score(line, ai_stone)
                if a >= SCORES['open_three']:
                    threat_count += 1
            self.board[r][c] = EMPTY

            if threat_count >= 3:
                score += 120000
            elif threat_count >= 2:
                score += 80000

            # 中心偏好
            center = (SIZE - 1) / 2.0
            dist = abs(r - center) + abs(c - center)
            score -= dist * 0.3

            scored_moves.append((score, r, c))

        if scored_moves:
            scored_moves.sort(reverse=True)
            return scored_moves[0][1], scored_moves[0][2]
        return random.choice(candidates)

    def print_board(self):
        cell_width = 3
        cell_height = 2
        row_label_width = 3
        col_nums = [f"{i + 1:03d}" for i in range(SIZE)]
        arrow_top = [' ' * cell_width for _ in range(SIZE)]
        if self.last_move:
            _, lc, _ = self.last_move
            arrow_top[lc] = '▼'.center(cell_width)
        left_pad = ' ' * (cell_width + 1 + row_label_width + 1)
        print(left_pad + ' '.join(arrow_top))
        print(left_pad + ' '.join(num.center(cell_width) for num in col_nums))
        for r in range(SIZE):
            left_arrow_area = ' ' * cell_width
            if self.last_move and self.last_move[0] == r:
                left_arrow_area = '▶'.center(cell_width)
            row_num = f"{r + 1:03d}"
            row_cells = ' '.join(self.board[r][c].center(cell_width) for c in range(SIZE))
            print(f"{left_arrow_area} {row_num} {row_cells}")
            for _ in range(cell_height - 1):
                print(' ' * cell_width + ' ' + ' ' * row_label_width + ' ' + ' '.join(
                    ' '.center(cell_width) for _ in range(SIZE)))
        print()


def parse_move(text):
    parts = text.strip().split()
    if len(parts) != 2:
        return None
    try:
        r = int(parts[0]) - 1
        c = int(parts[1]) - 1
        return (r, c)
    except ValueError:
        return None


def prompt_mode():
    print('请选择模式:')
    print('1. 双人对战')
    print('2. 人机对战')
    while True:
        c = input('输入 1 或 2: \n').strip()
        if c == '1':
            return 'pvp'
        if c == '2':
            return 'pve'
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
                human_is_black = True
                break
            if c == '2':
                human_is_black = False
                break
            print('无效输入')
        print('选择 AI 难度:')
        print('1. 简单')
        print('2. 中等')
        print('3. 困难')
        while True:
            d = input('输入 1/2/3: \n').strip()
            if d == '1':
                difficulty = 'easy'
                break
            if d == '2':
                difficulty = 'medium'
                break
            if d == '3':
                difficulty = 'hard'
                break
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
            r, c = mv
            if not game.place(r, c, game.current):
                print('无法下子：位置无效或已被占用')
                continue
            print(f'刚刚执{player} 在 {r + 1:03d} {c + 1:03d} 下子')
            if game.check_win(r, c, game.board[r][c]):
                game.print_board()
                winner = '白(○)' if game.board[r][c] == WHITE else '黑(●)'
                print('游戏结束，获胜者:', winner)
                break
            if game.is_draw():
                game.print_board()
                print('游戏结束，平局！')
                break
        else:
            human_turn = ((game.current == BLACK and game.human_is_black) or
                          (game.current == WHITE and not game.human_is_black))
            if human_turn:
                player = '你(黑●)' if game.current == BLACK else '你(白○)'
                display = '黑(●)' if game.current == BLACK else '白(○)'
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
                r, c = mv
                if not game.place(r, c, game.current):
                    print('无法下子：位置无效或已被占用')
                    continue
                display_player = '黑(●)' if game.board[r][c] == BLACK else '白(○)'
                print(f'刚刚执{display_player} 在 {r + 1:03d} {c + 1:03d} 下子')
                if game.check_win(r, c, game.board[r][c]):
                    game.print_board()
                    winner = '你' if game.board[r][c] == (BLACK if game.human_is_black else WHITE) else '电脑'
                    print('游戏结束，获胜者:', winner)
                    break
                if game.is_draw():
                    game.print_board()
                    print('游戏结束，平局！')
                    break
            else:
                display = '黑(●)' if game.current == BLACK else '白(○)'
                print(f"执{display}...")
                print('电脑思考中...')
                r, c = game.ai_move(difficulty)
                game.place(r, c, game.current)
                display_player = '黑(●)' if game.board[r][c] == BLACK else '白(○)'
                print(f'刚刚执{display_player} 在 {r + 1:03d} {c + 1:03d} 下子')
                if game.check_win(r, c, game.board[r][c]):
                    game.print_board()
                    winner = '电脑'
                    print('游戏结束，获胜者:', winner)
                    break
                if game.is_draw():
                    game.print_board()
                    print('游戏结束，平局！')
                    break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n中断，退出')
