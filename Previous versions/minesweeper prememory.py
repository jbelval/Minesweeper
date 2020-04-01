import tkinter as tk
import PIL
import random
import time
import glob, os, sys
from collections import defaultdict

"""This is a rewrite to make bomb information hidden behind second grid instead of embedded in buttons
This will allow me to create the bombs after the first choice is made
Idea is to make two grids, one with Button classes, one with a custom info class
"""

"""Carryover Variables"""
best_times = {'small':999, 'medium':'999', 'large':999}

def update_best_times(size, time):
    if best_times[size] > time:
        best_times[size] = time

class Application(tk.Frame):

    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.game = None
        self.top_menu = TopMenu(self)
        self.top_menu.pack(side='top')
        self.pack()
        self.root.bind('<Destroy>', self.destroy)

    def start_game(self):
        if self.game != None:
            self.game.destroy()
        try:
            self.game = Game(self, self.top_menu.drop_down.get(self.top_menu.drop_down.curselection()))
        except:
            self.game = Game(self, 'medium')
        self.game.pack(side='bottom')

    def destroy(self, event):
        pass
        # with open('__file__', 'r') as f:
        #     lines = f.readlines()
        # for i in range(len(lines)):
        #     if lines(i) == """"""

class TopMenu(tk.Frame):

    def __init__(self, root):
        super().__init__(root)
        self.root = root

        self.label = tk.Label(self, text='Board Size')
        self.drop_down = tk.Listbox(self, height=3, width=12)
        self.drop_down.insert(0, 'small')
        self.drop_down.insert(1, 'medium')
        self.drop_down.insert(2, 'large')
        self.confirm_button = tk.Button(self, text='Start Game', command=self.root.start_game)
        self.label.pack(side='left', padx=5)
        self.drop_down.pack(side='left', padx=5)
        self.confirm_button.pack(side='left', padx=5)

class Game(tk.Frame):

    BOMBS_FOR_SIZE = defaultdict(lambda: 40, small=10, medium=40, large=99)
    LENGTH_FOR_SIZE = defaultdict(lambda: 18, small=10, medium=18, large=24)

    def __init__(self, parent, size=18):
        super().__init__(parent)
        self.parent = parent
        self.size = size
        self.bomb_count = Game.BOMBS_FOR_SIZE[size]
        self.length = Game.LENGTH_FOR_SIZE[size]
        self.flag_count = 0
        self.found_tiles = 0
        self.is_over = False
        self.start = None
        self.button_images = self.get_images()
        self.info = Board(self.length)
        self.buttons = Board(self.length)
        self.populate_buttons()
        self.header = GameHeader(self)
        self.header.grid(row=0, columnspan=self.length)

    def event_handler(self, event, x, y):
        if self.start == None:
            self.start = time.time()
            self.populate_board(x, y)
            self.update_timer()
            self.update_bombs()

        if self.is_over == True:
            return

        if event == 'left_click':
            self.check(x, y)
        elif event == 'right_click':
            self.flag(x, y)
        elif event == 'double_left_click':
            self.explore(x, y)

    def populate_buttons(self):
        for x in range(self.length):
            for y in range(self.length):
                self.buttons[x][y] = TileButton(self, x, y)
                self.buttons[x][y].configure(image=self.button_images['Unpressed'], borderwidth=0)
                self.buttons[x][y].grid(row=x+1, column=y)

    def populate_board(self, x, y):
        self.placed_bombs = 0
        while self.placed_bombs < self.bomb_count:
            i = random.randint(0, self.length-1)
            j = random.randint(0, self.length-1)
            if (x-i)**2>1 or (y-j)**2>1:
                self.info[i][j] = TileInfo('Mine', i, j)
                self.placed_bombs +=1
        for i in range(self.length):
            for j in range(self.length):
                if self.info[i][j] == None:
                    self.info[i][j] = TileInfo('Empty', i, j)

    def update_bombs(self):
        if self.is_over:
            return
        num = self.bomb_count - self.flag_count
        self.header.bomb_label['text'] = f'{num:03}'

    def update_timer(self):
        if self.is_over:
            return
        elapsed = int(time.time() - self.start)
        self.header.timer['text'] = f'{elapsed:03}'
        self.parent.after(1000, self.update_timer)

    def get_images(self):
        os.chdir(sys.path[0])
        image_dic = {}
        for file in glob.glob('*.png'):
            key = file.split('.')[0]
            image_dic[key] = tk.PhotoImage(file=file)
        return image_dic

    def check(self, x, y):
        if self.info[x][y].flagged:
            return
        if self.info[x][y].clicked:
            return

        if self.info[x][y].type == 'Mine':
            self.buttons[x][y]['image'] = self.button_images['Mine']
            self.trigger_loss()
        elif self.info[x][y].type == 'Empty':
            self.info[x][y].clicked = True
            adj_bombs = self.adjacent_bombs(x, y)
            self.found_tiles +=1
            if adj_bombs != 0:
                self.buttons[x][y]['image'] = self.button_images[str(adj_bombs)]
            elif adj_bombs == 0:
                self.buttons[x][y]['image'] = self.button_images['Pressed']
                for i in range(max(0, x-1), min(self.length-1, x+1)+1):
                    for j in range(max(0, y-1), min(self.length-1, y+1)+1):
                        if self.info[i][j].type == 'Empty' and not self.info[i][j].clicked:
                            self.check(i, j)
        if self.found_tiles == self.length**2 - self.bomb_count:
            self.trigger_win()

    def flag(self, x, y):
        if self.info[x][y].clicked:
            return

        if self.info[x][y].flagged:
            self.info[x][y].flagged = False
            self.flag_count -=1
            self.buttons[x][y]['image'] = self.button_images['Unpressed']
        else:
            self.info[x][y].flagged = True
            self.flag_count +=1
            self.buttons[x][y]['image'] = self.button_images['Flag']
        self.update_bombs()

    def explore(self, x, y):
        if self.info[x][y].flagged:
            return
        if self.adjacent_bombs(x, y) == self.adjacent_flags(x, y):
            for i in range(max(0, x-1), min(self.length-1, x+1)+1):
                for j in range(max(0, y-1), min(self.length-1, y+1)+1):
                    if not self.info[i][j].clicked and not self.info[i][j].flagged:
                        self.check(i, j)

    def adjacent_bombs(self, x, y):
        count = 0
        for i in range(max(0, x-1), min(self.length-1, x+1)+1):
            for j in range(max(0, y-1), min(self.length-1, y+1)+1):
                if self.info[i][j].type == 'Mine':
                    count +=1
        return count

    def adjacent_flags(self, x, y):
        count = 0
        for i in range(max(0, x-1), min(self.length-1, x+1)+1):
            for j in range(max(0, y-1), min(self.length-1, y+1)+1):
                if self.info[i][j].flagged:
                    count +=1
        return count

    def trigger_loss(self):
        self.is_over = True
        for x in range(self.length):
            for y in range(self.length):
                if self.info[x][y].type == 'Mine':
                    self.buttons[x][y]['image'] = self.button_images['Mine']
                # if self.info[x][y].flagged and self.info[x][y].type == 'Empty'
        self.popup = tk.Toplevel(self)
        self.message = tk.Label(self.popup, text='You lose. Sorry :/')
        self.message.grid(row=0, column=0, columnspan=5)
        self.exit_button = tk.Button(self.popup, text='exit', command=self.popup.destroy)
        self.exit_button.grid(row=1, column=0, columnspan=5)

    def trigger_win(self):
        self.is_over = True
        update_best_times(self.size, int(self.header.timer['text']))
        self.popup = tk.Toplevel(self)
        self.message = tk.Label(self.popup, text='You won!!')
        self.message.grid(row=0, column=0, columnspan=5)
        self.exit_button = tk.Button(self.popup, text='exit', command=self.popup.destroy)
        self.exit_button.grid(row=1, column=0, columnspan=5)

class GameHeader(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self. parent = parent
        self.bomb_label = tk.Label(self, text=f'{self.parent.bomb_count:03}', font=("Courier", 15), bg='black', fg='red')
        self.timer = tk.Label(self, text=f'000', font=("Courier", 15), bg='black', fg='red')
        self.best_label = tk.Label(self, text = 'Best Time:', font=('Courier', 10))
        self.best_time = tk.Label(self, text=f'{best_times[self.parent.size]:03}', font=('Courier', 10))
        self.bomb_label.pack(side='left', padx=2)
        self.best_label.pack(side='left', padx=1)
        self.best_time.pack(side='left', padx=1)
        self.timer.pack(side='left', padx=2)

class Board:

    def __init__(self, size):
        self.size = size
        self.grid = [[None]*size for i in range(size)]

    def __getitem__(self, key):
        return self.grid[key]

class TileInfo():

    def __init__(self, type, x, y):
        self.type = type
        self.x = x
        self.y = y
        self.flagged = False
        self.clicked = False

class TileButton(tk.Button):

    def __init__(self, game, x, y):
        super().__init__(game)
        self.game = game
        self.x = x
        self.y = y
        self.bind('<Button-1>', self.left_click)
        self.bind('<Button-3>', self.right_click)
        self.bind('<Double-Button-1>', self.double_left_click)

    def left_click(self, event):
        self.game.event_handler('left_click', self.x, self.y)

    def right_click(self, event):
        self.game.event_handler('right_click', self.x, self.y)

    def double_left_click(self, event):
        self.game.event_handler('double_left_click', self.x, self.y)

root = tk.Tk()
app = Application(root)
app.mainloop()