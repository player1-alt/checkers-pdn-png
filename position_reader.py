from pathlib import Path
import re

from draughts import Board


# ============================================================
# POSITION FILE FORMAT
# ============================================================
#
# [POSITION]
#
# WHITE:
# 18 19 K22
#
# BLACK:
# 10 11 21
#
# TURN:
# WHITE
#
# [SOLUTION]
#
# 22-18 11-15 18-14
#
# ============================================================


class PositionFileError(Exception):
    """Raised when a position file is invalid."""


# ============================================================
# PARSING
# ============================================================

def _clean_lines(text):
    """
    Remove blank lines and comments.

    Comments begin with #.
    """

    lines = []

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if "#" in line:
            line = line.split("#", 1)[0].strip()

        if line:
            lines.append(line)

    return lines


def _parse_piece_list(text, color):
    """
    Parse:

        18 19 K22

    into:

        [(18, False), (19, False), (22, True)]
    """

    pieces = []

    if not text.strip():
        return pieces

    tokens = text.replace(",", " ").split()

    for token in tokens:

        token = token.strip().upper()

        king = False

        if token.startswith("K"):
            king = True
            token = token[1:]

        if not token.isdigit():
            raise PositionFileError(
                f"Invalid {color} piece: '{token}'"
            )

        square = int(token)

        if not 1 <= square <= 32:
            raise PositionFileError(
                f"Invalid square {square}. "
                f"Checker squares must be 1-32."
            )

        pieces.append((square, king))

    return pieces


def _check_duplicate_squares(white_pieces, black_pieces):

    occupied = {}

    for square, king in white_pieces:

        if square in occupied:
            raise PositionFileError(
                f"Square {square} contains more than one piece."
            )

        occupied[square] = "WHITE"

    for square, king in black_pieces:

        if square in occupied:
            raise PositionFileError(
                f"Square {square} contains both WHITE and BLACK pieces."
            )

        occupied[square] = "BLACK"


def _build_fen(
    turn,
    white_pieces,
    black_pieces
):
    """
    Build an English/American checkers FEN.

    Example:

        W:W18,19,K22:B10,11,21
    """

    white_tokens = []

    for square, king in white_pieces:

        if king:
            white_tokens.append(f"K{square}")
        else:
            white_tokens.append(str(square))

    black_tokens = []

    for square, king in black_pieces:

        if king:
            black_tokens.append(f"K{square}")
        else:
            black_tokens.append(str(square))

    white_part = ",".join(
        white_tokens
    )

    black_part = ",".join(
        black_tokens
    )

    return (
        f"{turn}:"
        f"W{white_part}:"
        f"B{black_part}"
    )


# ============================================================
# POSITION OBJECT
# ============================================================

class Position:

    def __init__(
        self,
        fen,
        solution
    ):

        self.fen = fen
        self.solution = solution

    def create_board(self):

        return Board(
            variant="english",
            fen=self.fen
        )


# ============================================================
# FILE READER
# ============================================================

def load_position(filepath):
    """
    Read a human-readable checkers position file.

    Returns:
        Position
    """

    filepath = Path(filepath)

    if not filepath.exists():

        raise FileNotFoundError(
            f"Position file not found: {filepath}"
        )

    text = filepath.read_text(
        encoding="utf-8"
    )

    lines = _clean_lines(text)

    if not lines:

        raise PositionFileError(
            "Position file is empty."
        )

    # --------------------------------------------------------
    # Find sections
    # --------------------------------------------------------

    try:

        position_index = lines.index(
            "[POSITION]"
        )

    except ValueError:

        raise PositionFileError(
            "Missing [POSITION] section."
        )

    try:

        solution_index = lines.index(
            "[SOLUTION]"
        )

    except ValueError:

        raise PositionFileError(
            "Missing [SOLUTION] section."
        )

    if solution_index <= position_index:

        raise PositionFileError(
            "[SOLUTION] must come after [POSITION]."
        )

    position_lines = lines[
        position_index + 1:
        solution_index
    ]

    solution_lines = lines[
        solution_index + 1:
    ]

    # --------------------------------------------------------
    # Read POSITION section
    # --------------------------------------------------------

    white_text = None
    black_text = None
    turn = None

    current_section = None

    for line in position_lines:

        upper = line.upper()

        if upper == "WHITE:":
            current_section = "WHITE"
            white_text = ""
            continue

        if upper == "BLACK:":
            current_section = "BLACK"
            black_text = ""
            continue

        if upper.startswith("TURN:"):

            current_section = "TURN"

            value = line.split(
                ":",
                1
            )[1].strip().upper()

            turn = value

            continue

        if current_section == "WHITE":

            if white_text:
                white_text += " "

            white_text += line

        elif current_section == "BLACK":

            if black_text:
                black_text += " "

            black_text += line

        elif current_section == "TURN":

            turn = line.strip().upper()

        else:

            raise PositionFileError(
                f"Unexpected line in position section: "
                f"'{line}'"
            )

    # --------------------------------------------------------
    # Validate required fields
    # --------------------------------------------------------

    if white_text is None:

        raise PositionFileError(
            "Missing WHITE: section."
        )

    if black_text is None:

        raise PositionFileError(
            "Missing BLACK: section."
        )

    if turn is None:

        raise PositionFileError(
            "Missing TURN: section."
        )

    if turn not in ("WHITE", "BLACK"):

        raise PositionFileError(
            "TURN must be WHITE or BLACK."
        )

    # --------------------------------------------------------
    # Parse pieces
    # --------------------------------------------------------

    white_pieces = _parse_piece_list(
        white_text,
        "WHITE"
    )

    black_pieces = _parse_piece_list(
        black_text,
        "BLACK"
    )

    _check_duplicate_squares(
        white_pieces,
        black_pieces
    )

    # --------------------------------------------------------
    # Build FEN
    # --------------------------------------------------------

    fen_turn = (
        "W"
        if turn == "WHITE"
        else "B"
    )

    fen = _build_fen(
        fen_turn,
        white_pieces,
        black_pieces
    )

    # --------------------------------------------------------
    # Parse solution
    # --------------------------------------------------------

    solution_text = " ".join(
        solution_lines
    ).strip()

    solution = []

    if solution_text:

        # Accept spaces, commas and line breaks.
        tokens = re.split(
            r"[\s,]+",
            solution_text
        )

        for token in tokens:

            token = token.strip()

            if not token:
                continue

            solution.append(token)

    return Position(
        fen=fen,
        solution=solution
    )