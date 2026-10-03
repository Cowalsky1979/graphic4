"""ЧЕЛОВЕК 3: вычислительная геометрия.

Координаты «мировые», ось Y вверх (см. geometry.py), поэтому
cross(b - a, p - a) > 0 означает «точка слева от ребра a -> b».

Пока функция не реализована, она бросает NotImplementedError —
UI это ловит и пишет в строке статуса «не реализовано».
"""

from geometry import Point, Polygon

# Результаты classify_point
LEFT = "left"
RIGHT = "right"
ON_LINE = "on_line"

# Результаты segment_intersection (первый элемент кортежа)
INTERSECT = "intersect"        # пересекаются в одной точке (точка во втором элементе)
NO_INTERSECTION = "none"       # не пересекаются
PARALLEL = "parallel"          # параллельны, не на одной прямой
COLLINEAR = "collinear"        # на одной прямой, общих точек нет
OVERLAP = "overlap"            # на одной прямой и перекрываются (общий отрезок)

# Результаты проверки принадлежности точки полигону
INSIDE = "inside"
OUTSIDE = "outside"
ON_BOUNDARY = "boundary"


def classify_point(p: Point, a: Point, b: Point) -> str:
    """Положение точки p относительно ребра a -> b: LEFT / RIGHT / ON_LINE."""
    raise NotImplementedError


def segment_intersection(a: Point, b: Point, c: Point, d: Point) -> tuple[str, Point | None]:
    """Пересечение отрезков ab и cd.

    Возвращает (статус, точка): точка задана только при статусе INTERSECT
    (в т.ч. если коллинеарные отрезки касаются ровно одним концом).
    """
    raise NotImplementedError


def is_convex(poly: Polygon) -> bool:
    """Выпуклость полигона по знакам поворотов всех троек вершин."""
    raise NotImplementedError


def point_in_convex_polygon(p: Point, poly: Polygon) -> str:
    """INSIDE / OUTSIDE / ON_BOUNDARY для выпуклого полигона (знаки cross по всем рёбрам)."""
    raise NotImplementedError


def point_in_polygon(p: Point, poly: Polygon) -> str:
    """INSIDE / OUTSIDE / ON_BOUNDARY для произвольного полигона (луч или winding number)."""
    raise NotImplementedError
