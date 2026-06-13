import pyautogui
import numpy as np
import keyboard
import time
import random
from math import inf

#CONFIGURABLE GRID DIMENSIONS
GRID_ROWS = 16  # Vertical size (Y-axis)
GRID_COLS = 16   # Horizontal size (X-axis)

# Globals
grid = None  
RUNNING = True 
AUTO = False
pyautogui.PAUSE = 0.01

# IF YOUR MINESWEEPER USES  DIFFERENT COLOR PALLETE COMNFIGURE IT HERE ACCORDINGLY
COLOR_PALETTE = np.asarray([
    [189, 189, 189], # Index 0: Standard Flat Gray (0)
    [0, 0, 255],     # Index 1: Blue (1) 
    [0, 128, 0],     # Index 2: Green (2)
    [255, 0, 0],     # Index 3: Red (3)
    [0, 0, 128],     # Index 4: Dark Blue (4)
    [123, 0, 0],     # Index 5: Dark Red (5)
    [0, 123, 123],   # Index 6: Teal (6)
    [255, 255, 255]  # Index 7: Pure White Bevel (Hidden Indicator)
])

class Cell:               
    def __init__(self, col, row):
        self.col = col          
        self.row = row          
        self.state = 'hidden'   # 'hidden', 'revealed', 'flagged'
        self.value = 0          
        self.pixel_x = 0        
        self.pixel_y = 0        
        self.neighbors = []     # 8 neighbor cells

def build_grid(left_x, top_y, right_x, bottom_y):
    global grid 
    
    # Dynamically scale step intervals based on custom grid counts
    cell_width = (right_x - left_x) / (GRID_COLS - 1)
    cell_height = (bottom_y - top_y) / (GRID_ROWS - 1)
    
    grid = [[Cell(c, r) for c in range(GRID_COLS)] for r in range(GRID_ROWS)]
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            current_cell = grid[row][col]

            # Calculate precise center location of each individual tile
            current_cell.pixel_x = int(left_x + (col * cell_width))
            current_cell.pixel_y = int(top_y + (row * cell_height))
            
            # Attach scanning boundaries to class object
            current_cell.w_radius = cell_width
            current_cell.h_radius = cell_height
            
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: 
                        continue # skip yourself
                    
                    neighbor_row = row + dr
                    neighbor_col = col + dc
                    
                    # Enforce boundaries relative to variable grid sizes
                    if 0 <= neighbor_row < GRID_ROWS and 0 <= neighbor_col < GRID_COLS:
                        current_cell.neighbors.append(grid[neighbor_row][neighbor_col])

def print_board():
    if grid is None:
        print("[ERROR] No board data exists in memory yet. Map the board first!")
        return

    print("\n--- CURRENT BOT MEMORY BOARD ---")
    print("    " + " ".join(f"{c:02d}" for c in range(GRID_COLS)))  
    print("    " + "---" * GRID_COLS)
    
    for r in range(GRID_ROWS):
        row_strings = []
        for c in range(GRID_COLS):
            cell = grid[r][c]
            if cell.state == 'hidden':
                symbol = "■"  
            elif cell.state in ('flagged', 'flagged_placed'):
                symbol = "F" 
            else:
                symbol = str(cell.value) if cell.value > 0 else "." 
            row_strings.append(f" {symbol} ")

        print(f"{r:02d} |" + "".join(row_strings))  
    print("    " + "---" * GRID_COLS + "\n")

def calibrate_manually():

    print(f"Hover mouse over DEAD CENTER of TOP-LEFT cell (0,0) and press 'ENTER'...")
    keyboard.wait('enter')
    left_x, top_y = pyautogui.position()

    print(f"Captured Top-Left Origin: ({left_x}, {top_y})")
    time.sleep(0.3)
    
    print(f"Hover mouse over DEAD CENTER of BOTTOM-RIGHT cell ({GRID_ROWS-1},{GRID_COLS-1}) and press 'ENTER'...")
    keyboard.wait('enter')
    right_x, bottom_y = pyautogui.position()

    print(f"Captured Bottom-Right Bound: ({right_x}, {bottom_y})")
    time.sleep(0.3)
    
    build_grid(left_x, top_y, right_x, bottom_y)
    print("Grid mapped cleanly into memory.\n")
    print("---------")
    print("SCAN THE BOARD TO BEGIN")

def scan_and_update():
    if grid is None:
        print("[ERROR] Cannot scan screen! Calibrate the grid first by pressing Space.")
        return
    
    screen_pil = pyautogui.screenshot()
    screen = np.array(screen_pil) 
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = grid[row][col]
            
            if cell.state in ('flagged', 'flagged_placed', 'pending_click'):
                continue
                
            center_rgb = screen[cell.pixel_y, cell.pixel_x][:3]
            
            errors = np.sum(np.square(COLOR_PALETTE - center_rgb), axis=1)  
            closest_match = np.argmin(errors)
            
            if closest_match in (1, 2, 3, 4, 5, 6):
                cell.state = 'revealed'
                cell.value = closest_match
            else:
                left_edge_start = int(cell.pixel_x - (cell.w_radius * 0.45))
                left_edge_end = int(cell.pixel_x - (cell.w_radius * 0.15))
                
                edge_pixels = screen[cell.pixel_y, left_edge_start:left_edge_end, :3]
                white_errors = np.sum(np.square(edge_pixels - COLOR_PALETTE[7]), axis=1)
                
                if np.any(white_errors < 500): 
                    cell.state = 'hidden'
                    cell.value = 0
                else:
                    cell.state = 'revealed'
                    cell.value = 0

def random_click():
    row = random.randint(0, GRID_ROWS - 1)
    column = random.randint(0, GRID_COLS - 1)
    cell = grid[row][column]
    pyautogui.click(cell.pixel_x, cell.pixel_y, button='left')
    time.sleep(0.2) #I TRIED LOWER NUMBER THE SCAN CAN IMMEDIATELY PICK UP THE BOARD

def emergency_guess():  #emergency guess the click the least likely bomb spot
    if grid is None: return
    best_cell = None
    min_danger = inf
    
    hidden_pool = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if grid[row][col].state == 'hidden':
                hidden_pool.append(grid[row][col])
                
    if not hidden_pool: return

    for cell in hidden_pool:
        danger_weight = 0.0
        revealed_neighbors = 0
        
        for n in cell.neighbors:
            if n.state == 'revealed' and n.value > 0:
                revealed_neighbors += 1
                n_hidden = sum(1 for active in n.neighbors if active.state == 'hidden')
                n_flagged = sum(1 for active in n.neighbors if active.state in ('flagged', 'flagged_placed'))
                rem_mines = n.value - n_flagged
                if n_hidden > 0:
                    danger_weight += (rem_mines / n_hidden)
                    
        if revealed_neighbors > 0:
            total_score = danger_weight / revealed_neighbors
        else:
            total_score = 0.15
            
        if total_score < min_danger:
            min_danger = total_score
            best_cell = cell

    target = best_cell if best_cell else random.choice(hidden_pool)
    print(f"Guess executed at Row:{target.row} Col:{target.col} (Danger: {round(min_danger, 2)*100}%)")
    pyautogui.click(target.pixel_x, target.pixel_y, button='left')
    time.sleep(0.08)

def rule_one():  #bomb flagging ang 100% safe space clicker rule
    if grid is None: return False
    action_found = False
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = grid[row][col]
            
            if cell.state != 'revealed' or cell.value == 0:
                continue
                
            hidden_neighbors = [n for n in cell.neighbors if n.state == 'hidden']
            flagged_neighbors = [n for n in cell.neighbors if n.state in ('flagged', 'flagged_placed')] 
            
            num_hidden = len(hidden_neighbors)
            num_flagged = len(flagged_neighbors)
            
            if cell.value == (num_hidden + num_flagged) and num_hidden > 0:
                for target in hidden_neighbors:
                    target.state = 'flagged' 
                action_found = True
                
            elif cell.value == num_flagged and num_hidden > 0:
                for target in hidden_neighbors:
                    target.state = 'pending_click' 
                action_found = True

    return action_found

def rule_two():   #subset Redution Logic
    if grid is None: return False
    action_found = False
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cellA = grid[row][col]
          
            if cellA.state != 'revealed' or cellA.value == 0: 
                continue

            hiddenA = set(n for n in cellA.neighbors if n.state == 'hidden')
            flaggedA = sum(1 for n in cellA.neighbors if n.state in ('flagged', 'flagged_placed'))
            effectiveA = cellA.value - flaggedA
            
            if not hiddenA: 
                continue

            for cellB in cellA.neighbors:
                if cellB.state != 'revealed' or cellB.value == 0 or cellB == cellA: 
                    continue

                hiddenB = set(n for n in cellB.neighbors if n.state == 'hidden')
                flaggedB = sum(1 for n in cellB.neighbors if n.state in ('flagged', 'flagged_placed'))
                effectiveB = cellB.value - flaggedB
                
                if not hiddenB: 
                    continue

                # Check if A's hidden tiles are completely wrapped inside B's hidden tiles
                if hiddenA.issubset(hiddenB) and hiddenA != hiddenB:
                    extra_tiles = hiddenB - hiddenA          #subtracts the shared sets to isolate the hidden tiles that only touch Cell B.
                    mine_diff = effectiveB - effectiveA      #determines how many mines are left unaccounted for outside the shared zone.

                    # Case 1: Both sets need the same number of mines. Extra tiles are SAFE.
                    if mine_diff == 0:
                        for target in extra_tiles:
                            if target.state == 'hidden':
                                target.state = 'pending_click'
                                action_found = True
                                
                    # Case 2: Excess mines equal the exact number of extra tiles. Extra tiles are MINES.
                    elif mine_diff == len(extra_tiles):
                        for target in extra_tiles:
                            if target.state == 'hidden':
                                target.state = 'flagged'
                                action_found = True
                                
    return action_found

def rule_three(): #classic 121 minesweeper pattern
    """Identifies and solves classic 1-2-1 linear wall configurations."""
    if grid is None: return False
    action_found = False

    # Helper function to safely calculate unflagged neighbor cells
    def get_eff(cell):
        if cell.state != 'revealed' or cell.value == 0:
            return -1
        flagged = sum(1 for n in cell.neighbors if n.state in ('flagged', 'flagged_placed'))
        return cell.value - flagged

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            
            # --- CASE A: Horizontal 1-2-1 Pattern [ 1 ][ 2 ][ 1 ] ---
            if col < GRID_COLS - 2:
                cA = grid[row][col]
                cB = grid[row][col+1]
                cC = grid[row][col+2]

                if get_eff(cA) == 1 and get_eff(cB) == 2 and get_eff(cC) == 1:
                    # Find shared hidden blocks above or below this horizontal line
                    for dr in [-1, 1]:
                        r_check = row + dr
                        if 0 <= r_check < GRID_ROWS:
                            tA = grid[r_check][col]
                            tB = grid[r_check][col+1]
                            tC = grid[r_check][col+2]

                            if tA.state == 'hidden' and tB.state == 'hidden' and tC.state == 'hidden':
                                tA.state = 'flagged'
                                tB.state = 'pending_click'  # The center is safe!
                                tC.state = 'flagged'
                                action_found = True

            # --- CASE B: Vertical 1-2-1 Pattern ---
            if row < GRID_ROWS - 2:
                cA = grid[row][col]
                cB = grid[row+1][col]
                cC = grid[row+2][col]

                if get_eff(cA) == 1 and get_eff(cB) == 2 and get_eff(cC) == 1:
                    # Find shared hidden blocks to the left or right of this vertical line
                    for dc in [-1, 1]:
                        c_check = col + dc
                        if 0 <= c_check < GRID_COLS:
                            tA = grid[row][c_check]
                            tB = grid[row+1][c_check]
                            tC = grid[row+2][c_check]

                            if tA.state == 'hidden' and tB.state == 'hidden' and tC.state == 'hidden':
                                tA.state = 'flagged'
                                tB.state = 'pending_click'  # The center is safe!
                                tC.state = 'flagged'
                                action_found = True

    return action_found

def rule_four():  #shared Intersection Rule 
    if grid is None: return False
    action_found = False
    
    numbered_cells = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            cell = grid[r][c]
            if cell.state == 'revealed' and cell.value > 0:
                numbered_cells.append(cell)

    for i in range(len(numbered_cells)):
        cellA = numbered_cells[i]
        hiddenA = set(n for n in cellA.neighbors if n.state == 'hidden')
        if not hiddenA: continue
        flaggedA = sum(1 for n in cellA.neighbors if n.state in ('flagged', 'flagged_placed'))
        effA = cellA.value - flaggedA

        for j in range(i + 1, len(numbered_cells)):
            cellB = numbered_cells[j]
            hiddenB = set(n for n in cellB.neighbors if n.state == 'hidden')
            if not hiddenB: continue
            flaggedB = sum(1 for n in cellB.neighbors if n.state in ('flagged', 'flagged_placed'))
            effB = cellB.value - flaggedB

            intersection = hiddenA.intersection(hiddenB)
            if not intersection: continue

            onlyA = hiddenA - intersection
            onlyB = hiddenB - intersection

            max_in_intersection = min(effA, len(intersection))
            min_in_intersection = max(0, effA - len(onlyA))

            if effB - len(onlyB) == max_in_intersection and len(onlyB) > 0:
                for target in onlyB:
                    if target.state == 'hidden':
                        target.state = 'flagged'
                        action_found = True

            if effB == min_in_intersection and len(onlyB) > 0:
                for target in onlyB:
                    if target.state == 'hidden':
                        target.state = 'pending_click'
                        action_found = True
                        
    return action_found

def rule_book(): 
    if rule_one(): 
        return True
    if rule_two():
        return True
    if rule_three():
        return True
    return rule_four()

def execution(): # clicking part
    clicked_any = False
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = grid[row][col]

            if cell.state == 'pending_click':
                pyautogui.click(cell.pixel_x, cell.pixel_y, button='left')
                cell.state = 'revealed' 
                clicked_any = True

            elif cell.state == 'flagged':
                pyautogui.click(cell.pixel_x, cell.pixel_y, button='right')
                cell.state = 'flagged_placed'
                clicked_any = True
    if clicked_any:
        time.sleep(0.08) # Let OS frame buffers clear

def main_loop():  #main shi
    scan_and_update()
    available_moves = rule_book()
    
    if not available_moves:
        print("No 100 percent safe moves")
        return False

    execution()
    return True 

print(" [C]     - Calibrate Board Coordinates ")
print(" [S]     - Scan Screen and Reset Board State")
print(" [P]     - Print Current Bot Brain Grid View")
print(" [Q]     - Quit Script") 
print(" [A]     - Turn OFF Automated Emergency Guessing") 
print(" [SPACE] - Begin botting")

while RUNNING:
    if keyboard.is_pressed("c"):
        calibrate_manually()
        time.sleep(0.4)
        
    if keyboard.is_pressed("s"):
        if grid is not None:
            for row in range(GRID_ROWS):
                for col in range(GRID_COLS):
                    cell = grid[row][col]
                    cell.state = "hidden"
            scan_and_update()
            print_board()
        else:
            print("Map the board first before scanning")
        time.sleep(0.4)
    
    if keyboard.is_pressed("Space"):
        main_loop_activated = True 
        random_click() 
        while main_loop_activated:
            has_moves = main_loop()

            if not has_moves and AUTO == True:
                print("Emergency guessing")
                emergency_guess()
                scan_and_update()
                if not rule_book():
                    print("No useful info revealed from Emergency guessing")

            elif not has_moves and AUTO == False:
                print("Press Y to emergency guess or N to skip")

                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    key = event.name.lower()

                    if key == 'y':
                        emergency_guess()
                        scan_and_update()
                        if not rule_book():
                            print("No useful info revealed from Emergency guessing")
                    if key == 'n':
                        print("Skipping")
                        continue

            if keyboard.is_pressed("Space"): 
                print("Stopping Solving") 
                main_loop_activated = False
                time.sleep(0.2)
    
    if keyboard.is_pressed("b"):
        x, y = pyautogui.position()
        rgb = pyautogui.pixel(x, y)
        print(f"X:{x}   Y:{y} | RGB: {rgb}")
        time.sleep(0.2)
 
    if keyboard.is_pressed("q"):
        print("Stopping")
        RUNNING = False
        time.sleep(0.3)

    if keyboard.is_pressed("A"):
        print("AUTOMATED EMERGENCY GUESSING SWITCHED")
        AUTO = True
        time.sleep(0.3)

    if keyboard.is_pressed("p"):
        print_board()
        time.sleep(0.3)
        
    time.sleep(0.02)