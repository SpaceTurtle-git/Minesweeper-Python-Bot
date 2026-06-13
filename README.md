---

# 💣 Minesweeper Automated Solver Bot

An optimized, screen-scraping Minesweeper automation bot written in Python. It uses computer vision (`pyautogui`) to map grid states directly from your screen, converts them into logical constraints using set theory and spatial pattern recognition, and executes physical mouse clicks to solve boards at lightning speeds.

---
#  Bot In Action


https://github.com/user-attachments/assets/fa39babb-e061-4e19-831b-b9f36926f97a


---

## Features

* **Dynamic Calibration**: Supports custom grid dimensions. Calibrates directly to your screen layout by mapping the top-left and bottom-right corners.
* **Computer Vision Scanning**: Samples pixel color arrays to distinguish revealed numbered tiles, flags, and hidden fog-of-war squares dynamically.
* **Flexible Control Schemes**: Run the bot fully automated or step through decisions manually with console feedback.
* **Tiered Logical Solver**: Runs through four layers of algorithmic complexity to determine deterministic moves.
* **Probability Engine**: Calculates a local hazard density score (danger-to-hidden ratios) when deadlocks occur to make informed statistical guesses.

> [!WARNING]
> Because this bot relies on direct screen coordinates and pixel reading, ensure your Minesweeper window is completely unblocked and the game theme colors exactly match the hardcoded `COLOR_PALETTE` matrix.

---

## Tiered Solver & Logic Engine

When analyzing the board state, the execution thread passes data through a prioritized cascading pipeline:

[Scan Grid] ──> [Rule 1: Basic] ──> [Rule 2: Subsets] ──> [Rule 3: Linear] ──> [Rule 4: Shared Intersect]│ 
(If Deadlocked) ▼ [Probability Guessing Engine]

| Strategy Level | Logic Type | Algorithmic Approach |
| :--- | :---: | :--- |
| **Rule 1** | Single-Cell Basic | Trivial bomb flagging and safe-space unlocking based on neighbor counts. |
| **Rule 2** | Subset Reduction | Isolates strict subsets between adjacent cells to calculate hidden tile states. |
| **Rule 3** | 1-2-1 Linear Pattern | Spatial pattern recognition along linear wall edges. |
| **Rule 4** | Shared Intersection | Evaluates partial overlaps between coupled cells using set mathematics and boundary inference. |

###The bot solves the board by applying four distinct, escalating tiers of logical rules. If a lower rule finds a move, the bot executes it immediately and rescans, preventing unnecessary processing.

### Rule 1: Single-Cell Basic
The most fundamental law of Minesweeper. It looks at single cells completely independently by evaluating their 8 immediate neighbors.
* **Forced Flagging:** If a revealed number equals the total count of hidden tiles touching it, *all* those hidden tiles must be mines.
* **Forced Clearing:** If a revealed number already matches the count of flagged tiles touching it, *all* other hidden tiles touching it are 100% safe to click.

<img width="565" height="156" alt="image" src="https://github.com/user-attachments/assets/597c1471-a160-4afc-b3c5-02e8abacab28" />

### Rule 2: Subset Reduction
Triggers when single-cell logic is exhausted. It compares two adjacent numbers by looking at the overlap of their hidden tiles.
* If **Cell A's** hidden tiles are completely swallowed by **Cell B's** hidden tiles, Cell A's mine requirement is a *subset* of Cell B's. 
* By subtracting the smaller set from the larger set, the bot can instantly deduce whether the leftover "unshared" tiles are guaranteed mines or guaranteed safe spaces.

<img width="667" height="159" alt="image" src="https://github.com/user-attachments/assets/2b4027c0-0bb7-4266-b197-0a2232b92776" />

### Rule 3: 1-2-1 Linear Pattern
A hardcoded structural shortcut for flat, linear walls. Instead of running heavy calculations, the bot instantly identifies the classic `1 - 2 - 1` numerical pattern along a straight edge of unopened blocks.
* Due to the tight mathematical constraints of this layout, the solution is always absolute: the tiles directly facing the `1`s are **always mines**, and the tile directly facing the center `2` is **always safe**.

<img width="660" height="160" alt="image" src="https://github.com/user-attachments/assets/ae1f3dcf-b404-43a3-ac4d-f7dcec87501a" />

### Rule 4: Shared Intersection
The most advanced algebraic solver in the book, used to handle complex, partial overlaps where two numbers face each other across a wall but don't neatly swallow each other's tiles.
* The bot isolates the precise **intersection zone** (tiles touching both numbers).
* It calculates the absolute *minimum* and *maximum* number of mines that can mathematically squeeze into that shared intersection. 
* If those intersection limits squeeze the outer, unshared tiles of either number into a logical corner, the bot forces a deduction, smashing open tight bottlenecks.

<img width="655" height="171" alt="image" src="https://github.com/user-attachments/assets/a7677975-afc6-4bba-9bc5-ea2ec48e98a8" />

---

## Prerequisites & Installation

Ensure you have Python 3.x installed, then pull the required system dependencies via `pip`:

```bash
pip install -r requirements.txt
```

---

## How to run bot

```bash
 py bot.py
```

---

## Controls & Execution

Launch the script in your terminal. You **must** calibrate the screen coordinates before launching the automation loops.

| Hotkey | Action | Description |
| :---: | :--- | :--- |
| <kbd>C</kbd> | **Calibrate Coordinates** | Prompts you to hover over the center of the top-left tile and bottom-right tile, pressing `Enter` on each to map the board workspace. |
| <kbd>S</kbd> | **Scan Screen** | Refreshes the internal memory state and updates the console view. |
| <kbd>P</kbd> | **Print Grid** | Prints a text-based layout visualization (`■` = Hidden, `F` = Flagged, `Number` = Revealed). |
| <kbd>A</kbd> | **Toggle Auto-Guess** | Switches the emergency guessing stalemate fallback engine to fully automated. |
| <kbd>Space</kbd> | **Start / Stop Loop** | Fires a random starting click to initialize the board and toggles the main execution cycle. |
| <kbd>B</kbd> | **Debug Pixel** | Prints the exact RGB color codes of wherever your mouse cursor is currently hovering. |
| <kbd>Q</kbd> | **Quit Bot** | Instantly terminates the automation script thread execution. |

---

## Code Architecture Overview

> [!WARNING]
> Use code with caution!

<details>
<summary><b>Click to expand architecture design details</b></summary>

The bot's brain runs continuously through an iterative loop cycle:

1. `scan_and_update()`: Takes a system screenshot, compares pixel regions to a pre-defined BGR color palette, and updates the structural `Cell` objects in runtime memory.
2. `rule_book()`: Iterates sequentially through four tiers of increasing mathematical complexity to find completely valid, zero-risk moves.
3. `execution()`: Translates logical decisions (`pending_click`, `flagged`) into physical, low-level OS mouse inputs.
4. **Fallback Handling**: If no deterministic logical moves are found, `emergency_guess()` calculates a low-risk density space to break the stalemate safely.

### 1. State Layer (Internal Memory Matrix)
The bot maintains a light, object-oriented memory matrix of `Cell` objects.
* Each `Cell` tracks its own grid coordinates, semantic state (`hidden`, `revealed`, `flagged`), and pixel coordinates.
* **Optimization:** Immediate 8-way neighbor pointers are cached into a list upon calibration, completely eliminating coordinate calculation overhead during intense game states.

### 2. Perception Layer (I/O Hub)
This layer translates the physical desktop environment into Python variables.
* **`scan_and_update()`**: Grabs a rapid screen capture via PyAutoGUI, processes it through a NumPy array, and uses Euclidean color-distance matching to decode unrevealed tiles, flags, or explicit numbers.
* **`execution()`**: Sweeps the internal memory map for `pending_click` or `flagged` tags and translates them into physical hardware mouse events across the desktop window.

### 3. Cognition Layer (Waterfall Solver Engine)
The brain operates on a **Short-Circuit Waterfall Priority Strategy** managed by `rule_book()`. It prioritizes computationally cheap math before escalating to deep structural matrix math.

</details>

---

## 🛠️ Diagnostics & Tweaks

If the bot is misreading numbers or clicking off-target, check your color arrays:

```python
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
```
