import tkinter as tk
import random
import time
import glob, os, sys

class Application(tk.Frame):

    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.game = Game(self.root)
        # self.create_initial_interface()

    def create_initial_interface(self):
        self.label = tk.Label(self.root, text='Board Size')
        self.drop_down = tk.Listbox(self.root)
        self.drop_down.insert('small')
        self.drop_down.insert('medium')
        self.drop_down.insert('large')

class Game(tk.Frame):

    def __init__(self, root=None, size=18):
        super().__init__(root)
        self.root = root
        self.size = size
        self.bombs = 0
        self.flags = 0
        self.found_tiles = 0
        self.is_over = False
        self.start = time.time()
        self.images = self.get_images()
        self.create_interface()

    def create_interface(self):
        self.root.title('Minesweeper')
        self.bomb_label = tk.Label(text='', font=("Courier", 15), bg='black', fg='red')
        self.timer = tk.Label(text='', font=("Courier", 15), bg='black', fg='red')
        self.bomb_label.grid(row=0, column=0, columnspan=3)
        self.timer.grid(row=0, column=self.size-3, columnspan=3)
        self.buttons = Board(self.size)
        self.populate_board()
        self.update_bombs()
        self.update_timer()

    def populate_board(self):
        BOMB_FREQUENCY = 0.15
        for x in range(self.size):
            for y in range(self.size):
                if random.random() < BOMB_FREQUENCY:
                    self.buttons[x][y] = Mine(self, x, y)
                    self.buttons[x][y].grid(row=x+1, column=y)
                    self.bombs +=1
                else:
                    self.buttons[x][y] = Empty(self, x, y)
                    self.buttons[x][y].grid(row=x+1, column=y)

    def update_bombs(self):
        if self.is_over:
            return
        num = self.bombs - self.flags
        self.bomb_label['text'] = f'{num:03}'

    def update_timer(self):
        if self.is_over:
            return
        elapsed = int(time.time() - self.start)
        self.timer['text'] = f'{elapsed:03}'
        self.root.after(1000, self.update_timer)

    def get_images(self):
        os.chdir(sys.path[0])
        image_dic = {}
        for file in glob.glob('*.png'):
            print(file)
            key = file.split('.')[0]
            image_dic[key] = tk.PhotoImage(file=file)
        return image_dic


    def check(self, x, y):
        if self.buttons[x][y].is_flagged:
            return
        if self.buttons[x][y].clicked:
            return

        if type(self.buttons[x][y]).__name__ == 'Mine':
            self.buttons[x][y]['image'] = self.images['Mine']
            self.trigger_loss()
        elif type(self.buttons[x][y]).__name__ == 'Empty':
            self.buttons[x][y].clicked = True
            adj_bombs = self.adjacent_bombs(x, y)
            self.found_tiles +=1
            if adj_bombs != 0:
                self.buttons[x][y]['image'] = self.images[str(adj_bombs)]
            elif adj_bombs == 0:
                self.buttons[x][y]['image'] = self.images['Pressed']
                for i in range(max(0, x-1), min(self.size-1, x+1)+1):
                    for j in range(max(0, y-1), min(self.size-1, y+1)+1):
                        if type(self.buttons[x][y]).__name__ == 'Empty' and not self.buttons[i][j].clicked:
                            self.check(i, j)
        if self.found_tiles == self.size**2 - self.bombs:
            self.trigger_win()

    def flag(self, x, y):
        if self.buttons[x][y].is_flagged:
            self.flags +=1
        else:
            self.flags -=1
        self.update_bombs()

    def explore(self, x, y):
        if self.buttons[x][y].is_flagged:
            return
        if self.adjacent_bombs(x, y) == self.adjacent_flags(x, y):
            for i in range(max(0, x-1), min(self.size-1, x+1)+1):
                for j in range(max(0, y-1), min(self.size-1, y+1)+1):
                    if self.buttons[i][j]['bg']=='SystemButtonFace' and not self.buttons[i][j].is_flagged:
                        self.check(i, j)

    def adjacent_bombs(self, x, y):
        count = 0
        for i in range(max(0, x-1), min(self.size-1, x+1)+1):
            for j in range(max(0, y-1), min(self.size-1, y+1)+1):
                if type(self.buttons[i][j]).__name__ == 'Mine':
                    count +=1
        return count

    def adjacent_flags(self, x, y):
        count = 0
        for i in range(max(0, x-1), min(self.size-1, x+1)+1):
            for j in range(max(0, y-1), min(self.size-1, y+1)+1):
                if self.buttons[i][j].is_flagged:
                    count +=1
        return count

    def button_format(self, arg):
        switcher = {
            0: ['#000000'],
            1: ['#0100fe'],
            2: ['#017f01'],
            3: ['#fe0000'],
            4: ['#010080'],
            5: ['#810102'],
            6: ['#008081'],
            7: ['#000000'],
            8: ['#808080'],
        }
        return switcher.get(arg, 'INVALID NUMBER')

    def trigger_loss(self):
        self.is_over = True
        self.popup = tk.Toplevel(self.root)
        self.message = tk.Label(self.popup, text='You lose. Sorry :/')
        self.message.grid(row=0, column=0, columnspan=5)
        self.exit_button = tk.Button(self.popup, text='exit', command=self.popup.destroy)
        self.exit_button.grid(row=1, column=0, columnspan=5)

    def trigger_win(self):
        self.is_over = True
        pop_up = tk.Tk()
        win_label = tk.Label(text='You did it!!!')
        win_label.grid()

class Board:

    def __init__(self, size):
        self.size = size
        self.grid = [[None]*size for i in range(size)]

    def __getitem__(self, key):
        return self.grid[key]

class Tile(tk.Button):

    def __init__(self, game, x, y):
        super().__init__(game.root, image = game.images['Unpressed'], height=20, width=20, borderwidth=0)
        self.game = game
        self.x = x
        self.y = y
        self.is_flagged = False
        self.clicked = False
        self.bind('<Button-1>', self.left_click)
        self.bind('<Button-3>', self.right_click)
        self.bind('<Double-Button-1>', self.double_left_click)

    def left_click(self, event):
        self.game.check(self.x, self.y)

    def right_click(self, event):
        if self.clicked:
            return
        if self.is_flagged:
            self['image'] = self.game.images['Unpressed']
            self.is_flagged = False
        else:
            self['image'] = self.game.images['Flag']
            self.is_flagged = True
        self.game.flag(self.x, self.y)

    def double_left_click(self, event):
        self.game.explore(self.x, self.y)

class Mine(Tile):
    pass

class Empty(Tile):
    pass

root = tk.Tk()
app = Application(root)
app.mainloop()