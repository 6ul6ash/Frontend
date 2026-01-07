import tkinter as tk
from tkinter import messagebox
import subprocess

# Шлях до backend
backend_path = r"F:\Pal\kursova\backend\x64\Debug\backend.exe"

ROWS, COLS = 6, 7
CELL_SIZE = 60
colors = {0: "white", 1: "red", 2: "yellow"}

root = tk.Tk()
root.title("Connect Four")

canvas = tk.Canvas(root, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE, bg="blue")
canvas.pack()

# Глобальні змінні
board = [[0 for i in range(COLS)] for i in range(ROWS)]
pending_move = False
last_move = None  
currentPlayer = 1

# Таймер
MOVE_TIME = 10  # секунд на хід
time_left = MOVE_TIME
timer_id = None

# Запускаємо backend
backend = subprocess.Popen(
    [backend_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1
)

# ================= Функції =================

def draw_board():
    canvas.delete("all")
    for r in range(ROWS):
        for c in range(COLS):
            x0 = c*CELL_SIZE + 5
            y0 = r*CELL_SIZE + 5
            x1 = (c+1)*CELL_SIZE - 5
            y1 = (r+1)*CELL_SIZE - 5
            canvas.create_oval(x0, y0, x1, y1, fill=colors[board[r][c]])

def animate_click(row, col, player):
    board[row][col] = player
    draw_board()

def animate_last_click(row, col, winner):
    board[row][col] = winner
    draw_board()

def reset_timer():
    global time_left, timer_id
    time_left = MOVE_TIME
    if timer_id is not None:
        root.after_cancel(timer_id)
    timer_id = root.after(1000, countdown)

def countdown():
    global time_left, timer_id
    if time_left > 0:
        time_left -= 1
        root.title(f"Connect Four - Player {currentPlayer} turn ({time_left}s)")
        timer_id = root.after(1000, countdown)
    else:
        # Час вийшов, пропускаємо хід
        root.title(f"Player {currentPlayer} ran out of time!")
        finalize_move(-1)  # можна змінити на автоматичний хід
        

def finalize_move(col):
    global pending_move, last_move, currentPlayer, time_left
    if col >= 0:
        for r in range(ROWS-1, -1, -1):
            if board[r][col] == 0:
                animate_click(r, col, currentPlayer)
                last_move = (r, col)
                break
    try:
        backend.stdin.write(f"{col}\n")
        backend.stdin.flush()
        pending_move = True
        reset_timer()  # перезапускаємо таймер після ходу
        root.after(10, check_backend)
    except OSError:
        pending_move = False

def check_backend():
    global pending_move, currentPlayer, last_move
    if backend.poll() is not None:
        return

    if pending_move:
        # Читаємо новий борд з бекенду
        new_board = []
        for i in range(ROWS):
            line = backend.stdout.readline()
            if not line:
                return
            parts = line.strip().split()
            if len(parts) != COLS:
                return
            new_board.append([int(x) for x in parts])

        for r in range(ROWS):
            board[r] = new_board[r]
        draw_board()

        # Перевіряємо перемогу
        win_line = backend.stdout.readline()
        if win_line:
            win_line = win_line.strip()
            if win_line.startswith("WIN"):
                winner = int(win_line.split()[1])
                if last_move:
                    animate_last_click(last_move[0], last_move[1], winner)
                root.update()
                messagebox.showinfo("Game Over", f"Player {winner} wins!")
                root.destroy()
                return

        # Міняємо гравця
        currentPlayer = 3 - currentPlayer
        pending_move = False
        reset_timer()  # таймер на нового гравця

    root.after(10, check_backend)

def click(event):
    global pending_move
    if pending_move or backend.poll() is not None:
        return
    col = event.x // CELL_SIZE
    finalize_move(col)

# ================= Старт гри =================
canvas.bind("<Button-1>", click)
draw_board()
reset_timer()
root.after(10, check_backend)
root.mainloop()
