import grf

road_ground_tiles = (
    ("bay_ne", 0xA84),
    ("bay_se", 0xA85),
    ("bay_nw", 0xA86),
    ("bay_sw", 0xA87),
    ("pass_ne_sw", 0x522),
    ("pass_nw_se", 0x521),
)


class LayoutOperation:
    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def calculate_offset(x, y):
        # Convert x and y to their respective nibbles
        high_nibble = x & 0x0F
        low_nibble = y & 0x0F

        # Combine the high and low nibbles into a single byte
        offset = (high_nibble << 4) | low_nibble

        return offset


class SequenceManager:
    def __init__(self) -> None:
        self.labels = {}
        self.new_len = 0

    def index(self, s: str) -> int:
        self.labels[s] = self.labels.get(s, len(self.labels))
        return self.labels[s]

    def new(self, i=1) -> int:
        current_len = self.new_len
        self.new_len += i
        return current_len


class StringManager(SequenceManager):
    CLASS_STRING_OFFSET = 0xDC00

    def __init__(self) -> None:
        super().__init__()

    def index(self, s: str) -> int:
        return super().index(s) + self.CLASS_STRING_OFFSET


class_string_manager = StringManager()


class RoadStop(grf.SpriteGenerator):
    FEATURE = grf.ROAD_STOP

    def __init__(
        self, callbacks, props, class_name, class_label, sprite_layouts, name, id=None
    ) -> None:
        super().__init__()
        self.callbacks = grf.make_callback_manager(grf.ROAD_STOP, callbacks)
        self.id: int = id
        self.name: str = name
        self.sprite_layouts: dict[str, grf.AdvancedSpriteLayout] = sprite_layouts
        self.class_label: bytes = grf.to_bytes(class_label)
        self.class_name: str = class_name
        self._props = props

    def get_sprites(self, g) -> list:
        raise NotImplementedError


class RoadDeco(RoadStop):
    def __init__(
        self,
        callbacks,
        class_name,
        class_label,
        sprites: list[grf.FileSprite],
        name,
        props={},
        id=None,
    ):
        super().__init__(callbacks, props, class_name, class_label, None, name, id)
        self.sprites = sprites

    def get_sprites(self, g) -> list:
        res = []  # to return this thing

        assert (
            len(self.sprites) % 2 == 0
        ), f"Sprites must be in pairs, got {len(self.sprites)}"

        res.append(
            grf.Action1(
                feature=grf.ROAD_STOP,
                set_count=2,
                sprite_count=len(self.sprites) // 2,
                first_set=0,
            )
        )
        res.extend(self.sprites)

        # strings
        for s in (self.name, self.class_name):
            if s in class_string_manager.labels:
                continue
            res.append(
                grf.DefineStrings(
                    feature=self.FEATURE,
                    offset=class_string_manager.index(s),
                    is_generic_offset=True,
                    strings=[s.encode("utf-8")],
                )
            )

        res.append(
            definition := grf.Define(
                feature=self.FEATURE,
                id=self.id,
                props={
                    "class_label": self.class_label,
                    "name_id": class_string_manager.index(self.name),
                    "class_name_id": class_string_manager.index(self.class_name),
                    "general_flags": 0b00001000,
                    "draw_mode": 4,
                    **self._props,
                },
            )
        )

        layouts = {
            i: grf.AdvancedSpriteLayout(
                feature=grf.ROAD_STOP,
                ground={
                    "sprite": grf.SpriteRef(
                        id=val[1],
                        pal=0,
                        is_global=True,
                        use_recolour=False,
                        always_transparent=False,
                        no_transparent=False,
                    ),
                },
                buildings=[
                    {
                        "sprite": grf.SpriteRef(
                            id=0 if i == 4 else 1,
                            pal=0,
                            is_global=False,
                            use_recolour=False,
                            always_transparent=False,
                            no_transparent=False,
                        ),
                        "add": grf.Temp(0 if i == 4 else 1),
                    },
                ],
            )
            for i, val in enumerate(road_ground_tiles)
            if i in (4, 5)
        }

        def get_tile_id(x: int, y: int):
            return f"var(0x68, param=({LayoutOperation.calculate_offset(x, y)}), shift=0, and=0xF)"

        res.append(
            layout := grf.Switch(
                feature=self.FEATURE,
                related_scope=False,
                code=("TEMP[1] = formation_1()", "TEMP[0] = formation_0()", "view"),
                ranges={**layouts},
                default=next(iter(layouts.values()), None),
                subroutines={
                    "formation_0": grf.Switch(
                        feature=self.FEATURE,
                        related_scope=False,
                        ranges={},
                        code=(
                            f"({get_tile_id(0,0)} == {get_tile_id(0,-1)}) + ({get_tile_id(0,0)} == {get_tile_id(0,1)}) * 2"
                        ),
                        default=0,
                    ),
                    "formation_1": grf.Switch(
                        feature=self.FEATURE,
                        related_scope=False,
                        ranges={},
                        code=(
                            f"({get_tile_id(0,0)} == {get_tile_id(-1,0)}) + ({get_tile_id(0,0)} == {get_tile_id(1,0)}) * 2"
                        ),
                        default=0,
                    ),
                },
            )
        )

        res.append(
            grf.Map(
                definition,
                {},
                layout,
            )
        )

        return res


def tmpl_pullouts(x, func):
    ls = []
    for i in range(7):
        ls += [
            func(80 * (x * 4 + j) + 16, 32 * i * 2 + 33, 64, 31, xofs=-31, yofs=0)
            for j in range(4)
        ]
        ls += [
            func(80 * (x * 4 + j) + 16, 32 * (i * 2 + 1) + 33, 64, 31, xofs=-31, yofs=0)
            for j in range(4)
        ]
    return ls


pullouts_png = grf.ImageFile("gfx/u-ratt-pullouts.png")  # TODO finish
sprites = [
    sprite
    for i in range(2)
    for sprite in tmpl_pullouts(
        i, lambda *args, **kw: grf.FileSprite(pullouts_png, *args, **kw, bpp=8)
    )
]

g = grf.NewGRF(
    grfid=b"ROAD",
    name="grf-py road station sample",
    description="grf-py road station sample",
)

id_manager = SequenceManager()

stops = [
    RoadDeco(
        callbacks=None,
        class_name="Station",
        class_label=b"STAT",
        name="Sample station",
        id=id_manager.new(),  # wow new id!
        sprites=packed_sprites,
    )
    for packed_sprites in [
        sprites[i : i + 8] for i in range(0, len(sprites), 8)
    ]  # 8 sprites per station
]

g.add(*stops)
g.write("station.grf")
