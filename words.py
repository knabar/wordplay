from __future__ import with_statement
import itertools
import re
from random import shuffle


def load_words():
    with open('words.txt') as data:
        words = dict()
        for word in data.readline().split():
            words[word] = True
            for prefix in range(1, len(word)):
                words.setdefault(word[:prefix], False)
    return words

WORDS = load_words()


def load_tiles():
    tiles = []
    values = {}
    with open('tiles.txt') as data:
        for line in data.readlines():
            letter, value, quantity = line.split()
            values[letter] = int(value)
            if letter.isupper():
                values[letter.lower()] = 0
            tiles.extend([letter] * int(quantity))
    return tiles, values

TILES, VALUES = load_tiles()


class Score(object):
    
    def __init__(self, board):
        self.score = 0
        self.multiplier = 1
        self.cross_score = 0
        self.board = board
        
    def copy(self):
        dup = Score(self.board)
        dup.score = self.score
        dup.multiplier = self.multiplier
        dup.cross_score = self.cross_score
        return dup
    
    def play_tile(self, line, column, tile=None):
        field = self.board.board[line][column]
        if field.isalpha():
            self.score += VALUES[field]
        else:
            tile_multiplier = 1
            if field == '.':
                pass
            elif field == ':':
                tile_multiplier = 2
            elif field == '!':
                tile_multiplier = 3
            elif field == '2':
                self.multiplier *= 2
            elif field == '3':
                self.multiplier *= 3
            self.score += VALUES[tile] * tile_multiplier
    
    def add_cross_score(self, cross_score):
        self.cross_score += cross_score
    
    def get_word_score(self):
        return self.score * self.multiplier + self.cross_score


class Play(object):
    
    def __init__(self, line, column, start, word, score=None, pattern=None):
        self.line = line
        self.column = column
        self.start = start
        self.word = word
        self.score = score
        self.pattern = pattern
    
    def used_tiles(self):
        for letter, place in zip(self.word, self.pattern):
            if not place.isalpha():
                yield letter if letter.isupper() else '*'
    
    def __repr__(self):
        return ("Play(%s,%s,%s,'%s',%s,'%s')" %
                (self.line, self.column, self.start,
                 self.word, self.score, self.pattern))
    
    def show(self):
        if self.column is None:
            print ("Across at line %d column %d play %s for %d points" %
                   (self.line + 1, self.start + 1, self.word, self.score))
        else:
            print ("  Down at line %d column %d play %s for %d points" %
                   (self.start + 1, self.column + 1, self.word, self.score))
            
            
class Board(object):

    def __init__(self, board=None, master=None):
        if board:
            self.board = board
        else:
            with open('board.txt') as data:
                self.board = [line.strip() for line in data.readlines()]
        self.board_size = len(self.board)
        
        if master:
            self.transposed = master
            self.board = [''.join(line[column] for line in self.board)
                          for column in range(self.board_size)]
        else:
            self.transposed = Board(board=self.board, master=self)


    def is_first_move(self):
        return not any(any(char.isalpha() for char in line)
                       for line in self.board)

    def get_pattern(self, line, start, length, first, num_letters):

        if first:
            center = self.board_size / 2
            # needs to touch center
            if line != center or start > center or start + length - 1 < center:
                return None

        # get pattern from board
        pattern = self.board[line][start:start + length]

        # validate number of blank spaces
        used = len(filter(str.isalpha, pattern))
        if (len(pattern) - used > num_letters) or (len(pattern) == used):
            return None

        if first:
            # no more checks needed
            return pattern

        # can't touch letters before or after
        if start > 0 and self.board[line][start - 1].isalpha():
            return None
        if (start + length < self.board_size and
            self.board[line][start + length].isalpha()):
            return None

        # validate attaching to letter
        if used > 0:
            return pattern

        # check if adjacent rows/columns have letters
        if ((line > 0 and
             filter(str.isalpha, self.board[line - 1][start:start + length])) or
            (line < self.board_size - 1 and
             filter(str.isalpha, self.board[line + 1][start:start + length]))):
            return pattern

        return None


    def get_playing_positions(self, num_letters):
        first = self.is_first_move()
        for line, start in itertools.product(range(self.board_size),
                                             range(self.board_size - 1)):
            for length in range(2, self.board_size - start):
                pattern = self.get_pattern(line, start, length,
                                           first, num_letters)
                if pattern:
                    yield line, start, pattern
    
    
    
    def check_cross_word(self, line, column, tile):
        from_column = to_column = column
        while from_column > 0 and self.board[line][from_column - 1].isalpha():
            from_column -= 1
        while (to_column + 1 < self.board_size and
               self.board[line][to_column + 1].isalpha()):
            to_column += 1
        if from_column == to_column:
            return 0
        check = (self.board[line][from_column:column] + tile +
                 self.board[line][column + 1:to_column + 1])
        if not WORDS.get(check.upper()):
            return -1
        score = Score(self)
        for col in range(from_column, column):
            score.play_tile(line, col)
        score.play_tile(line, column, tile)
        for col in range(column + 1, to_column + 1):
            score.play_tile(line, col)
        return score.get_word_score()
    
    
    def get_words(self, line, start, tiles, pattern):
        found = dict()
        invalid_cross_tiles = dict()
        
        def recurse(tiles, head, tail, score):
            for index, tile in enumerate(tiles):
                options = tile if tile != '*' else filter(str.islower,
                                                          VALUES.keys())
                for option in options:
                    # check if we tried this letter before in this position
                    if option in invalid_cross_tiles.setdefault(len(head), []):
                        continue
                    
                    word = head + option
                    new_score = score.copy()
                    new_score.play_tile(line, start + len(head), option)
                    
                    # check cross words
                    column = start + len(head)
                    cross_score = self.transposed.check_cross_word(column, line,
                                                                   option)
                    if cross_score < 0:
                        # invalid, remember letter to not try again in this pos
                        invalid_cross_tiles[len(head)].append(option)
                        continue
                    else:
                        new_score.add_cross_score(cross_score)
                    
                    remaining = tail
                    while True:
                        remaining = remaining[1:]
                        if remaining and remaining[0].isalpha():
                            new_score.play_tile(line, start + len(word))
                            word += remaining[0]
                        else:
                            break
                    check = WORDS.get(word.upper())
                    if check is None:
                        continue
                    elif not remaining:
                        if check:
                            found[word] = new_score.get_word_score()
                    else:
                        recurse(tiles[:index] + tiles[index + 1:], word,
                                remaining, new_score)

        head = ''
        score = Score(self)
        while pattern[0].isalpha():
            score.play_tile(line, start + len(head))
            head += pattern[0]
            pattern = pattern[1:]
            
        recurse(tiles, head, pattern, score)
        return found.iteritems()


    def get_plays(self, tiles):
        for line, start, pattern in self.get_playing_positions(len(tiles)):
            for word, score in self.get_words(line, start, tiles, pattern):
                yield Play(line, None, start, word, score, pattern)
        for line, start, pattern in \
            self.transposed.get_playing_positions(len(tiles)):
            for word, score in \
                self.transposed.get_words(line, start, tiles, pattern):
                yield Play(None, line, start, word, score, pattern)


    def show(self):
        print re.sub('[.:!23]', ' ', '\n'.join(self.board))


    def play(self, play):     #line, column, start, word):
        if play.column is None:
            self.board[play.line] = (self.board[play.line][:play.start] +
                play.word +
                self.board[play.line][play.start + len(play.word):])
        else:            
            for index, line in enumerate(range(play.start, play.start +
                                               len(play.word))):
                self.board[line] = (self.board[line][:play.column] +
                                    play.word[index] +
                                    self.board[line][play.column + 1:])
        
        self.transposed = Board(board=self.board, master=self)


class Player(object):
    
    def __init__(self, drawpile):
        self.score = 0
        self.tiles = ''
        self.drawpile = drawpile
        self.draw_tiles()
        
    def draw_tiles(self):
        shuffle(self.drawpile)
        while len(self.tiles) < 7 and self.drawpile:
            self.tiles += self.drawpile.pop()
    
    def play(self, board):
        plays = sorted(board.get_plays(self.tiles),
                       key=lambda play: play.score, reverse=True)
        if not plays:
            self.tiles = ''
        else:
            board.play(plays[0])
            self.score += plays[0].score
            plays[0].show()
            for tile in plays[0].used_tiles():
                self.tiles = self.tiles.replace(tile, '', 1)
        self.draw_tiles()
        

def play_game():
    drawpile = TILES[:]
    board = Board()
    player1 = Player(drawpile)
    player2 = Player(drawpile)
    while True:    
        print "Player 1: %d %s" % (player1.score, player1.tiles)
        print "Player 2: %d %s" % (player2.score, player2.tiles)
        print "Remaining: ", ''.join(sorted(drawpile))
        print "-" * 70
        if player1.tiles and player2.tiles:
            player1.play(board)
            player2.play(board)
        else:
            break
    board.show()
    

if __name__ == "__main__":
    play_game()
