"""Общие типы данных, которыми пользуются все три модуля.

Система координат «мировая»: начало в левом нижнем углу холста,
ось Y направлена ВВЕРХ (как в математике). Поэтому положительный угол
поворота — против часовой стрелки, а «слева/справа» от ребра совпадают
с тем, что видно на экране. Перевод в экранные координаты делает только UI.
"""

from typing import NamedTuple


class Point(NamedTuple):
    x: float
    y: float


class Polygon:
    """Полигон — список вершин. 1 вершина — точка, 2 — ребро (a -> b)."""

    def __init__(self, vertices=None):
        self.vertices: list[Point] = [Point(float(v[0]), float(v[1])) for v in (vertices or [])]

    def __len__(self):
        return len(self.vertices)

    def copy(self) -> "Polygon":
        return Polygon(self.vertices)

    @property
    def kind(self) -> str:
        n = len(self.vertices)
        if n == 1:
            return "точка"
        if n == 2:
            return "ребро"
        return f"полигон ({n} вершин)"

    def __repr__(self):
        return f"Polygon({self.vertices!r})"
