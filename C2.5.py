from random import randint, choice


class BoardDeploymentError(Exception):
    pass


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Dot(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f'Dot(x={self.x},y={self.y})'


class Ship:
    def __init__(self, ship_head, ship_size, orientation):
        self.lives = ship_size
        self.ship_head = ship_head
        self.ship_size = ship_size
        # H -горизонтальное, V - вертикальное направление
        self.orientation = orientation

    @property
    def coordinates(self):
        # Возвращает список с координатами (Dot объектами)
        ship_coords = []
        for i in range(self.ship_size):
            x_1 = self.ship_head.x
            y_1 = self.ship_head.y
            if self.orientation == 'V':
                x_1 += i
            if self.orientation == 'H':
                y_1 += i
            ship_coords.append(Dot(x_1, y_1))

        return ship_coords


class Board:
    def __init__(self, hidden, size=6):
        self.size = size
        self.hidden = hidden
        self.ships = []
        self.occupied_grid = []
        self.casualties = 0

        self.board = [[f'{"O":^3}'] * (self.size + 1) for _ in range(self.size + 1)]

    def __str__(self):
        # Возвращает строку с полем
        self.field = ''
        self.board[0] = [f'{_:^3d}' for _ in range(self.size + 1)]
        self.board[0][0] = 'ᵪ\ʸ'
        for i in range(1, self.size + 1):
            self.board[i][0] = f'{i:^3}'

        for _ in self.board:
            if not self.hidden:
                self.field += '\n' + ' | '.join(_) + ' | '
            else:
                self.field += '\n' + ' | '.join(_).replace(' ■ ', ' O ') + ' | '
        return self.field

    @property
    def occupied(self):
        return self.occupied_grid

    def out(self, coord):
        return not ((0 < coord.x <= self.size) and (0 < coord.y <= self.size))

    def repeat(self, coord):
        return coord in self.occupied

    def ship_deployment(self, ship):
        # Принимает объект корабля. Ничего не возвращает.
        for part in ship.coordinates:
            if self.out(part) or self.repeat(part):
                raise BoardDeploymentError()
        for part in ship.coordinates:
            self.board[part.x][part.y] = ' ■ '
            self.occupied.append(part)

        self.ships.append(ship)
        self.shadow(ship.coordinates, deploy=True)

    def shadow(self, ship_coords, deploy=False):
        # Принимает список (ship_coords) с объектами Dot
        shadow_points = [Dot(-1, -1), Dot(-1, 0), Dot(-1, 1),
                         Dot(0, -1, ), Dot(0, 0), Dot(0, 1),
                         Dot(1, -1, ), Dot(1, 0), Dot(1, 1)]

        for d in ship_coords:
            for p in shadow_points:
                s_p = d + p
                if not self.out(s_p) and not self.repeat(s_p):
                    self.occupied.append(s_p)
                    if not deploy:
                        self.board[s_p.x][s_p.y] = ' * '

    def hit_check(self, shot):
        # Проверка на попадание.
        if self.out(shot):
            print('Выстрел за пределы поля, пожалуйста повторите...')
            return 'Repeat'
        if self.repeat(shot):
            print('Эта координата уже указывалась...')
            return 'Repeat'
        self.occupied.append(shot)
        for ship in self.ships:
            if shot in ship.coordinates:
                ship.lives -= 1
                self.board[shot.x][shot.y] = ' X '
                if ship.lives == 0:
                    print('Корабль поврежден!')
                    self.casualties += 1
                    self.shadow(ship.coordinates, deploy=False)
                    return 'Destroyed'
                else:
                    print('Корабль уничтожен!')
                    return 'Damaged'
        print('Промах!')
        self.board[shot.x][shot.y] = ' * '
        return 'Missed'

    def board_clear(self):
        self.occupied.clear()


class Player:
    def __init__(self, first_board, second_board):
        self.first_board = first_board
        self.second_board = second_board


class User(Player):
    def fire_request(self):
        # Получение координат выстрела от пользователя
        while True:
            try:
                f_x, f_y = input('введите координаты выстрела (x y):').split()
                f_x, f_y = int(f_x), int(f_y)
            except ValueError:
                print('Некорректный ввод, повторите пожалуйста')
            else:
                return Dot(f_x, f_y)

    def shooting(self):
        one_more_shot = False
        shot = self.fire_request()
        result = self.second_board.hit_check(shot)
        if result == 'Missed' or result == 'Destroyed':
            one_more_shot = False
        elif result == 'Damaged' or 'Repeat':
            one_more_shot = True
        return one_more_shot


class Ai(Player):
    def __init__(self, first_board, second_board):
        super().__init__(first_board, second_board)
        self.shooting_list = self.aiming_grid()
        self.recommended = []

    def aiming_grid(self):
        shooting_grid = []
        for col in range(1, self.first_board.size + 1):
            for row in range(1, self.first_board.size + 1):
                shooting_grid.append(Dot(col, row))
        return shooting_grid

    def fire_request(self):
        aim = choice(self.shooting_list)
        self.shooting_list.remove(aim)
        return aim

    def shooting(self):
        one_more_shot = False
        if self.recommended:
            shot = choice(self.recommended)
            print('Пытаюсь добить...')
            print(f'Целюсь в {shot}...')
            try:
                self.recommended.remove(shot)
                self.shooting_list.remove(shot)
            except ValueError:
                pass
        else:
            shot = self.fire_request()

        print(f'Стреляю в {shot}...')
        result = self.second_board.hit_check(shot)

        if result == 'Destroyed':
            one_more_shot = False
            self.recommended.clear()

        elif result == 'Missed':
            one_more_shot = False

        elif result == 'Damaged':
            one_more_shot = True
            precision_shooting_list = [Dot(shot.x - 1, shot.y), Dot(shot.x + 1, shot.y),
                                       Dot(shot.x, shot.y - 1), Dot(shot.x, shot.y + 1)]
            self.recommended.extend(precision_shooting_list)
        else:
            one_more_shot = True

        return one_more_shot


class Game:
    def __init__(self, size=6):
        self.size = size
        my_board = self.random_board()
        enemy_board = self.random_board()
        enemy_board.hidden = True

        self.ai = Ai(enemy_board, my_board)
        self.player = User(my_board, enemy_board)

    def greetings(self):
        print('☻' * 35)
        print('  Добро пожаловать в Морской бой!')
        print(' ☼☼☼ Введите (X Y) для выстрела ☼☼☼')
        print('☻' * 35)

    @property
    def turn_selection(self):
        return randint(0, 1)

    def board_creation(self):
        ship_sizes = [3, 2, 2, 1, 1, 1, 1]
        board = Board(size=self.size, hidden=False)
        tries = 0

        orientation = randint(0, 1)
        direction = 'V' if orientation == 0 else 'H'
        for s_s in ship_sizes:
            while True:
                if tries > 2000:
                    return None
                tries += 1
                ship = Ship(Dot(randint(1, self.size), (randint(1, self.size))), s_s, direction)
                try:
                    board.ship_deployment(ship)
                    break
                except:
                    pass

        board.board_clear()
        return board

    def random_board(self):
        board = None
        while board is None:
            board = self.board_creation()
        return board

    def loop(self):

        self.greetings()
        turn = self.turn_selection
        if turn % 2 == 0:
            print("Игрок ходит первым:")
        else:
            print("Компьютер ходит первым:")

        while True:
            if self.player.first_board.casualties == 7:
                print('Победил компьютер')
                print('☻' * 20)
                break
            if self.player.second_board.casualties == 7:
                print('Победил игрок')
                print('☻' * 20)
                break
            print("Доска игрока:")
            print(self.player.first_board)
            print()
            print("Доска компьютера:")
            print(self.ai.first_board)
            print()


            if turn % 2 == 0:
                print("Ход игрока:")
                extra_turn = self.player.shooting()
                if extra_turn:
                    turn -= 1
            else:
                print("Ход компьютера:")
                extra_turn = self.ai.shooting()
                if extra_turn:
                    turn -= 1
            turn += 1
        print("Доска игрока:")
        print(self.player.first_board)
        print("Доска компьютера:")
        print(self.ai.first_board)


g = Game()
g.loop()
