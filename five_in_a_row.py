#!/usr/bin/env python

import pygame, sys
from time import sleep
from collections import defaultdict

WIDTH, HEIGHT = 720, 720
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
BUTTON_WIDTH, BUTTON_HEIGHT = 200, 80

ROWS, COLUMNS = 10, 10
WIN_COUNT = 5

# how many sons should each node in the minimax tree have
MINIMAX_DEPTH = 4
# for efficiency, only this number of closest sons are checked
MINIMAX_WIDTH = 50


def create_board():
    board = []
    border = [2]*(COLUMNS+2)
    board.append(border)
    for i in range(ROWS):
        row = [2]
        for j in range(COLUMNS):
            row.append(0)
        row.append(2)
        board.append(row)
    board.append(border)
    return board


def set(position, sign, board): 
    board[position[0]][position[1]] = sign


def get_position(board, grid, sqsize, click):

    left, top = grid[0], grid[1]
    c = (click[0]-left)//sqsize + 1
    r = (click[1]-top)//sqsize + 1
    
    if board[r][c] == 0: 
        return (r, c)
    return "invalid"


def has_won(pozice, player, board):
    
    def _vyhra_smerem(pozice, smer, board, player, counter=1):

        initial = pozice
        for i in range(2):
            while board[pozice[0] + smer[0]][pozice[1] + smer[1]] == player:
                counter += 1
                pozice = (pozice[0]+smer[0], pozice[1]+smer[1])
            pozice = initial
            smer = (-smer[0], -smer[1])

        if counter >= WIN_COUNT:
            return True
        return False
        
    return (_vyhra_smerem(pozice, (0, 1), board, player) or _vyhra_smerem(pozice, (1, 1), board, player)
     or _vyhra_smerem(pozice, (1, 0), board, player) or _vyhra_smerem(pozice, (1, -1), board, player))


def find_next(board, last, top, bottom, left, right, direction=(0,1)):

    r, c = last
    while True:
        r, c = r+direction[0], c+direction[1]
        if c > right: 
            if right < COLUMNS: right += 1
            if direction == (0, 1): direction = (-1, 0)
        elif c < left:
            if left > 1: left -=1
            if direction == (0, -1): direction = (1, 0)
        if r > bottom:
            if bottom < ROWS: bottom += 1
            if direction == (1, 0): direction = (0, 1)
        elif r < top:
            if top > 1: top -= 1
            if direction == (-1, 0): direction = (0, -1)
        if board[r][c] == 0: break
        
    return (r,c), direction, top, bottom, left, right


def evaluate_section(section, player):
    # return the score for one list representing one row/column/diagonal by splitting it 
    # into smaller chunks which are evaled by eval_section

    def _too_strong(points, sign, player): 
        return points==100 or (points==50 and player==sign)
    
    combinations = {
        (-1, 1, 1, 1, 1, 0): 50,
        (-1, 0, 1, 1, 1, 0): 50,
        (-1, 0, 1, 1, 0, 0): 25,
        (-1, 1, 1, 1, 0, 0): 25,
        (-1, 1, 1, 0, 1, 0): 25,
        (-1, 1, 0, 1, 1, 0): 25,
        (0, 1, 1, 1, 1, 0): 100,
        (0, 0, 1, 1, 1, 0): 50,
        (0, 1, 1, 1, 0, 0): 50,
        (0, 1, 1, 0, 1, 0): 50,
        (0, 1, 0, 1, 1, 0): 50,
        (0, 0, 1, 1, 0, 0): 25,
        (0, 1, 1, 1, 1, -1): 50,
        (0, 1, 1, 1, 0, -1): 50,
        (0, 0, 1, 1, 0, -1): 25,
        (0, 0, 1, 1, 0, -1): 25,
        (0, 0, 1, 1, 1, -1): 25,
        (0, 1, 0, 1, 1, -1): 25,
        (0, 1, 1, 0, 1, -1): 25
        }

    combinations = defaultdict(lambda: 0, combinations)

    five_seq = {
        (1, 1, 0, 1, 1): 50,
        (1, 0, 1, 1, 1): 50,
        (1, 1, 1, 0, 1): 50,
    }

    five_seq = defaultdict(lambda: 0, five_seq)

    k = 1
    while section[k] == 0: k += 1
    if k == len(section)-1: return 0
    section[0] = -section[k]
    k = -2
    while section[k] == 0: k -= 1
    section[-1] = -section[k]

    skore = 0
    fronta = []
    for i in range(6): fronta.append(section[i])
    j = 6
    while j <= len(section)-1:        
        temp = combinations[tuple(fronta)]
        if _too_strong(temp, 1, player): return 10000
        skore += temp
        temp = combinations[tuple(map(lambda x: -x, fronta))]
        if _too_strong(temp, -1, player): return -10000
        skore -= temp
        
        fronta.pop(0)
        five_search = five_seq[tuple(fronta)]
        opposite_five = five_seq[tuple(map(lambda x: -x, fronta))]
        if five_search or opposite_five:
            if _too_strong(five_search, 1, player): return 10000
            if _too_strong(opposite_five, -1, player): return -10000
            skore += five_search
            skore -= opposite_five
            fronta.pop(0)
            if j < len(section) - 1:
                j += 1
                fronta.append(section[j])
        fronta.append(section[j])

        j += 1
    
    return skore

        
def get_section(board, start, smer):    

    start = (start[0]-smer[0], start[1]-smer[1])
    current_sequence = []
    while start[0] <= ROWS+1 and start[0] >= 0 and start[1] <= COLUMNS+1:
        current_sequence.append(board[start[0]][start[1]])
        start = (start[0]+smer[0], start[1]+smer[1])
    return current_sequence
    

def get_indices(positions):

    indices = []
    for position in positions:
        r, c = position
        position_indices = [(r, (r, 1), (0, 1)), (ROWS+c, (1, c), (1, 0))]
        d_num = ROWS-WIN_COUNT+1
        while r > 1 and c > 1: r, c = r-1, c-1
        if c == 1: 
            if r <= d_num: position_indices.append((ROWS+COLUMNS+r, (r, c), (1, 1)))
        else: 
            if c <= d_num: position_indices.append((ROWS+COLUMNS+d_num+c-1, (r, c), (1, 1)))
        r, c = position
        while r < ROWS and c > 1: r, c = r+1, c-1
        if c == 1:
            if r > ROWS-d_num: position_indices.append((ROWS+COLUMNS+2*d_num-1+ROWS-r+1, (r, c), (-1, 1)))
        else:
            if c <= d_num: position_indices.append((ROWS+COLUMNS+3*d_num-1+c-1, (r, c), (-1, 1)))
        
        for p in position_indices:
            if p not in indices: indices.append(p)
    return indices
    

def eval(board, player, positions, section_values):

    indices = get_indices(positions)
    for elem in indices:
        index, start, smer = elem
        value = evaluate_section(get_section(board, start, smer), player)
        section_values[index] = value
    return sum(section_values)


def minimax(menu, board, player, positions, pieces, section_values, alpha=-100000, beta=100000, depth=1):

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            click = pygame.mouse.get_pos()
            if on_object(menu, click): return None, None

    # player je, kdo je v současném uzlu na řadě
    last_position = positions[-1]
    if has_won(last_position, -player, board):
        return -player*10000, last_position
    elif depth == MINIMAX_DEPTH:
        xvalues = section_values.copy()
        return eval(board, player, positions, xvalues), last_position

    best_son = None 
    fields_checked = 0
    t = b = last_position[0]
    l = r = last_position[1]
    direction = (0, 1)

    while fields_checked < min(MINIMAX_WIDTH, ROWS*COLUMNS-pieces):
        current_position, direction, t, b, l, r = \
            find_next(board, last_position, t, b, l, r, direction)
        znak = board[current_position[0]][current_position[1]]
        # going through state space, expanding the free positions
        if znak == 0:
            fields_checked += 1
            # creates the copy of the board which can be edited in recursion
            xboard = []
            for i in range(len(board)):
                inner = board[i].copy()
                xboard.append(inner)
            xboard[current_position[0]][current_position[1]] = player

            xpositions = positions.copy()
            xpositions.append(current_position)

            value, position = minimax(menu, xboard, -player, xpositions, \
                pieces+1, section_values, alpha, beta, depth+1)

            # clicked on menu button
            if value == None and position == None: return None, None
            if player == -1 and value < beta:
                beta = value
                best_son = current_position
            elif player == 1 and value > alpha:
                alpha = value
                best_son = current_position
            if alpha >= beta:
                # if this occurs, we can prune and value will not change in parent
                # outside eval range - best_son doesnt get rewritten
                # we dont care about the position returned unless its the last free space
                if player == 1:
                    return 100000, current_position
                else: return -100000, current_position

        last_position = current_position

    if player == -1:
        return beta, best_son
    else:   return alpha, best_son


def get_text(message, size, x, y):

    font = pygame.font.SysFont("verdana", size)
    text = font.render(message, 0, 0x0)
    text_area = text.get_rect(center=(x, y))
    return text, text_area


def game_over_message(message):

    text, text_area = get_text(message, 35, WIDTH//2, HEIGHT//2)
    pygame.draw.rect(WIN, 0xffffff, text_area)
    WIN.blit(text, text_area)
    pygame.display.update()
    sleep(3)


def draw_button(label, midx, midy, resize=1):

    text, text_area = get_text(label, int(30*resize), midx, midy)
    left, top = midx - BUTTON_WIDTH*resize//2, midy - BUTTON_HEIGHT*resize//2

    b = pygame.draw.rect(WIN, 0x0, (left, top, BUTTON_WIDTH*resize, BUTTON_HEIGHT*resize), width=1, border_radius=5)
    WIN.blit(text, text_area)
    return b


def on_object(object, click): 
    
    return click[0] >= object[0] and click[0] <= object[0]+object[2] and click[1] >= object[1] \
        and click[1] <= object[1]+object[3]


def startup():

    WIN.fill(0xffffff)
    title, title_coord = get_text("FIVE IN A ROW", 60, WIDTH//2, HEIGHT//8)
    WIN.blit(title, title_coord)

    # logo position
    logo_radius = HEIGHT//4
    midx, midy = WIDTH//2, HEIGHT//2
    top, bottom = midy-logo_radius, midy+logo_radius
    left, right = midx-logo_radius, midx+logo_radius
    # logo drawing
    pygame.draw.line(WIN, 0x0, (midx, top), (midx, bottom), width=2)
    pygame.draw.line(WIN, 0x0, (left, midy), (right, midy), width=2)

    pygame.draw.circle(WIN, 0x012d6, ((left+midx)//2, (top+midy)//2), logo_radius*3//8, width=5)
    pygame.draw.circle(WIN, 0x012d6, ((midx+right)//2, (midy+bottom)//2), logo_radius*3//8, width=5)

    pad = logo_radius//8
    pygame.draw.line(WIN, 0xff0000, (midx+pad, top+pad), (right-pad, midy-pad), width=5)
    pygame.draw.line(WIN, 0xff0000, (midx+pad, midy-pad), (right-pad, top+pad), width=5)
    pygame.draw.line(WIN, 0xff0000, (left+pad, midy+pad), (midx-pad, bottom-pad), width=5)
    pygame.draw.line(WIN, 0xff0000, (left+pad, bottom-pad), (midx-pad, midy+pad), width=5)

    # play buttons
    ai_button = draw_button("Singleplayer", WIDTH//4, HEIGHT*7//8)
    player_button = draw_button("Multiplayer", WIDTH*3//4, HEIGHT*7//8)
    return ai_button, player_button


def playing_screen():

    grid_size = min(WIDTH, HEIGHT)*3//4
    midx, midy = WIDTH//2, HEIGHT//2
    left, top = midx - grid_size//2, midy*7//8 - grid_size//2
    sqsize = grid_size//ROWS

    # draw column separators
    for i in range(COLUMNS+1):
        pygame.draw.line(WIN, 0x0, (i*sqsize+left, top), (i*sqsize+left, grid_size+top))
    # draw row separators
    for j in range(ROWS+1):
        pygame.draw.line(WIN, 0x0, (left, j*sqsize+top), (grid_size+left, j*sqsize+top))

    #WIDTH - BUTTON_WIDTH//2 - 10
    b = draw_button("menu", WIDTH//2, HEIGHT - BUTTON_HEIGHT//2 - 10, resize=0.75)
    return (left, top, grid_size, grid_size), sqsize, b


def draw(board, grid, sqsize, position, highlighted=True):

    left, top = grid[0], grid[1]
    r, c = position

    startx = left + (c-1)*sqsize
    starty = top + (r-1)*sqsize

    if highlighted: pygame.draw.rect(WIN, 0xd9e665, (startx+2, starty+2, sqsize-2, sqsize-2))
    else: pygame.draw.rect(WIN, 0xffffff, (startx+2, starty+2, sqsize-2, sqsize-2))

    if board[position[0]][position[1]] == 1: pygame.draw.circle(WIN, 0x0012d6, (startx+sqsize//2, starty+sqsize//2), sqsize*7//16, width=3)
    else:
        pad = sqsize//8
        pygame.draw.line(WIN, 0xff0000, (startx+pad, starty+pad), (startx+sqsize-pad, starty+sqsize-pad), width=3)
        pygame.draw.line(WIN, 0xff0000, (startx+pad, starty+sqsize-pad), (startx+sqsize-pad, starty+pad), width=3)
    pygame.display.update(startx, starty, sqsize, sqsize)


def play(ai_on):

    WIN.fill(0xFFFFFF)
    grid_coord, sqsize, menu_button = playing_screen()

    board = create_board()
    player = -1
    pieces_placed = 0
    section_values = [0]*(6*ROWS - 4*WIN_COUNT + 3)
    opposition, position = (1, 1), (1, 1)
    pygame.display.update()

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = pygame.mouse.get_pos()
                if on_object(menu_button, click): run = False
                if on_object(grid_coord, click):

                    player = - player
                    if ai_on and pieces_placed>0: draw(board, grid_coord, sqsize, opposition, highlighted=False)
                    elif pieces_placed>0: draw(board, grid_coord, sqsize, position, highlighted=False)
                    position = get_position(board, grid_coord, sqsize, click)
                    if position == "invalid": player = - player
                    else:
                        set(position, player, board)
                        pieces_placed += 1
                        draw(board, grid_coord, sqsize, position)
                        if has_won(position, player, board):
                            game_over_message(f"Player {player%3} has won!")
                            run = False
                        elif pieces_placed == ROWS*COLUMNS:  
                            game_over_message("Draw!")
                            run = False
                    pygame.display.update()

                    if ai_on and position != "invalid": 
                        # calculates section values
                        # must be done in the section of the player for whom I run the eval function
                        eval(board, player, [position, opposition], section_values)

                        player = - player
                        value, opposition = minimax(menu_button, board, -1, [position], pieces_placed, section_values)
                        if opposition == None and value == None: run=False
                        else:
                            set(opposition, player, board)
                            # position = generate_position(board)

                            pieces_placed += 1
                            draw(board, grid_coord, sqsize, opposition)
                            draw(board, grid_coord, sqsize, position, highlighted=False)

                            if has_won(opposition, player, board):
                                game_over_message("Player 2 has won!")
                                run = False
                            elif pieces_placed == ROWS*COLUMNS:  
                                game_over_message("Draw!")
                                run = False 
                        pygame.display.update()


def main():

    pygame.init()
    pygame.display.set_caption("Five in a row")
    
    run = True
    while run:
        ai_button, player_button = startup()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = pygame.mouse.get_pos()
                if on_object(ai_button, click): play(ai_on=True)
                elif on_object(player_button, click): play(ai_on=False)

        pygame.display.update()

    pygame.quit()


if __name__ == '__main__':
    main()
