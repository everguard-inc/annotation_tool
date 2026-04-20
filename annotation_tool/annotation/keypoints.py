from annotation_tool.annotation.figures import Figure, Point


class KeypointGroup(Figure):
    def __init__(self, label: str, keypoints: list[Point]) -> None:
        ...

    @classmethod
    def from_box(
        cls,
        start: Point,
        end: Point,
        label: str,
        keypoint_template: dict,
    ) -> "KeypointGroup | None":
        ...
