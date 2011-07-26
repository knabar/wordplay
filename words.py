from __future__ import with_statement
import itertools
import datetime



def load_words():
    with open('words.txt') as data:
        words = dict()
        for word in data.readline().split():
            words[word] = True
            for prefix in range(2, len(word)):
                words.setdefault(word[:prefix], False)
    return words

WORDS = load_words()


class Board(object):

    def __init__(self, board=None, transpose=False):
        if board:
            self.board = board
        else:
            with open('board.txt') as data:
                self.board = map(str.strip, data.readlines())
        self.board_size = len(self.board)
        if transpose:
            self.board = [''.join(line[column] for line in self.board) for column in range(self.board_size)]


    def transposed(self):
        return Board(board=self.board, transpose=True)


    def is_first_move(self):
        return not any(map(str.isupper, self.board))


    def get_pattern(self, line, start, length, first, num_letters):

        if first:
            center = self.board_size / 2
            # needs to touch center
            if line != center or start > center or start + length < center:
                return None

        # get pattern from board
        pattern = self.board[line][start:start + length]

        # validate number of blank spaces
        used = len(filter(str.isupper, pattern))
        if (len(pattern) - used > num_letters) or (len(pattern) == used):
            return None

        if first:
            # no more checks needed
            return pattern

        # can't touch letters before or after
        if start > 0 and self.board[line][start - 1].isupper():
            return None
        if start + length < self.board_size and self.board[line][start + length].isupper():
            return None

        # validate attaching to letter
        if used > 0:
            return pattern

        # check if adjacent rows/columns have letters
        if line and filter(str.isupper, self.board[line - 1][start:start + length]):
            return pattern
        if line < self.board_size - 1 and filter(str.isupper, self.board[line + 1][start:start + length]):
            return pattern

        return None


    def get_playing_positions(self, num_letters):
        first = self.is_first_move()
        for line, start in itertools.product(range(self.board_size), range(self.board_size - 1)):
            for length in range(2, self.board_size - start):
                pattern = self.get_pattern(line, start, length, first, num_letters)
                if pattern:
                    yield line, start, pattern
    
    
    def get_words(self, tiles, pattern):
        used = len(filter(str.isupper, pattern))
        found = dict()
        
        def recurse(tiles, head, tail):
            for index, tile in enumerate(tiles):
                word = head + tile
                remaining = tail
                while True:
                    remaining = remaining[1:]
                    if remaining and remaining[0].isupper():
                        word += remaining[0]
                    else:
                        break
                check = WORDS.get(word)
                if check is None:
                    continue
                elif not tail:
                    found[word] = None
                else:
                    recurse(tiles[:index] + tiles[index + 1:], word, remaining)

        head = ''
        while pattern[0].isupper():
            head += pattern[0]
            pattern = pattern[1:]
            
        recurse(tiles, head, pattern)
        return found.keys()


    def check_cross_words(self, column, start, word):
        for line in range(start, start + len(word)):
            from_column = to_column = column
            while from_column > 0 and self.board[line][from_column - 1].isupper():
                from_column -= 1
            while to_column < self.board_size - 1 and self.board[line][to_column + 1].isupper():
                to_column += 1
            if from_column < to_column:
                check = self.board[line][from_column:column] + word[line - start] + self.board[line][column + 1:to_column + 1]
                if not WORDS.get(check):
                    return False
        return True


    def get_plays(self, tiles):
        transposed = self.transposed()
        
        for line, start, pattern in self.get_playing_positions(len(tiles)):
            for word in self.get_words(tiles, pattern):
                if transposed.check_cross_words(line, start, word):
                    # good word
                    yield line, None, start, word
        for line, start, pattern in transposed.get_playing_positions(len(tiles)):
            for word in transposed.get_words(tiles, pattern):
                if self.check_cross_words(line, start, word):
                    # good word
                    yield None, line, start, word


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
                


def get_tiles():
    tiles = []
    values = {}
    with open('tiles.txt') as data:
        for line in data.readlines():
            letter, value, quantity = line.split()
            values[letter] = int(value)
            tiles.extend([letter] * int(quantity))
    return tiles, values






    


if __name__ == "__main__":
    
    print len(WORDS), "words and prefixes"
    
    
    tiles, values = get_tiles()
    
    board = Board()
    
    board.play(None, 7, 4, 'HELLO')
    board.play(4, None, 7, 'HAT')
    
    start = datetime.datetime.now()
    
    plays = list(board.get_plays('ANDREAS'))
    
    print datetime.datetime.now() - start
    
    for play in plays:
        print play
    exit()
