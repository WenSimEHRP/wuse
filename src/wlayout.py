road_ground_tiles = (
    ("bay_ne", 0xA84),
    ("bay_se", 0xA85),
    ("bay_nw", 0xA86),
    ("bay_sw", 0xA87),
    ("pass_ne_sw", 0x522),
    ("pass_nw_se", 0x521),
)


def rotate(
    offset: tuple[int, int, int], extent: tuple[int, int, int], angle: int
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    match angle % 4:
        case 0:
            return offset, extent
        case 1 | -3:
            return (offset[1], -offset[0], offset[2]), (
                extent[1],
                extent[0],
                extent[2],
            )
        case 2 | -2:
            return (-offset[0], -offset[1], offset[2]), (
                extent[0],
                extent[1],
                extent[2],
            )
        case 3 | -1:
            return (-offset[1], offset[0], offset[2]), (
                extent[1],
                extent[0],
                extent[2],
            )
    raise ValueError(f"Invalid angle: {angle}")


def flip(
    offset: tuple[int, int, int], extent: tuple[int, int, int], axis: int
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    match axis:
        case 0 | "x" | "X":
            return (-offset[0], offset[1], offset[2]), (
                extent[0],
                extent[1],
                extent[2],
            )
        case 1 | "y" | "Y":
            return (offset[0], -offset[1], offset[2]), (
                extent[0],
                extent[1],
                extent[2],
            )
        case 2 | "z" | "Z":
            return (offset[0], offset[1], -offset[2]), (
                extent[0],
                extent[1],
                extent[2],
            )
    raise ValueError(f"Invalid axis: {axis}")


def calculate_offset(x, y):
    # Convert x and y to their respective nibbles
    high_nibble = x & 0x0F
    low_nibble = y & 0x0F
    # Combine the high and low nibbles into a single byte
    offset = (high_nibble << 4) | low_nibble
    return offset
