import pygame
import sys
import copy
import math

# Colors and other constants
BACKGROUND = (244, 216, 185)
HUMAN_COLOR = (70, 119, 207)  # Darker blue for human store
COMPUTER_COLOR = (190, 0, 30)  # Darker red for computer store
SEED_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
TEXT_COLOR = (0, 0, 0)
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700

class MancalaBoard:
    def __init__(self):
        self.board = {
            'A': 4, 'B': 4, 'C': 4, 'D': 4, 'E': 4, 'F': 4,
            'G': 4, 'H': 4, 'I': 4, 'J': 4, 'K': 4, 'L': 4,
            1: 0, 2: 0
        }
        self.player1_pits = ('A', 'B', 'C', 'D', 'E', 'F')
        self.player2_pits = ('G', 'H', 'I', 'J', 'K', 'L')
        self.opposite_pits = {
            'A': 'L', 'B': 'K', 'C': 'J', 'D': 'I', 'E': 'H', 'F': 'G',
            'G': 'F', 'H': 'E', 'I': 'D', 'J': 'C', 'K': 'B', 'L': 'A'
        }
        self.next_pits = {
            'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'F', 'F': 1,
            1: 'G', 'G': 'H', 'H': 'I', 'I': 'J', 'J': 'K', 'K': 'L', 'L': 2,
            2: 'A'
        }

    def possibleMoves(self, player_pits):
        return [pit for pit in player_pits if self.board[pit] > 0]

    def doMove(self, player_pits, pit):
        seeds = self.board[pit]
        self.board[pit] = 0
        current_pit = pit
        while seeds > 0:
            current_pit = self.next_pits[current_pit]
            if current_pit == (2 if player_pits == self.player1_pits else 1):
                continue
            self.board[current_pit] += 1
            seeds -= 1

        if (current_pit in player_pits and self.board[current_pit] == 1 and 
            self.board[self.opposite_pits[current_pit]] > 0):
            store = 1 if player_pits == self.player1_pits else 2
            captured_seeds = self.board[current_pit] + self.board[self.opposite_pits[current_pit]]
            self.board[current_pit] = 0
            self.board[self.opposite_pits[current_pit]] = 0
            self.board[store] += captured_seeds
        return current_pit

    def gameOver(self):
        player1_empty = all(self.board[pit] == 0 for pit in self.player1_pits)
        player2_empty = all(self.board[pit] == 0 for pit in self.player2_pits)
        if player1_empty or player2_empty:
            # If Player 1's pits are empty, Player 2 collects the remaining seeds
            if player1_empty:
                for pit in self.player2_pits:
                    self.board[2] += self.board[pit]  # Player 2 collects remaining seeds
                    self.board[pit] = 0
            # If Player 2's pits are empty, Player 1 collects the remaining seeds
            if player2_empty:
                for pit in self.player1_pits:
                    self.board[1] += self.board[pit]  # Player 1 collects remaining seeds
                    self.board[pit] = 0
            return True
        return False


class Game:
    def __init__(self):
        self.state = MancalaBoard()
        self.playerSide = {
            1: self.state.player1_pits,
            -1: self.state.player2_pits
        }

    def evaluate(self):
        return self.state.board[1] - self.state.board[2]

    def findWinner(self):
        player1_score = self.state.board[1]
        player2_score = self.state.board[2]
        if player1_score > player2_score:
            return "Computer", player1_score
        elif player2_score > player1_score:
            return "Human", player2_score
        else:
            return "Tie", player1_score

class Play:
    def __init__(self):
        self.game = Game()

    def minimaxAlphaBeta(self, game, player, depth, alpha, beta):
        if game.state.gameOver() or depth == 0:
            return game.evaluate(), None

        if player == 1:  # MAX
            bestValue = -math.inf
            bestMove = None
            for pit in game.state.possibleMoves(game.playerSide[player]):
                child_game = copy.deepcopy(game)
                child_game.state.doMove(game.playerSide[player], pit)
                value, _ = self.minimaxAlphaBeta(child_game, -player, depth-1, alpha, beta)
                if value > bestValue:
                    bestValue = value
                    bestMove = pit
                alpha = max(alpha, bestValue)
                if alpha >= beta:
                    break
            return bestValue, bestMove

        else:  # MIN
            bestValue = math.inf
            bestMove = None
            for pit in game.state.possibleMoves(game.playerSide[player]):
                child_game = copy.deepcopy(game)
                child_game.state.doMove(game.playerSide[player], pit)
                value, _ = self.minimaxAlphaBeta(child_game, -player, depth-1, alpha, beta)
                if value < bestValue:
                    bestValue = value
                    bestMove = pit
                beta = min(beta, bestValue)
                if beta <= alpha:
                    break
            return bestValue, bestMove

    def computerTurn(self):
        _, bestMove = self.minimaxAlphaBeta(self.game, 1, 5, -math.inf, math.inf)
        if bestMove:
            self.game.state.doMove(self.game.playerSide[1], bestMove)

    def humanTurn(self, pit):
        if pit in self.game.state.possibleMoves(self.game.playerSide[-1]):
            self.game.state.doMove(self.game.playerSide[-1], pit)

class MancalaGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mancala Game")
        self.font = pygame.font.Font(None, 36)
        self.play = Play()
        self.pit_rects = {}
        self.store_rects = {}
        self.current_player = -1  # Human starts
        self.computer_move_timer = 0
        self.waiting_for_computer_move = False
        self.game_over_triggered = False
        self.setup_board_layout()

    def setup_board_layout(self):
        pit_width = 100
        pit_height = 150
        start_x = (SCREEN_WIDTH - (6 * pit_width + 5 * 20)) / 2
        start_y = 100

        letters = ['L', 'K', 'J', 'I', 'H', 'G']
        for i, letter in enumerate(letters):
            x = start_x + i * (pit_width + 20)
            rect = pygame.Rect(x, start_y, pit_width, pit_height)
            self.pit_rects[letter] = rect

        start_y = 450
        letters = ['A', 'B', 'C', 'D', 'E', 'F']
        for i, letter in enumerate(letters):
            x = start_x + i * (pit_width + 20)
            rect = pygame.Rect(x, start_y, pit_width, pit_height)
            self.pit_rects[letter] = rect

        self.store_rects[2] = pygame.Rect(start_x - 150 - 20, 100, 150, 300)
        self.store_rects[1] = pygame.Rect(start_x + (6 * pit_width + 5 * 20) + 20, 100, 150, 300)

    def draw_seeds(self, rect, seed_count):
        seed_radius = 8
        max_seeds_per_row = 4
        seed_spacing = 10

        for i in range(seed_count):
            row = i // max_seeds_per_row
            pos_in_row = i % max_seeds_per_row
            x = rect.centerx - (max_seeds_per_row * seed_spacing // 2) + (pos_in_row * seed_spacing)
            y = rect.centery - (row * seed_spacing) + (row * seed_spacing // 2)
            seed_color = SEED_COLORS[i % len(SEED_COLORS)]
            pygame.draw.circle(self.screen, seed_color, (x, y), seed_radius)

    def draw_board(self):
        self.screen.fill(BACKGROUND)

        for letter, rect in self.pit_rects.items():
            # Determine pit color based on whether it belongs to human or computer
            pit_color = HUMAN_COLOR if letter in self.play.game.state.player1_pits else COMPUTER_COLOR
            pygame.draw.rect(self.screen, pit_color, rect)
            seeds = self.play.game.state.board[letter]
            self.draw_seeds(rect, seeds)

        # Draw stores with different colors
        store_color_map = {1: HUMAN_COLOR, 2: COMPUTER_COLOR}
        for store_num, rect in self.store_rects.items():
            pygame.draw.rect(self.screen, store_color_map[store_num], rect)
            seeds = self.play.game.state.board[store_num]
            self.draw_seeds(rect, seeds)

        player_text = "Human's Turn" if self.current_player == -1 else "Computer's Turn"
        text = self.font.render(player_text, True, TEXT_COLOR)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(text, text_rect)

    def get_clicked_pit(self, pos):
        for letter, rect in self.pit_rects.items():
            if rect.collidepoint(pos):
                return letter
        return None

    def display_winner_popup(self):
        winner, score = self.play.game.findWinner()
        popup_text = f"Game Over! {winner} wins with {score} seeds!" if winner != "Tie" else "Game Over! It's a tie!"
        popup = self.font.render(popup_text, True, TEXT_COLOR)
        popup_rect = popup.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(popup, popup_rect)
        pygame.display.flip()
        pygame.time.wait(10000)

    def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.current_player == -1 and event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    clicked_pit = self.get_clicked_pit(pos)
                    if clicked_pit and clicked_pit in self.play.game.state.possibleMoves(self.play.game.playerSide[-1]):
                        self.play.humanTurn(clicked_pit)
                        if self.play.game.state.gameOver():
                            self.current_player = -2  # indicates game over state
                            self.game_over_triggered = True
                        else:
                            # Start timer for computer move
                            self.computer_move_timer = pygame.time.get_ticks()
                            self.waiting_for_computer_move = True
                            self.current_player = 1

            # Delay computer move by 0.5 seconds
            if (self.current_player == 1 and self.waiting_for_computer_move and 
                pygame.time.get_ticks() - self.computer_move_timer >= 500):
                self.play.computerTurn()
                if self.play.game.state.gameOver():
                    self.current_player = -2  # indicates game over state
                    self.game_over_triggered = True
                else:
                    self.current_player = -1
                    self.waiting_for_computer_move = False

            self.draw_board()
            pygame.display.flip()

            # Check for game over after drawing the board
            if self.game_over_triggered:
                pygame.time.delay(500)  # brief pause to show final move
                self.display_winner_popup()
                pygame.quit()
                sys.exit()

            clock.tick(60)

if __name__ == "__main__":
    gui = MancalaGUI()
    gui.run()