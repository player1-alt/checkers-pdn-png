from draughts.PDN import PDNReader


def load_pdn(path):
    """
    Load the first game from a PDN file.
    """

    reader = PDNReader(
        filename=str(path)
    )

    if not reader.games:
        raise ValueError(
            f"No games found in PDN: {path}"
        )

    return reader.games[0]