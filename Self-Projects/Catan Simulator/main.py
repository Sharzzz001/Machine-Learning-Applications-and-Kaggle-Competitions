import pygame
import sys
from game_state import GameState
from board import BoardRenderer

WIDTH, HEIGHT = 800, 600

def get_best_ai_move(state: GameState):
    # Placeholder for the Optimization/Heuristic Algorithm
    print("\n[AI ENGINE] Calculating best move...")
    print("[AI ENGINE] Decision: Build Road at (x,y)")
    # If the AI decides to buy a dev card:
    # dev_card_override()
    pass

def dev_card_override(state: GameState, player_name: str):
    print(f"\n--- DEV CARD OVERRIDE ---")
    print(f"The AI ({player_name}) decided to buy a Development Card.")
    actual = input("You physically drew a card. What is it? (Knight/VP/Roads/Plenty/Monopoly): ")
    print(f"Injected {actual} into AI's inventory.")
    # state.players[...].dev_cards[actual] += 1

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Catan Cheat Engine")
    clock = pygame.time.Clock()
    
    state = GameState()
    board = BoardRenderer(screen)
    state.board_tiles = board.generate_layout(WIDTH // 2, HEIGHT // 2)

    phase = "SETUP_BOARD"
    
    running = True
    while running:
        screen.fill((30, 144, 255))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if phase == "SETUP_BOARD":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    board.handle_click(event.pos, event.button)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    phase = "SETUP_PLAYERS"
                    
            elif phase == "GAME_LOOP":
                # In the game loop, pressing space triggers the terminal logic for the current turn
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    current = state.get_current_player()
                    print(f"\n--- {current.name}'s Turn ---")
                    
                    if not current.is_ai:
                        roll = input(f"What did {current.name} roll? (2-12): ")
                        print(f"Distributing resources for roll: {roll}")
                        # action = input(f"What did {current.name} do? (e.g. built road): ")
                    else:
                        roll = input(f"What did YOU (AI) roll? (2-12): ")
                        print(f"Distributing resources for roll: {roll}")
                        get_best_ai_move(state)
                        
                    state.next_turn()
                    print("Press SPACE in the Pygame window to process the next turn.")

        board.draw()
        
        # UI Text Instructions
        font = pygame.font.SysFont(None, 24)
        if phase == "SETUP_BOARD":
            text = font.render("Left Click: Cycle Resource | Right Click: Cycle Number | ENTER: Next", True, (255, 255, 255))
        elif phase == "SETUP_PLAYERS":
            text = font.render("Look at Terminal to setup players...", True, (255, 255, 255))
        else:
            text = font.render("GAME ACTIVE. Press SPACE to trigger the next turn.", True, (255, 255, 255))
        screen.blit(text, (20, 20))

        pygame.display.flip()
        
        # Intercept terminal logic smoothly without freezing Pygame
        if phase == "SETUP_PLAYERS":
            print("\n--- PLAYER SETUP ---")
            num = int(input("Enter number of players (2-4): "))
            for i in range(num):
                name = input(f"Enter name for Player {i+1} (In turn order): ")
                is_ai = input(f"Is {name} the AI Engine? (y/n): ").lower() == 'y'
                state.add_player(name, is_ai)
            
            print("\nSetup Complete. The game has started.")
            print("Press SPACE in the Pygame window to process the first turn.")
            phase = "GAME_LOOP"

        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()