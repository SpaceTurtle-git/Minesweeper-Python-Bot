import pyautogui
import numpy as np
import keyboard
import time
import random
from math import inf

# Globals
grid_size_x = 16
grid_size_y = 16
grid = None  
RUNNING = True

COLOR_PALETTE = np.asarray([
    [189, 189, 189], # Index 0: Standard Flat Gray (0)
    [0, 0, 255],     # Index 1: Blue (1) 
    [0, 128, 0],     # Index 2: Green (2)
    [255, 0, 0],     # Index 3: Red (3)
    [0, 0, 128],     # Index 4: Dark Blue (4)
    [123, 0, 0],     # Index 5: Dark Red (5)
    [255, 255, 255]  # Index 6: Pure White Bevel (Hidden Indicator)
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
    
    # Calculate cell dimensions accurately as floats from corner to corner
    cell_width = (right_x - left_x) / 15
    cell_height = (bottom_y - top_y) / 15
    
    grid = [[Cell(c, r) for c in range(16)] for r in range(16)]
    
    for row in range(16):
        for col in range(16):
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
                        continue # skip urself
                    
                    neighbor_row = row + dr
                    neighbor_col = col + dc
                    
                    if 0 <= neighbor_row < 16 and 0 <= neighbor_col < 16:
                        current_cell.neighbors.append(grid[neighbor_row][neighbor_col])

def print_board():
    if grid is None:
        print("[ERROR] No board data exists in memory yet. Map the board first!")
        return

    print("\n--- CURRENT BOT MEMORY BOARD ---")
    print("    " + " ".join(f"{c:02d}" for c in range(16)))  
    print("    " + "-----------------------------------------------")
    
    for r in range(16):
        row_strings = []
        for c in range(16):
            cell = grid[r][c]
            if cell.state == 'hidden':
                symbol = "■"  
            elif cell.state == 'flagged':
                symbol = "F" 
            else:
                symbol = str(cell.value) if cell.value > 0 else "." 
            row_strings.append(f" {symbol} ")

        print(f"{r:02d} |" + "".join(row_strings))  
    print("    " + "------------------------------------------------\n")

def calibrate_manually():
    print("\n=== STARTING MANUAL CORNER CALIBRATION ===")
    
    print("1. Hover your mouse over the DEAD CENTER of the TOP-LEFT cell (0,0) and press 'ENTER'...")
    keyboard.wait('enter')
    left_x, top_y = pyautogui.position()
    print(f"Captured Top-Left Origin: ({left_x}, {top_y})")
    time.sleep(0.3)
    
    print("2. Hover your mouse over the DEAD CENTER of the BOTTOM-RIGHT cell (15,15) and press 'ENTER'...")
    keyboard.wait('enter')
    right_x, bottom_y = pyautogui.position()
    print(f"Captured Bottom-Right Bound: ({right_x}, {bottom_y})")
    time.sleep(0.3)
    
    build_grid(left_x, top_y, right_x, bottom_y)
    print("[SUCCESS] Grid mapped cleanly into memory. Ready to scan.\n")

def scan_and_update():
    
    if grid is None:
        print("[ERROR] Cannot scan screen! Calibrate the grid first by pressing Space.")
        return
    
    print("Scanning screen and parsing colors via MSE...")
    screen = pyautogui.screenshot()
    
    for row in range(16):
        for col in range(16):
            cell = grid[row][col]
            
            if cell.state in ('flagged', 'flagged_placed', 'pending_click'):
                continue
                
            #get center pixels for cell
            center_rgb = screen.getpixel((cell.pixel_x, cell.pixel_y))[:3]
            #calculate minimum error for which color
            errors = np.sum(np.square(COLOR_PALETTE - center_rgb), axis=1)  
            #turn error into absolute value
            closest_match = np.argmin(errors)
            
            # Map vision results straight to state variables
            if closest_match == 1:
                cell.state = 'revealed'; cell.value = 1
            elif closest_match == 2:
                cell.state = 'revealed'; cell.value = 2
            elif closest_match == 3:
                cell.state = 'revealed'; cell.value = 3
            elif closest_match == 4:
                cell.state = 'revealed'; cell.value = 4
            elif closest_match == 5:
                cell.state = 'revealed'; cell.value = 5
            else:
                # If closest match is 0 (gray), verify if it's hidden or an empty opened zero
                # We perform a micro sweep on the left edge looking for the white 3D highlight
                is_hidden = False
                left_edge_start = int(cell.pixel_x - (cell.w_radius * 0.45))
                left_edge_end = int(cell.pixel_x - (cell.w_radius * 0.15))
                
                for scan_x in range(left_edge_start, left_edge_end):
                    edge_rgb = screen.getpixel((scan_x, cell.pixel_y))[:3]
                    edge_errors = np.sum(np.square(COLOR_PALETTE - edge_rgb), axis=1)
                    if np.argmin(edge_errors) == 6: # Detected white highlight element
                        is_hidden = True
                        break
                        
                if is_hidden:
                    cell.state = 'hidden'
                    cell.value = 0
                else:
                    cell.state = 'revealed'
                    cell.value = 0

def random_click():
    row, column = random.randint(0, 15), random.randint(0, 15)
    cell = grid[row][column]
    pyautogui.click(cell.pixel_x, cell.pixel_y, button='left')
    time.sleep(0.3)

def rule_one():

    if grid is None: return False
    
    action_found = False
    
    for row in range(16):
        for col in range(16):
            cell = grid[row][col]
            
            if cell.state != 'revealed' or cell.value == 0:
                continue
                
            # make 2 lists for every cell
            hidden_neighbors = [n for n in cell.neighbors if n.state == 'hidden']
            flagged_neighbors = [n for n in cell.neighbors if n.state in ('flagged', 'flagged_placed')] 
            
            num_hidden = len(hidden_neighbors)
            num_flagged = len(flagged_neighbors)
            
            # RULE 1: Flagging Logic
            # If the number of remaining hidden tiles + already flagged tiles 

            if cell.value == (num_hidden + num_flagged) and num_hidden > 0:
                for target in hidden_neighbors:
                    target.state = 'flagged' 
                action_found = True
                
            # RULE 2: Clear Safe Tiles Logic
            # Flagged tiles == num on cell mean hidden cells safe
            elif cell.value == num_flagged and num_hidden > 0:
                for target in hidden_neighbors:
                    target.state = 'pending_click' 
                action_found = True

    return action_found

def rule_book(): 
    #apply rules one by one

    return rule_one()


def execution():
    
    for row in range(16):
        for col in range(16):
            cell = grid[row][col]
            
            # Action A: Cleanly click safe areas
            if cell.state == 'pending_click':
                pyautogui.click(cell.pixel_x, cell.pixel_y, button='left')
                cell.state = 'revealed' # Optimistically change state to minimize screen lag

            # Action B: Place flag markers on found bombs
            elif cell.state == 'flagged_placed':
                continue

            elif cell.state == 'flagged':
                pyautogui.click(cell.pixel_x, cell.pixel_y, button='right')
                cell.state = 'flagged_placed'
                
def main_loop():
    
    scan_and_update()

    available_moves = rule_book()
    
    if not available_moves:
        print("No 100 percent safe moves")
        return False

    execution()
    return True 
    


print(" [Space] - Calibrate Board Coordinates Manually")
print(" [S]     - Scan Screen and Reset Board State")
print(" [P]     - Print Current Bot Brain Grid View")
print(" [H]     - Begin botting")
print(" [Q]     - Quit Script") 

while RUNNING:
    if keyboard.is_pressed("Space"):
        calibrate_manually()
        time.sleep(0.4)
        
    if keyboard.is_pressed("s"):
        for row in range(16):
            for col in range(16):
                cell = grid[row][col]
                cell.state = "hidden"
        scan_and_update()
        print_board()
        time.sleep(0.4)
    
    if keyboard.is_pressed("h"):
        main_loop_activated = True 
        random_click() 
        while main_loop_activated:
            has_moves = main_loop()

            if not has_moves:
                print("Stopping Solving")
                main_loop_activated = False

            if keyboard.is_pressed("h"):
                print("Stopping Solving") 
                main_loop_activated = False
                time.sleep(0.5)
    
    if keyboard.is_pressed("b"):
        x, y = pyautogui.position()
        rgb = pyautogui.pixel(x, y)
        print(f"X:{x}   Y:{y} | RGB: {rgb}")
        time.sleep(0.2)
 
    if keyboard.is_pressed("q"):
        print("Stopping")
        RUNNING = False
    
    if keyboard.is_pressed("p"):
        print_board()
        time.sleep(0.3)
        
    time.sleep(0.02)