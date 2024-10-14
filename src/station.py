import grf

road_ground_tiles = {
    "bay_ne": 0xA84,
    "bay_se": 0xA85,
    "bay_nw": 0xA86,
    "bay_sw": 0xA87,
    "pass_ne_sw": 0x522,
    "pass_nw_se": 0x521,
}

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


class SequenceManager:

    def __init__(self) -> None:
        self.labels = {}
        self.new_len = 0

    def index(self, s: str) -> int:
        self.labels[s] = self.labels.get(s, len(self.labels))
        return self.labels[s]

    def new(self) -> int:
        current_len = self.new_len
        self.new_len += 1
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
        self.sprite_layouts: list[grf.AdvancedSpriteLayout] = sprite_layouts
        self.class_label: bytes = grf.to_bytes(class_label)
        self.class_name: str = class_name
        self._props = props

    def get_sprites(self, g) -> list:
        res = []  # to return this thing

        res.extend(self.sprite_layouts)

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
                    **self._props,
                },
            )
        )

        res.append(
            layout := grf.Switch(
                feature=self.FEATURE,
                related_scope=False,
                code=("view"),
                ranges={i: res[i] for i in range(6)},
                default = res[2],
            )
        )

        res.append(
            grf.Map(
                definition,
                {},  # cargo types
                layout,  # FIXME
            )
        )

        return res

class RoadDeco(RoadStop):
    def __init__(self, callbacks, props, class_name, class_label, sprite_layouts, name, id=None):
        super().__init__(callbacks, props, class_name, class_label, sprite_layouts, name, id)

def tmpl_pullouts(x, func):
    return [
        func(72 * x + 1, 35 * i + 1, 64, 31, xofs=-31, yofs=0) for i in range(16)
    ]


pullouts_png = grf.ImageFile("gfx/u-ratt-pullouts.png")  # TODO finish
sprites = [
    sprite
    for i in range(6)
    for sprite in tmpl_pullouts(
        i, lambda *args, **kw: grf.FileSprite(pullouts_png, *args, **kw, bpp=8)
    )
]

g = grf.NewGRF(
    grfid=b"ROAD",
    name="grf-py road station sample",
    description="grf-py road station sample",
)


g.add(
    grf.Action1(
        feature=grf.ROAD_STOP,
        set_count=len(sprites),
        sprite_count=1,
        first_set=None,
    )
)
g.add(*sprites)

def call_next():
    processed = {}
    yield len(processed)

sequence_manager = SequenceManager()
id_manager = SequenceManager()

stops = [RoadStop(
    callbacks=None,
    props={},
    class_name="Station",
    class_label=b"STAT",
    name="Sample station",
    id=id_manager.new(),

    sprite_layouts=[
        grf.AdvancedSpriteLayout(
            feature=grf.ROAD_STOP,
            ground={
                "sprite": grf.SpriteRef(
                    id=gfx,
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
                        id=sequence_manager.new(),
                        pal=0,
                        is_global=False,
                        use_recolour=False,
                        always_transparent=False,
                        no_transparent=False,
                    ),
                    "offset": (0, 0, 0),
                    "extent": (16,16,0),
                }
            ]
        ) for gfx in (0xA84, 0xA85, 0xA86, 0xA87, 0x522, 0x521)
    ],
) for i in range(len(sprites)//6+1)]


g.add(*stops)
g.write("station.grf")
