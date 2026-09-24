"""Measured source rectangles and ground pivots, in source-image pixels.

Do not scale a crouching dog to the height of a standing dog. Head width sets
the scale; the body's support point sets placement. Front frames never flip.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpriteLayout:
    rect: tuple[int, int, int, int]
    anchor: tuple[float, float]
    head_width: float
    facing: str = "front"

    @property
    def head_fraction(self) -> float:
        return 0.88 if self.facing == "front" else 0.68


# Coordinates are local to each rectangle; anchors exclude hands, toys and fur.
MOTION = (
    SpriteLayout((0, 40, 362, 320), (179, 304), 345),
    SpriteLayout((362, 40, 362, 320), (180, 304), 353),
    SpriteLayout((724, 40, 366, 320), (177, 304), 354),
    SpriteLayout((1090, 50, 358, 310), (174, 294), 345),
    SpriteLayout((0, 400, 362, 312), (192, 285), 258, "left"),
    SpriteLayout((362, 400, 362, 312), (194, 285), 250, "left"),
    SpriteLayout((724, 400, 370, 312), (190, 276), 258, "left"),
    SpriteLayout((1094, 400, 354, 320), (217, 303), 248, "left"),
    # In flight, use a virtual support point below the tucked body, keeping
    # the torso near the same physical y instead of lowering it with the paws.
    SpriteLayout((0, 746, 362, 270), (189, 261), 250, "left"),
    SpriteLayout((362, 770, 362, 265), (189, 240), 250, "left"),
    SpriteLayout((724, 768, 365, 270), (181, 246), 354),
    SpriteLayout((1090, 745, 358, 320), (176, 292), 338),
)
ACTION = (
    SpriteLayout((0, 46, 378, 350), (191, 336), 344),
    SpriteLayout((380, 100, 366, 296), (186, 282), 344),
    SpriteLayout((746, 95, 333, 301), (160, 278), 315),
    SpriteLayout((1080, 94, 368, 302), (192, 265), 344),
    SpriteLayout((0, 414, 378, 304), (193, 282), 344),
    SpriteLayout((378, 420, 364, 298), (184, 277), 310, "left"),
    SpriteLayout((742, 420, 375, 298), (177, 276), 310, "right"),
    SpriteLayout((1117, 414, 331, 310), (169, 290), 320),
    SpriteLayout((0, 724, 400, 330), (222, 313), 304),
    SpriteLayout((400, 770, 346, 281), (166, 251), 278, "left"),
    SpriteLayout((746, 760, 342, 300), (167, 275), 330),
    SpriteLayout((1088, 750, 360, 310), (178, 286), 332),
)


def layout_for(sheet: str, row: int, column: int) -> SpriteLayout:
    if sheet == "motion":
        return MOTION[row * 4 + column]
    if sheet == "action":
        return ACTION[row * 4 + column]
    if sheet == "gait":
        anchors = ((346, 563), (318, 563), (346, 496), (318, 496))
        return SpriteLayout((column * 627, row * 627, 627, 627), anchors[row * 2 + column], 433, "left")
    if sheet == "rest":
        layouts = (
            SpriteLayout((0, 100, 626, 545), (327, 514), 596),
            SpriteLayout((626, 140, 628, 505), (288, 474), 586),
            SpriteLayout((0, 736, 628, 418), (328, 374), 598),
            SpriteLayout((628, 736, 626, 418), (290, 374), 595),
        )
        return layouts[row * 2 + column]
    raise ValueError(f"Unknown sprite sheet: {sheet}")


def should_flip(layout: SpriteLayout, facing_right: bool) -> bool:
    if layout.facing == "front":
        return False
    return (layout.facing == "left") == facing_right
