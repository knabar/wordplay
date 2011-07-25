from __future__ import with_statement
import itertools



class Board(object):

    def __init__(self):
        with open('board.txt') as data:
            self.board = map(str.strip, data.readlines())
        self.board_size = len(self.board)


    def is_first_move(self):
        return not any(map(str.isupper, self.board))


    def get_pattern(self, line, column, start, length, first, num_letters):

        def get_line_pattern(line, start, length):
            return self.board[line][start:start + length]

        def get_column_pattern(column, start, length):
            return ''.join(map(lambda col: col[column],
                               self.board[start:start + length]))

        if first:
            center = self.board_size / 2
            # needs to touch center
            if not ((line == center or column == center) and (
                        start <= center and start + length >= center
                    )):
                return None

        # get pattern from board
        if column is None:
            pattern = get_line_pattern(line, start, length)
        else:
            pattern = get_column_pattern(column, start, length)

        # validate number of blank spaces
        used = len(filter(str.isupper, pattern))
        if (len(pattern) - used > num_letters) or (len(pattern) == used):
            return None

        if first:
            # no more checks needed
            return pattern

        # validate attaching to letter
        if used > 0:
            return pattern

        # can't touch letters before or after
        if column is None:
            if start > 0:
                if self.board[line][start - 1].isupper():
                    return None
            if start + length < self.board_size:
                if self.board[line][start + length].isupper():
                    return None
        else:
            if start > 0:
                if self.board[start - 1][column].isupper():
                    return None
            if start + length < self.board_size:
                if self.board[start + length][column].isupper():
                    return None

        # check if adjacent rows/columns have letters

        if column is None:
            if line > 0:
                if filter(str.isupper, get_line_pattern(line - 1, start, length)):
                    return pattern
            if line < self.board_size - 1:
                if filter(str.isupper, get_line_pattern(line + 1, start, length)):
                    return pattern
        else:
            if column > 0:
                if filter(str.isupper, get_column_pattern(column - 1, start, length)):
                    return pattern
            if column < self.board_size - 1:
                if filter(str.isupper, get_column_pattern(column + 1, start, length)):
                    return pattern

        return None


    def get_playing_positions(self, num_letters):
        options = []
        first = self.is_first_move()

        for line in range(self.board_size):
            for start in range(self.board_size - 1):
                for length in range(2, self.board_size - start):
                    pattern = self.get_pattern(line, None, start, length, first, num_letters)
                    if pattern:
                        options.append((line, None, start, length, pattern))

        for column in range(self.board_size):
            for start in range(self.board_size - 1):
                for length in range(2, self.board_size - start):
                    pattern = self.get_pattern(None, column, start, length, first, num_letters)
                    if pattern:
                        options.append((None, column, start, length, pattern))

        return options


    def show(self):
        for line in self.board:
            print line


    def play(self, line, column, start, word):
        if column is None:
            self.board[line] = (self.board[line][:start] +
                                word +
                                self.board[line][start + len(word):])
        else:
            for index, line in enumerate(range(start, start + len(word))):
                self.board[line] = (self.board[line][:column] +
                                    word[index] +
                                    self.board[line][column + 1:])


def load_words():
    with open('words.txt') as data:
        return dict((word, None) for word in data.readline().split())


def get_tiles():
    tiles = []
    values = {}
    with open('tiles.txt') as data:
        for line in data.readlines():
            letter, value, quantity = line.split()
            values[letter] = int(value)
            tiles.extend([letter] * int(quantity))
    return tiles, values


words = load_words()

def get_words(tiles, pattern):
    used = len(filter(str.isupper, pattern))
    found = dict()
    for perm in itertools.permutations(tiles, len(pattern) - used):
        result = []
        chars = list(perm)
        for char in pattern:
            result.append(char if char.isupper() else chars.pop())
        word = ''.join(result)
        if words.has_key(word):
            found[word] = None
    return found.keys()



if __name__ == "__main__":
    
    
    
    tiles, values = get_tiles()
    
    board = Board()
    
    board.play(None, 7, 4, 'HELLO')
    board.play(4, None, 7, 'HAT')
    
    options = board.get_playing_positions(7)
    
    board.show()
   
     
    print "Calculating words..."
    for line, column, start, length, pattern in options:
        results = get_words('ANDREAS', pattern)
    
    print "Done"