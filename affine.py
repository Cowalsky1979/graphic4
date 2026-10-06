"""ЧЕЛОВЕК 2: аффинные преобразования (всё — через матрицы 3x3).

Соглашение: однородные координаты, точка — столбец (x, y, 1)^T,
преобразование точки: p' = M · p. Композиция «сначала A, потом B» = B @ A.
Углы — в РАДИАНАХ, положительный угол — против часовой стрелки
(ось Y направлена вверх, см. geometry.py).

Центр полигона = среднее арифметическое вершин (зафиксировано).

UI вызывает только функции из раздела «Интерфейс для UI».
"""

import math

from geometry import Point, Polygon


class Mat3:
    """Матрица 3x3. self.m — список из трёх строк по три числа."""

    def __init__(self, m=None):
        if m is None:
            m = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        self.m = [[float(v) for v in row] for row in m]

    def __matmul__(self, other: "Mat3") -> "Mat3":
        """Умножение матриц: self @ other."""
        a, b = self.m, other.m
        return Mat3(
            [
                [sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
                for i in range(3)
            ]
        )

    def apply(self, p: Point) -> Point:
        """Умножение матрицы на точку: M · (x, y, 1)^T."""
        m = self.m
        x = m[0][0] * p.x + m[0][1] * p.y + m[0][2]
        y = m[1][0] * p.x + m[1][1] * p.y + m[1][2]
        w = m[2][0] * p.x + m[2][1] * p.y + m[2][2]
        # для аффинных матриц w == 1; деление — на случай проективных
        if w != 1.0 and w != 0.0:
            x, y = x / w, y / w
        return Point(x, y)

    def __repr__(self):
        return f"Mat3({self.m!r})"


# ---------- базовые матрицы ----------


def identity() -> Mat3:
    return Mat3()


def translation(dx: float, dy: float) -> Mat3:
    """T(dx, dy)."""
    return Mat3([[1, 0, dx], [0, 1, dy], [0, 0, 1]])


def rotation(angle: float) -> Mat3:
    """R(φ) вокруг начала координат (против часовой при Y вверх)."""
    c, s = math.cos(angle), math.sin(angle)
    return Mat3([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def scaling(sx: float, sy: float) -> Mat3:
    """S(sx, sy) относительно начала координат."""
    return Mat3([[sx, 0, 0], [0, sy, 0], [0, 0, 1]])


# ---------- Интерфейс для UI ----------


def translate(dx: float, dy: float) -> Mat3:
    """Матрица смещения на (dx, dy)."""
    return translation(dx, dy)


def rotate_around(p: Point, angle: float) -> Mat3:
    """Поворот вокруг точки p: T(p) · R(φ) · T(-p)."""
    return translation(p.x, p.y) @ rotation(angle) @ translation(-p.x, -p.y)


def scale_around(p: Point, sx: float, sy: float) -> Mat3:
    """Масштаб относительно точки p: T(p) · S(sx, sy) · T(-p)."""
    return translation(p.x, p.y) @ scaling(sx, sy) @ translation(-p.x, -p.y)


def polygon_center(poly: Polygon) -> Point:
    """Центр полигона — среднее арифметическое вершин."""
    n = len(poly.vertices)
    if n == 0:
        raise ValueError("пустой полигон: центра нет")
    sx = sum(v.x for v in poly.vertices)
    sy = sum(v.y for v in poly.vertices)
    return Point(sx / n, sy / n)


def rotate_around_center(poly: Polygon, angle: float) -> Mat3:
    """Поворот вокруг собственного центра полигона."""
    return rotate_around(polygon_center(poly), angle)


def scale_around_center(poly: Polygon, sx: float, sy: float) -> Mat3:
    """Масштаб относительно собственного центра полигона."""
    return scale_around(polygon_center(poly), sx, sy)


def transformed(poly: Polygon, m: Mat3) -> Polygon:
    """Новый полигон, к каждой вершине которого применена матрица m."""
    return Polygon([m.apply(v) for v in poly.vertices])


def apply_transform(poly: Polygon, m: Mat3) -> None:
    """То же, что transformed, но изменяет poly на месте."""
    poly.vertices = [m.apply(v) for v in poly.vertices]


if __name__ == "__main__":
    # быстрая самопроверка
    sq = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    c = polygon_center(sq)
    assert c == Point(1.0, 1.0)

    r = transformed(sq, rotate_around(c, math.pi / 2))
    expected = [(2, 0), (2, 2), (0, 2), (0, 0)]
    for v, e in zip(r.vertices, expected):
        assert abs(v.x - e[0]) < 1e-9 and abs(v.y - e[1]) < 1e-9

    s = transformed(sq, scale_around(Point(0, 0), 2, 3))
    assert s.vertices[2] == Point(4.0, 6.0)

    t = transformed(sq, translate(5, -1))
    assert t.vertices[0] == Point(5.0, -1.0)
    print("ok")
