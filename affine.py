"""ЧЕЛОВЕК 2: аффинные преобразования (всё — через матрицы 3x3).

Соглашение: однородные координаты, точка — столбец (x, y, 1)^T,
преобразование точки: p' = M · p. Композиция «сначала A, потом B» = B @ A.
Углы — в РАДИАНАХ, положительный угол — против часовой стрелки
(ось Y направлена вверх, см. geometry.py).

UI вызывает только функции из раздела «Интерфейс для UI».
Пока функция не реализована, она бросает NotImplementedError —
UI это ловит и пишет в строке статуса «не реализовано».
"""

from geometry import Point, Polygon


class Mat3:
    """Матрица 3x3. self.m — список из трёх строк по три числа."""

    def __init__(self, m=None):
        self.m = m

    def __matmul__(self, other: "Mat3") -> "Mat3":
        """Умножение матриц: self @ other."""
        raise NotImplementedError

    def apply(self, p: Point) -> Point:
        """Умножение матрицы на точку: M · (x, y, 1)^T."""
        raise NotImplementedError


# ---------- базовые матрицы ----------

def identity() -> Mat3:
    raise NotImplementedError


def translation(dx: float, dy: float) -> Mat3:
    """T(dx, dy)."""
    raise NotImplementedError


def rotation(angle: float) -> Mat3:
    """R(φ) вокруг начала координат."""
    raise NotImplementedError


def scaling(sx: float, sy: float) -> Mat3:
    """S(sx, sy) относительно начала координат."""
    raise NotImplementedError


# ---------- Интерфейс для UI ----------

def translate(dx: float, dy: float) -> Mat3:
    """Матрица смещения на (dx, dy)."""
    raise NotImplementedError


def rotate_around(p: Point, angle: float) -> Mat3:
    """Поворот вокруг точки p: T(p) · R(φ) · T(-p)."""
    raise NotImplementedError


def scale_around(p: Point, sx: float, sy: float) -> Mat3:
    """Масштаб относительно точки p: T(p) · S(sx, sy) · T(-p)."""
    raise NotImplementedError


def polygon_center(poly: Polygon) -> Point:
    """Центр полигона (среднее вершин или центр bounding box — выбрать и зафиксировать)."""
    raise NotImplementedError


def transformed(poly: Polygon, m: Mat3) -> Polygon:
    """Новый полигон, к каждой вершине которого применена матрица m."""
    raise NotImplementedError


def apply_transform(poly: Polygon, m: Mat3) -> None:
    """То же, что transformed, но изменяет poly на месте."""
    raise NotImplementedError
