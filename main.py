from pathlib import Path
import sys

from draughts import Board, Move

from pdn_reader import load_pdn
from position_reader import load_position, PositionFileError
from renderer import render_position


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_ROOT = Path("output")


# ============================================================
# FULL GAME
# ============================================================

def render_game(
    pdn_path,
    output_dir
):

    game = load_pdn(
        pdn_path
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    board = Board(
        variant=game.variant,
        fen="startpos"
    )

    # --------------------------------------------------------
    # Starting position
    # --------------------------------------------------------

    render_position(
        board,
        output_dir / "000.png"
    )

    # --------------------------------------------------------
    # Replay game
    # --------------------------------------------------------

    for index, pdn_move in enumerate(
        game.moves,
        start=1
    ):

        move = Move(
            board,
            pdn_move=pdn_move
        )

        board.push(move)

        render_position(
            board,
            output_dir / f"{index:03d}.png",
            last_move=pdn_move,
            move_number=index
        )


# ============================================================
# POSITION / PROBLEM
# ============================================================

def render_position_file(
    position_path,
    output_dir
):

    position = load_position(
        position_path
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    board = position.create_board()

    # --------------------------------------------------------
    # Position 0
    #
    # The untouched diagram.
    # --------------------------------------------------------

    render_position(
        board,
        output_dir / "000.png"
    )

    # --------------------------------------------------------
    # Replay solution
    # --------------------------------------------------------

    for index, pdn_move in enumerate(
        position.solution,
        start=1
    ):

        try:

            move = Move(
                board,
                pdn_move=pdn_move
            )

        except Exception as exc:

            raise ValueError(
                f"Illegal or invalid solution move "
                f"'{pdn_move}' at move {index} "
                f"in {position_path}"
            ) from exc

        board.push(move)

        render_position(
            board,
            output_dir / f"{index:03d}.png",
            last_move=pdn_move,
            move_number=index
        )


# ============================================================
# SINGLE FILE
# ============================================================

def render_file(
    filepath
):

    filepath = Path(filepath)

    if not filepath.exists():

        raise FileNotFoundError(
            f"Input file not found: {filepath}"
        )

    suffix = filepath.suffix.lower()

    output_dir = (
        OUTPUT_ROOT /
        filepath.stem
    )

    if suffix == ".pdn":

        render_game(
            filepath,
            output_dir
        )

    elif suffix in (
        ".txt",
        ".position",
        ".problem"
    ):

        render_position_file(
            filepath,
            output_dir
        )

    else:

        raise ValueError(
            f"Unsupported input type: {filepath.suffix}"
        )


# ============================================================
# FOLDER
# ============================================================

def render_folder(
    folder
):

    folder = Path(folder)

    if not folder.exists():

        raise FileNotFoundError(
            f"Folder not found: {folder}"
        )

    files = sorted(
        [
            p
            for p in folder.iterdir()
            if p.is_file()
            and p.suffix.lower() in (
                ".pdn",
                ".txt",
                ".position",
                ".problem"
            )
        ]
    )

    if not files:

        print(
            f"No supported files found in {folder}"
        )

        return

    for filepath in files:

        print(
            f"Rendering: {filepath.name}"
        )

        render_file(
            filepath
        )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  python main.py <file>"
        )

        print(
            "  python main.py <folder>"
        )

        print()

        print(
            "Supported files:"
        )

        print(
            "  .pdn"
        )

        print(
            "  .txt"
        )

        print(
            "  .position"
        )

        print(
            "  .problem"
        )

        sys.exit(1)

    target = Path(
        sys.argv[1]
    )

    try:

        if target.is_dir():

            render_folder(
                target
            )

        else:

            render_file(
                target
            )

    except PositionFileError as exc:

        print()
        print(
            "POSITION ERROR:"
        )
        print(exc)
        sys.exit(1)

    except Exception as exc:

        print()
        print(
            "ERROR:"
        )
        print(exc)
        sys.exit(1)

    print()
    print(
        "Rendering complete."
    )


if __name__ == "__main__":
    main()