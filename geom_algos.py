"""
Координаты «мировые», ось Y вверх (geometry.py), поэтому
cross(b - a, p - a) > 0 означает «точка слева от ребра a -> b».
"""

import math

from geometry import Point, Polygon

# Результаты classify_point
LEFT = "left"
RIGHT = "right"
ON_LINE = "on_line"

# Результаты segment_intersection (первый элемент кортежа)
INTERSECT = "intersect"  # пересекаются в одной точке (точка во втором элементе)
NO_INTERSECTION = "none"  # не пересекаются
PARALLEL = "parallel"  # параллельны, не на одной прямой
COLLINEAR = "collinear"  # на одной прямой, общих точек нет
OVERLAP = "overlap"  # на одной прямой и перекрываются (общий отрезок)

# Результаты проверки принадлежности точки полигону
INSIDE = "inside"
OUTSIDE = "outside"
ON_BOUNDARY = "boundary"

# Допуск для сравнения float с нулём (float врёт в последних знаках)
EPS = 1e-9


# ---------- вспомогательные функции ----------


def cross(o: Point, a: Point, b: Point) -> float:
    """Косое (векторное) произведение (a - o) x (b - o).

    > 0: поворот от o->a к o->b идёт против часовой (b слева от o->a),
    < 0: по часовой (справа),
    ≈ 0: три точки на одной прямой.
    """
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)


def on_segment(p: Point, a: Point, b: Point) -> bool:
    """Лежит ли p на отрезке ab (на прямой и между концами)."""
    if abs(cross(a, b, p)) > EPS * max(1.0, math.hypot(b.x - a.x, b.y - a.y)):
        return False
    return (
            min(a.x, b.x) - EPS <= p.x <= max(a.x, b.x) + EPS
            and min(a.y, b.y) - EPS <= p.y <= max(a.y, b.y) + EPS
    )


def dist_to_segment(p: Point, a: Point, b: Point) -> float:
    """Расстояние от точки p до отрезка ab."""
    vx, vy = b.x - a.x, b.y - a.y
    wx, wy = p.x - a.x, p.y - a.y
    len2 = vx * vx + vy * vy
    t = 0.0 if len2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / len2))
    return math.hypot(p.x - (a.x + t * vx), p.y - (a.y + t * vy))


def _edges(poly: Polygon):
    """Рёбра полигона как пары (a, b), включая замыкающее ребро."""
    v = poly.vertices
    n = len(v)
    return [(v[i], v[(i + 1) % n]) for i in range(n)]


def _on_boundary(p: Point, poly: Polygon, tol: float = EPS) -> bool:
    """Лежит ли p на границе полигона (с допуском tol — расстояние до ребра)."""
    return any(dist_to_segment(p, a, b) <= tol for a, b in _edges(poly))


# ---------- 1. точка относительно ребра ----------


def classify_point(p: Point, a: Point, b: Point, tol: float = EPS) -> str:
    """Положение точки p относительно ребра a -> b: LEFT / RIGHT / ON_LINE.

    tol — допуск по расстоянию до прямой (UI передаёт пару пикселей, чтобы
    мышью можно было попасть «на прямую»).
    """
    length = math.hypot(b.x - a.x, b.y - a.y)
    if length <= EPS:  # ребро схлопнулось в точку
        return ON_LINE
    d = cross(a, b, p) / length  # знаковое расстояние до прямой
    if d > tol:
        return LEFT
    if d < -tol:
        return RIGHT
    return ON_LINE


# ---------- 2. пересечение отрезков ----------


def segment_intersection(a: Point, b: Point, c: Point, d: Point) -> tuple[str, Point | None]:
    """Пересечение отрезков ab и cd.

    Возвращает (статус, точка): точка задана только при статусе INTERSECT
    (в т.ч. если коллинеарные отрезки касаются ровно одним концом).
    """
    rx, ry = b.x - a.x, b.y - a.y  # направление ab
    sx, sy = d.x - c.x, d.y - c.y  # направление cd
    len_r = math.hypot(rx, ry)
    len_s = math.hypot(sx, sy)

    # Вырожденные случаи: отрезок схлопнулся в точку
    # (так бывает, пока второе ребро только начали рисовать)
    if len_r <= EPS and len_s <= EPS:
        return (INTERSECT, a) if math.hypot(a.x - c.x, a.y - c.y) <= EPS else (NO_INTERSECTION, None)
    if len_r <= EPS:
        return (INTERSECT, a) if on_segment(a, c, d) else (NO_INTERSECTION, None)
    if len_s <= EPS:
        return (INTERSECT, c) if on_segment(c, a, b) else (NO_INTERSECTION, None)

    denom = rx * sy - ry * sx  # cross(r, s)
    qx, qy = c.x - a.x, c.y - a.y  # вектор a -> c

    if abs(denom) <= EPS * len_r * len_s:
        # Параллельны. Лежат ли на одной прямой? (расстояние от c до прямой ab)
        if abs(rx * qy - ry * qx) / len_r > EPS:
            return PARALLEL, None
        # На одной прямой: выразим c и d как параметры вдоль ab (a -> 0, b -> 1)
        rr = rx * rx + ry * ry
        t0 = (qx * rx + qy * ry) / rr
        t1 = t0 + (sx * rx + sy * ry) / rr
        left = max(0.0, min(t0, t1))
        right = min(1.0, max(t0, t1))
        if left > right + EPS:
            return COLLINEAR, None
        if right - left <= EPS:  # касаются ровно одним концом
            return INTERSECT, Point(a.x + left * rx, a.y + left * ry)
        return OVERLAP, None

    # Общий случай: a + t*r = c + u*s, решаем через cross
    t = (qx * sy - qy * sx) / denom
    u = (qx * ry - qy * rx) / denom
    if -EPS <= t <= 1 + EPS and -EPS <= u <= 1 + EPS:
        t = min(1.0, max(0.0, t))
        return INTERSECT, Point(a.x + t * rx, a.y + t * ry)
    return NO_INTERSECTION, None


# ---------- 3. выпуклость ----------


def is_convex(poly: Polygon) -> bool:
    """Выпуклость полигона по знакам поворотов всех троек вершин."""
    v = poly.vertices
    n = len(v)
    if n < 3:
        return False

    has_left = has_right = False
    for i in range(n):
        c = cross(v[i], v[(i + 1) % n], v[(i + 2) % n])
        if c > EPS:
            has_left = True
        elif c < -EPS:
            has_right = True
    if has_left == has_right:
        # повороты в обе стороны (невыпуклый) либо все нулевые (вырожденный)
        return False

    # Звезда-пентаграмма тоже поворачивает всегда в одну сторону, но она
    # самопересекающаяся, поэтому проверим, что несмежные рёбра не пересекаются.
    edges = _edges(poly)
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue  # соседние рёбра, у них общая вершина
            status, _ = segment_intersection(*edges[i], *edges[j])
            if status in (INTERSECT, OVERLAP):
                return False
    return True


# ---------- 4. точка в выпуклом полигоне ----------


def point_in_convex_polygon(p: Point, poly: Polygon, tol: float = EPS) -> str:
    """INSIDE / OUTSIDE / ON_BOUNDARY для выпуклого полигона (знаки cross по всем рёбрам)."""
    if len(poly.vertices) < 3:
        return OUTSIDE
    if _on_boundary(p, poly, tol):
        return ON_BOUNDARY

    has_left = has_right = False
    for a, b in _edges(poly):
        c = cross(a, b, p)
        if c > EPS:
            has_left = True
        elif c < -EPS:
            has_right = True
    # внутри — когда точка с одной и той же стороны от ВСЕХ рёбер
    # (так не важно, обход по часовой или против)
    return OUTSIDE if (has_left and has_right) else INSIDE


# ---------- 5. точка в произвольном полигоне ----------


def point_in_polygon(p: Point, poly: Polygon, tol: float = EPS) -> str:
    """INSIDE / OUTSIDE / ON_BOUNDARY для произвольного полигона (луч или winding number)."""
    if len(poly.vertices) < 3:
        return OUTSIDE
    if _on_boundary(p, poly, tol):
        return ON_BOUNDARY

    # Луч вправо из p; считаем пересечения с рёбрами.
    inside = False
    for a, b in _edges(poly):
        # ребро пересекает горизонталь y = p.y (вершина на луче считается ровно один раз)
        if (a.y > p.y) != (b.y > p.y):
            x_cross = a.x + (p.y - a.y) * (b.x - a.x) / (b.y - a.y)
            if x_cross > p.x:  # пересечение справа от точки, то есть на луче
                inside = not inside
    return INSIDE if inside else OUTSIDE


if __name__ == "__main__":
    P = Point

    # classify_point
    assert classify_point(P(0, 1), P(0, 0), P(2, 0)) == LEFT
    assert classify_point(P(0, -1), P(0, 0), P(2, 0)) == RIGHT
    assert classify_point(P(5, 0), P(0, 0), P(2, 0)) == ON_LINE

    # segment_intersection
    st, pt = segment_intersection(P(0, 0), P(2, 2), P(0, 2), P(2, 0))
    assert st == INTERSECT and abs(pt.x - 1) < 1e-9 and abs(pt.y - 1) < 1e-9
    assert segment_intersection(P(0, 0), P(1, 0), P(2, 1), P(3, 5))[0] == NO_INTERSECTION
    assert segment_intersection(P(0, 0), P(2, 0), P(0, 1), P(2, 1))[0] == PARALLEL
    assert segment_intersection(P(0, 0), P(1, 0), P(2, 0), P(3, 0))[0] == COLLINEAR
    assert segment_intersection(P(0, 0), P(2, 0), P(1, 0), P(3, 0))[0] == OVERLAP
    st, pt = segment_intersection(P(0, 0), P(1, 0), P(1, 0), P(2, 0))
    assert st == INTERSECT and pt == P(1, 0)  # касание концами на одной прямой
    st, pt = segment_intersection(P(0, 0), P(2, 0), P(1, 0), P(1, 5))
    assert st == INTERSECT and pt == P(1, 0)  # T-образное касание
    assert segment_intersection(P(0, 0), P(2, 0), P(5, 5), P(5, 5))[0] == NO_INTERSECTION  # d == c

    # выпуклость
    square = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    square_cw = Polygon([(0, 0), (0, 2), (2, 2), (2, 0)])
    g_shape = Polygon([(0, 0), (4, 0), (4, 1), (1, 1), (1, 4), (0, 4)])
    star = Polygon([(0, 2), (3, 0), (1.5, 3.5), (0, 0), (3, 2)])
    assert is_convex(square) and is_convex(square_cw)
    assert not is_convex(g_shape)
    assert not is_convex(star)
    assert not is_convex(Polygon([(0, 0), (1, 1)]))

    # точка в выпуклом
    for sq in (square, square_cw):
        assert point_in_convex_polygon(P(1, 1), sq) == INSIDE
        assert point_in_convex_polygon(P(3, 1), sq) == OUTSIDE
        assert point_in_convex_polygon(P(2, 1), sq) == ON_BOUNDARY
        assert point_in_convex_polygon(P(0, 0), sq) == ON_BOUNDARY
        assert point_in_convex_polygon(P(4, 0), sq) == OUTSIDE  # на продолжении ребра

    # точка в произвольном (Г-образный)
    assert point_in_polygon(P(0.5, 0.5), g_shape) == INSIDE
    assert point_in_polygon(P(0.5, 3), g_shape) == INSIDE
    assert point_in_polygon(P(3, 3), g_shape) == OUTSIDE  # в «вырезе»
    assert point_in_polygon(P(3, 1), g_shape) == ON_BOUNDARY
    assert point_in_polygon(P(-1, 0.5), g_shape) == OUTSIDE
    assert point_in_polygon(P(2, 1), g_shape) == ON_BOUNDARY  # на ребре (1,1)-(4,1)
    # луч точно через вершину
    diamond = Polygon([(0, 2), (2, 0), (4, 2), (2, 4)])
    assert point_in_polygon(P(2, 2), diamond) == INSIDE
    assert point_in_polygon(P(-1, 2), diamond) == OUTSIDE  # луч идёт через 2 вершины
    assert point_in_polygon(P(5, 2), diamond) == OUTSIDE
    # допуск (для мыши): наклонное ребро, точка в ~0.5 от него
    assert classify_point(P(1.5, 2.1), P(0, 0), P(3, 4)) == LEFT  # без допуска — «слева»
    assert classify_point(P(1.5, 2.1), P(0, 0), P(3, 4), tol=0.5) == ON_LINE
    tri = Polygon([(0, 0), (4, 0), (4, 3)])
    assert point_in_convex_polygon(P(2, 1.6), tri) == OUTSIDE
    assert point_in_convex_polygon(P(2, 1.6), tri, tol=0.5) == ON_BOUNDARY
    assert point_in_polygon(P(2, 1.6), tri, tol=0.5) == ON_BOUNDARY
    print("ok")