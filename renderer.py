from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_SIZE = 1600
BOARD_SIZE = 1280

BOARD_X = (OUTPUT_SIZE - BOARD_SIZE) // 2
BOARD_Y = 190

SQUARE_SIZE = BOARD_SIZE // 8

ASSET_DIR = (
    Path(__file__).resolve().parent
    / "assets"
    / "checkerboard"
    / "standard"
)


# ============================================================
# COLORS
# ============================================================

BACKGROUND = "#151515"
TEXT = "#FFFFFF"


# ============================================================
# FONTS
# ============================================================

def get_font(size):

    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]

    for candidate in candidates:

        path = Path(candidate)

        if path.exists():

            return ImageFont.truetype(
                str(path),
                size
            )

    return ImageFont.load_default()


TITLE_FONT = get_font(56)
MOVE_FONT = get_font(42)
SQUARE_FONT = get_font(28)


# ============================================================
# ASSETS
# ============================================================

def load_asset(filename):

    path = ASSET_DIR / filename

    if not path.exists():

        raise FileNotFoundError(
            f"CheckerBoard asset not found: {path}"
        )

    return Image.open(path).convert("RGBA")


LIGHT_SQUARE = load_asset("light.bmp")
DARK_SQUARE = load_asset("dark.bmp")

BLACK_MAN = load_asset("bm.bmp")
BLACK_KING = load_asset("bk.bmp")

WHITE_MAN = load_asset("wm.bmp")
WHITE_KING = load_asset("wk.bmp")


# ============================================================
# BOARD MAPPING
# ============================================================

def square_to_row_col(square):
    """
    Convert English draughts square number 1-32
    into an 8x8 board row/column.
    """

    square = int(square)

    if not 1 <= square <= 32:

        raise ValueError(
            f"Invalid checker square: {square}"
        )

    index = square - 1

    row = index // 4
    position = index % 4

    if row % 2 == 0:

        col = position * 2 + 1

    else:

        col = position * 2

    return row, col


# ============================================================
# BOARD
# ============================================================

def draw_board(image):

    for row in range(8):

        for col in range(8):

            x = BOARD_X + col * SQUARE_SIZE
            y = BOARD_Y + row * SQUARE_SIZE

            if (row + col) % 2 == 0:

                tile = LIGHT_SQUARE

            else:

                tile = DARK_SQUARE

            tile = tile.resize(
                (
                    SQUARE_SIZE,
                    SQUARE_SIZE
                ),
                Image.Resampling.LANCZOS
            )

            image.paste(
                tile,
                (x, y)
            )


# ============================================================
# SQUARE NUMBERS
# ============================================================

def draw_square_numbers(image):

    draw = ImageDraw.Draw(image)

    for square in range(1, 33):

        row, col = square_to_row_col(square)

        x = BOARD_X + col * SQUARE_SIZE
        y = BOARD_Y + row * SQUARE_SIZE

        text = str(square)

        padding = 12

        text_x = x + padding
        text_y = y + padding

        if (row + col) % 2 == 0:

            fill = "#333333"

        else:

            fill = "#EEEEEE"

        draw.text(
            (text_x, text_y),
            text,
            font=SQUARE_FONT,
            fill=fill
        )


# ============================================================
# BOARD FEN
# ============================================================

def get_board_fen(board):
    """
    Obtain the current FEN from the pydraughts board.
    """

    fen = getattr(
        board,
        "fen",
        None
    )

    if callable(fen):

        fen = fen()

    if fen is None:

        raise AttributeError(
            "The draughts Board does not expose a FEN position."
        )

    return str(fen)


def parse_fen_pieces(fen):
    """
    Parse American/English draughts FEN.

    Example:

        B:W21,22,23,K24:B1,2,3,K4

    Returns:

        {
            21: ("white", False),
            22: ("white", False),
            24: ("white", True),
            1: ("black", False),
            4: ("black", True),
        }
    """

    if not fen:

        return {}

    sections = fen.split(":")

    pieces = {}

    for section in sections:

        section = section.strip()

        if not section:

            continue

        upper = section.upper()

        if upper.startswith("W"):

            color = "white"
            data = section[1:]

        elif upper.startswith("B"):

            color = "black"
            data = section[1:]

        else:

            continue

        data = data.strip()

        if not data:

            continue

        data = data.lstrip(",")

        for token in data.split(","):

            token = token.strip()

            if not token:

                continue

            king = False

            if token.upper().startswith("K"):

                king = True
                token = token[1:]

            match = re.fullmatch(
                r"\d+",
                token
            )

            if not match:

                continue

            square = int(token)

            if 1 <= square <= 32:

                pieces[square] = (
                    color,
                    king
                )

    return pieces


# ============================================================
# PIECES
# ============================================================

def draw_pieces(image, board):
    """
    Draw pieces from the current pydraughts board position.
    """

    fen = get_board_fen(board)

    pieces = parse_fen_pieces(fen)

    for square, piece in pieces.items():

        color, king = piece

        row, col = square_to_row_col(square)

        x = BOARD_X + col * SQUARE_SIZE
        y = BOARD_Y + row * SQUARE_SIZE

        if color == "black":

            if king:

                asset = BLACK_KING

            else:

                asset = BLACK_MAN

        else:

            if king:

                asset = WHITE_KING

            else:

                asset = WHITE_MAN

        asset = asset.resize(
            (
                SQUARE_SIZE,
                SQUARE_SIZE
            ),
            Image.Resampling.LANCZOS
        )

        image.alpha_composite(
            asset,
            (x, y)
        )


# ============================================================
# TEXT INFORMATION
# ============================================================

def draw_text_information(
    image,
    last_move,
    move_number
):

    draw = ImageDraw.Draw(image)

    if move_number is not None:

        if last_move:

            move_text = (
                f"{move_number}. "
                f"{last_move}"
            )

        else:

            move_text = str(move_number)

        bbox = draw.textbbox(
            (0, 0),
            move_text,
            font=MOVE_FONT
        )

        text_width = bbox[2] - bbox[0]

        text_x = (
            OUTPUT_SIZE - text_width
        ) // 2

        text_y = 105

        draw.text(
            (text_x, text_y),
            move_text,
            font=MOVE_FONT,
            fill=TEXT
        )

    else:

        title = "CHECKERS"

        bbox = draw.textbbox(
            (0, 0),
            title,
            font=TITLE_FONT
        )

        text_width = bbox[2] - bbox[0]

        text_x = (
            OUTPUT_SIZE - text_width
        ) // 2

        text_y = 95

        draw.text(
            (text_x, text_y),
            title,
            font=TITLE_FONT,
            fill=TEXT
        )


# ============================================================
# MAIN RENDERER
# ============================================================

def render_position(
    board,
    output_path,
    last_move=None,
    move_number=None
):

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    image = Image.new(
        "RGBA",
        (
            OUTPUT_SIZE,
            OUTPUT_SIZE
        ),
        BACKGROUND
    )

    # Board
    draw_board(image)

    # Square numbers
    draw_square_numbers(image)

    # Pieces
    draw_pieces(
        image,
        board
    )

    # Move information only.
    # No arrows or move highlighting.
    draw_text_information(
        image,
        last_move,
        move_number
    )

    image.convert("RGB").save(
        output_path,
        "PNG",
        optimize=True
    )