import grf
from abc import ABC, abstractmethod
from . import wlayout


class SequenceManager:
    labels = {}
    new_len = 0

    def __init__(self) -> None:
        pass

    def index(self, s: str) -> int:
        self.labels[s] = self.labels.get(s, len(self.labels))
        return self.labels[s]

    def new(self, i=1) -> int:
        current_len = self.new_len
        self.new_len += i
        return current_len


class StringManagerDC00(SequenceManager):
    CLASS_STRING_OFFSET = 0xDC00

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def index(cls, s: str) -> int:
        return super().index(s) + cls.CLASS_STRING_OFFSET


class RoadStopDefineMixin:
    def __init__(self, props, class_name, class_label, id):
        self.props = props
        self.class_name = class_name
        self.class_label = class_label
        assert len(id) == 4
        self.id = id
        self._definition = None
        self.string_man = StringManagerDC00

    @property
    def definition(self):
        if self._definition is not None:
            return self._definition
        self._definition = grf.Define(
            feature=self.FEATURE,
            id=self.id,
            props={
                "class_label": self.class_label,
                "name_id": self.string_man.index(self.name),
                "class_name_id": self.string_man.index(self.class_name),
                **self._props,
            },
        )
        return self._definition

    @property
    def is_waypoint(self):
        return self.class_label == b"WAYP" or self.class_label.startswith(b"\xff")


class RoadStop(ABC, grf.SpriteGenerator, RoadStopDefineMixin):
    FEATURE = grf.ROAD_STOP

    @abstractmethod
    def get_sprites(self, g) -> list:
        raise NotImplementedError

    @abstractmethod
    def layouts(self) -> list:
        raise NotImplementedError


class BoundingBoxMixin:
    """Bounding box format: offset: tuple(x, y, z), extent: tuple(x, y, z)"""

    def __init__(
        self,
        offset: tuple[int, int, int] = (0, 0, 0),
        extent: tuple[int, int, int] = (16, 16, 16),
    ):
        self.offset = offset
        self.extent = extent


class RegistersMixin:
    """Register format: key: code"""

    def __init__(self, registers: dict):
        from grf.parser import parse_code

        for code in registers.values():
            if parse_code(grf.ROAD_STOP, code) is None:
                raise ValueError(f"Invalid code: {code}")

        self.registers = {
            "x_left": None,
            "x_right": None,
            "y_left": None,
            "y_right": None,
            **registers,
        }


class SpriteMixin:
    def __init__(self, sprites: dict):
        # no more checks!
        self.sprites = {
            "x_left": None,
            "x_right": None,
            "y_left": None,
            "y_right": None,
            **sprites,
        }


class RoadDecoModeMixin:
    def __init__(self, mode: dict):
        self.mode = {"generate": True, "flip": False, **mode}
        self._layouts = None

    @property
    def layouts(self, offset, extent):
        if self._layouts is not None:
            return self._layouts
        # four layouts
        res = {}
        res["x_left"] = {
            "offset": offset,
            "extent": extent,
        }
        res["y_left"] = (
            {
                "offset": wlayout.rotate(offset, "y", 1),
                "extent": wlayout.rotate(extent, "y", 1),
            },
        )
        if self.mode["generate"]:
            res["x_right"] = {
                "offset": wlayout.flip(offset, "x")
                if self.mode["flip"]
                else wlayout.rotate(offset, "x", 2),
                "extent": wlayout.flip(extent, "x")
                if self.mode["flip"]
                else wlayout.rotate(extent, "x", 2),
            }
            res["y_right"] = {
                "offset": wlayout.flip(wlayout.rotate(offset, "y", -1), "y")
                if self.mode["flip"]
                else wlayout.rotate(offset, "y", -1),
                "extent": wlayout.flip(wlayout.rotate(extent, "y", -1), "y")
                if self.mode["flip"]
                else wlayout.rotate(extent, "y", -1),
            }
        self._layout = res
        return res


class RoadDecoBuilding(
    BoundingBoxMixin, RegistersMixin, SpriteMixin, RoadDecoModeMixin
):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sprite_count = None

    @property
    def sprite_count(self):
        if self._sprite_count is not None:
            return self._sprite_count
        self._sprite_count = sum(len(i) for i in self.sprites.values() if i is not None)
        return self._sprite_count


class RoadDecoBuildingSet:
    def __init__(self, *buildings):
        self.buildings = buildings

    @property
    def sprite_count(self):
        return sum(i.sprite_count for i in self.buildings)


class RoadDeco(RoadStop):
    def __init__(
        self,
        callbacks: list,
        buildings: RoadDecoBuildingSet,
        **kwargs,
    ):
        self.callbacks = grf.make_callback_manager(grf.ROAD_STOP, callbacks)
        self.buildings = buildings
        super().__init__(**kwargs)

    def _make_realsprites(self):
        res = []
        res.append(
            grf.Action1(
                feature=self.FEATURE,
                sprite_count=None,  # XXX
            )
        )

    def get_sprites(self, g):
        res = []
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
