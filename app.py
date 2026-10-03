"""лёша: каркас, ввод, отрисовка и интеграция модулей affine и geom_algos."""

import math
import tkinter as tk
from tkinter import ttk

import affine
import geom_algos as ga
from geometry import Point, Polygon

# Режимы работы мыши
MODE_POINT = "point"
MODE_EDGE = "edge"
MODE_POLY = "poly"
MODE_SELECT = "select"
MODE_PIVOT = "pivot"
MODE_INTERSECT = "intersect"
MODE_INSIDE = "inside"
MODE_CLASSIFY = "classify"

MODE_GROUPS = [
    ("Создание", [(MODE_POINT, "Точка"), (MODE_EDGE, "Ребро"), (MODE_POLY, "Полигон")]),
    ("Выбор", [(MODE_SELECT, "Выбор полигона"), (MODE_PIVOT, "Опорная точка")]),
    ("Проверки", [(MODE_INTERSECT, "Пересечение рёбер"),
                  (MODE_INSIDE, "Точка в полигоне"),
                  (MODE_CLASSIFY, "Точка и ребро")]),
]

HINTS = {
    MODE_POINT: "ЛКМ — поставить точку.",
    MODE_EDGE: "ЛКМ — две вершины ребра. Esc — отмена.",
    MODE_POLY: "ЛКМ — добавить вершину.\nПКМ или Enter — завершить.\nEsc — отмена.",
    MODE_SELECT: "ЛКМ — выбрать полигон.\nDelete — удалить выбранный.",
    MODE_PIVOT: "ЛКМ — задать опорную точку\n(или впишите x, y вручную).",
    MODE_INTERSECT: "Первое ребро: выбранное ребро (ПКМ)\nили 2 клика ЛКМ.\nДалее ЛКМ — начало и конец второго\nребра, оно следует за курсором.\nEsc — сбросить.",
    MODE_INSIDE: "ПКМ — выбрать полигон.\nЛКМ — проверить точку.",
    MODE_CLASSIFY: "ПКМ — выбрать ребро.\nЛКМ — проверить точку.",
}

PICK_TOLERANCE = 6  # пикселей

COLOR_BG = "white"
COLOR_POLY = "#1f4e8c"
COLOR_POLY_FILL = "#dbe6f5"
COLOR_SELECTED = "#d62828"
COLOR_SELECTED_FILL = "#f8d7d7"
COLOR_DRAFT = "#2a9d8f"
COLOR_PIVOT = "#9b30d9"
COLOR_EDGE1 = "#f4a261"
COLOR_EDGE2 = "#2a6fdb"
COLOR_HIT = "#e63946"

NOT_IMPLEMENTED = "Функция ещё не реализована ({})"


def dist_to_segment(p: Point, a: Point, b: Point) -> float:
    """Расстояние от точки до отрезка — нужно только для выбора полигона мышью."""
    vx, vy = b.x - a.x, b.y - a.y
    wx, wy = p.x - a.x, p.y - a.y
    len2 = vx * vx + vy * vy
    t = 0.0 if len2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / len2))
    return math.hypot(p.x - (a.x + t * vx), p.y - (a.y + t * vy))


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Полигоны: аффинные преобразования и геометрия")
        root.geometry("1200x760")

        self.polygons: list[Polygon] = []
        self.selected: Polygon | None = None
        self.draft: list[Point] = []          # вершины создаваемого полигона
        self.cursor: Point | None = None
        self.markers: list[tuple[Point, str]] = []  # отметки проверок: (точка, цвет)

        # Состояние инструмента «пересечение рёбер»
        self.inter_first: Polygon | None = None   # первое ребро (из сцены или временное)
        self.inter_draft: list[Point] = []
        self.inter_start: Point | None = None     # начало второго ребра
        self.inter_end: Point | None = None       # конец второго ребра (None — следует за курсором)
        self.inter_point: Point | None = None

        self.mode = tk.StringVar(value=MODE_POLY)
        self.status_var = tk.StringVar()
        self.coord_var = tk.StringVar()
        self.hint_var = tk.StringVar()
        self.fields = {
            "dx": tk.StringVar(value="50"), "dy": tk.StringVar(value="0"),
            "angle": tk.StringVar(value="30"),
            "sx": tk.StringVar(value="1.5"), "sy": tk.StringVar(value="1.5"),
            "px": tk.StringVar(), "py": tk.StringVar(),
        }
        for name in ("px", "py"):
            self.fields[name].trace_add("write", lambda *_: self.redraw())

        self._build_ui()
        self._bind_events()
        self.on_mode_change()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        panel = ttk.Frame(self.root, padding=8)
        panel.pack(side=tk.LEFT, fill=tk.Y)

        for title, modes in MODE_GROUPS:
            box = ttk.LabelFrame(panel, text=title, padding=6)
            box.pack(fill=tk.X, pady=(0, 6))
            for value, text in modes:
                ttk.Radiobutton(box, text=text, value=value, variable=self.mode,
                                command=self.on_mode_change).pack(anchor=tk.W)

        scene = ttk.LabelFrame(panel, text="Сцена", padding=6)
        scene.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(scene, text="Очистить сцену", command=self.clear_scene).pack(fill=tk.X)
        ttk.Button(scene, text="Удалить выбранный", command=self.delete_selected).pack(fill=tk.X, pady=2)
        ttk.Button(scene, text="Убрать отметки проверок", command=self.clear_markers).pack(fill=tk.X)

        tr = ttk.LabelFrame(panel, text="Преобразования выбранного", padding=6)
        tr.pack(fill=tk.X, pady=(0, 6))
        grid = ttk.Frame(tr)
        grid.pack(fill=tk.X)
        rows = [("dx", "dy"), ("angle", None), ("sx", "sy"), ("px", "py")]
        labels = {"dx": "dx", "dy": "dy", "angle": "угол °", "sx": "sx", "sy": "sy",
                  "px": "опора x", "py": "опора y"}
        for r, pair in enumerate(rows):
            for c, name in enumerate(pair):
                if name is None:
                    continue
                ttk.Label(grid, text=labels[name]).grid(row=r, column=2 * c, sticky=tk.W, padx=(0, 3))
                ttk.Entry(grid, textvariable=self.fields[name], width=7).grid(
                    row=r, column=2 * c + 1, pady=1, padx=(0, 6))

        buttons = [
            ("Сместить на dx, dy", self.do_translate),
            ("Повернуть вокруг опорной точки", self.do_rotate_pivot),
            ("Повернуть вокруг центра", self.do_rotate_center),
            ("Масштаб от опорной точки", self.do_scale_pivot),
            ("Масштаб от центра", self.do_scale_center),
        ]
        for text, cmd in buttons:
            ttk.Button(tr, text=text, command=cmd).pack(fill=tk.X, pady=1)

        ttk.Label(panel, textvariable=self.hint_var, foreground="#555",
                  justify=tk.LEFT, wraplength=240).pack(anchor=tk.W, pady=(6, 0))

        status = ttk.Frame(self.root, padding=(8, 2))
        status.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status, textvariable=self.status_var, font=("Segoe UI", 11)).pack(side=tk.LEFT)
        ttk.Label(status, textvariable=self.coord_var, foreground="#555").pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(self.root, bg=COLOR_BG, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.root.bind("<Return>", self.on_enter)
        self.root.bind("<Escape>", self.on_escape)
        self.root.bind("<Delete>", self.on_delete_key)

    # --------------------------------------------------------- координаты

    def to_world(self, sx, sy) -> Point:
        return Point(float(sx), float(self.canvas.winfo_height() - sy))

    def to_screen(self, p: Point) -> tuple[float, float]:
        return p.x, self.canvas.winfo_height() - p.y

    def flat_screen(self, points) -> list[float]:
        return [c for p in points for c in self.to_screen(p)]

    def _typing_in_entry(self) -> bool:
        return isinstance(self.root.focus_get(), (tk.Entry, ttk.Entry))

    def set_status(self, text: str):
        self.status_var.set(text)

    # -------------------------------------------------------------- режимы

    def on_mode_change(self):
        mode = self.mode.get()
        self.draft.clear()
        self.reset_intersection()
        if mode == MODE_INTERSECT and self.selected is not None and len(self.selected) == 2:
            self.inter_first = self.selected
        self.hint_var.set(HINTS[mode])
        self.set_status(self._mode_prompt())
        self.redraw()

    def _mode_prompt(self) -> str:
        mode = self.mode.get()
        if mode == MODE_INTERSECT:
            if self.inter_first is None:
                return "Задайте первое ребро: ПКМ по ребру сцены или 2 клика ЛКМ"
            return "Первое ребро задано. ЛКМ — начало второго ребра"
        if mode == MODE_INSIDE:
            return "Выбран: " + self.selected.kind if self.selected else "Выберите полигон ПКМ"
        if mode == MODE_CLASSIFY:
            return "Выбрано ребро" if self.selected and len(self.selected) == 2 else "Выберите ребро ПКМ"
        return HINTS[mode].split("\n")[0]

    # --------------------------------------------------------- события мыши

    def on_left_click(self, event):
        self.canvas.focus_set()
        p = self.to_world(event.x, event.y)
        mode = self.mode.get()

        if mode == MODE_POINT:
            self.add_polygon([p])
        elif mode == MODE_EDGE:
            self.draft.append(p)
            if len(self.draft) == 2:
                self.finish_draft()
        elif mode == MODE_POLY:
            self.draft.append(p)
            self.set_status(f"Вершин: {len(self.draft)}. ПКМ или Enter — завершить")
        elif mode == MODE_SELECT:
            self.select_at(p)
        elif mode == MODE_PIVOT:
            self.fields["px"].set(f"{p.x:g}")
            self.fields["py"].set(f"{p.y:g}")
            self.set_status(f"Опорная точка: ({p.x:g}, {p.y:g})")
        elif mode == MODE_INTERSECT:
            self.intersect_click(p)
        elif mode == MODE_INSIDE:
            self.check_inside(p)
        elif mode == MODE_CLASSIFY:
            self.check_classify(p)
        self.redraw()

    def on_right_click(self, event):
        p = self.to_world(event.x, event.y)
        mode = self.mode.get()
        if mode in (MODE_POLY, MODE_EDGE):
            self.finish_draft()
        elif mode != MODE_POINT:
            self.select_at(p)
            if mode == MODE_INTERSECT and self.selected is not None and len(self.selected) == 2:
                self.reset_intersection()
                self.inter_first = self.selected
                self.set_status(self._mode_prompt())
            elif mode in (MODE_INSIDE, MODE_CLASSIFY):
                self.set_status(self._mode_prompt())
        self.redraw()

    def on_motion(self, event):
        self.cursor = self.to_world(event.x, event.y)
        self.coord_var.set(f"x = {self.cursor.x:g}, y = {self.cursor.y:g}")
        if self.mode.get() == MODE_INTERSECT and self.inter_start is not None and self.inter_end is None:
            self.update_intersection(self.cursor)
        self.redraw()

    def on_leave(self, _event):
        self.cursor = None
        self.coord_var.set("")
        self.redraw()

    def on_enter(self, _event):
        if not self._typing_in_entry() and self.mode.get() in (MODE_POLY, MODE_EDGE):
            self.finish_draft()
            self.redraw()

    def on_escape(self, _event):
        self.draft.clear()
        if self.mode.get() == MODE_INTERSECT:
            self.reset_intersection()
        self.set_status("Отменено")
        self.redraw()

    def on_delete_key(self, _event):
        if not self._typing_in_entry():
            self.delete_selected()

    # --------------------------------------------------------------- сцена

    def add_polygon(self, vertices):
        poly = Polygon(vertices)
        self.polygons.append(poly)
        self.selected = poly
        self.set_status(f"Создан объект: {poly.kind}")

    def finish_draft(self):
        if not self.draft:
            return
        self.add_polygon(self.draft)
        self.draft = []

    def select_at(self, p: Point):
        self.selected = self.polygon_at(p)
        self.set_status("Выбран: " + self.selected.kind if self.selected else "Ничего не выбрано")

    def polygon_at(self, p: Point) -> Polygon | None:
        """Верхний полигон, рядом с границей которого (или внутри которого) лежит p."""
        for poly in reversed(self.polygons):
            v = poly.vertices
            if len(v) == 1:
                if math.hypot(p.x - v[0].x, p.y - v[0].y) <= PICK_TOLERANCE:
                    return poly
                continue
            edges = zip(v, v[1:] + v[:1]) if len(v) > 2 else [(v[0], v[1])]
            if any(dist_to_segment(p, a, b) <= PICK_TOLERANCE for a, b in edges):
                return poly
        # Клик внутри полигона — если Человек 3 уже реализовал проверку
        for poly in reversed(self.polygons):
            if len(poly) >= 3:
                try:
                    if ga.point_in_polygon(p, poly) != ga.OUTSIDE:
                        return poly
                except NotImplementedError:
                    break
        return None

    def clear_scene(self):
        self.polygons.clear()
        self.selected = None
        self.draft.clear()
        self.markers.clear()
        self.reset_intersection()
        self.set_status("Сцена очищена")
        self.redraw()

    def delete_selected(self):
        if self.selected is None:
            self.set_status("Ничего не выбрано")
            return
        self.polygons.remove(self.selected)
        if self.inter_first is self.selected:
            self.reset_intersection()
        self.selected = None
        self.set_status("Объект удалён")
        self.redraw()

    def clear_markers(self):
        self.markers.clear()
        self.redraw()

    # -------------------------------------------------- преобразования (Ч.2)

    def _float(self, name: str) -> float:
        try:
            return float(self.fields[name].get().replace(",", "."))
        except ValueError:
            raise ValueError(f"Некорректное значение в поле «{name}»") from None

    def _pivot(self) -> Point:
        if not self.fields["px"].get().strip() or not self.fields["py"].get().strip():
            raise ValueError("Задайте опорную точку (режим «Опорная точка» или поля x, y)")
        return Point(self._float("px"), self._float("py"))

    def _pivot_or_none(self) -> Point | None:
        try:
            return self._pivot()
        except ValueError:
            return None

    def apply_matrix(self, make_matrix, description: str):
        """make_matrix(poly) -> Mat3; результат применяется к выбранному полигону."""
        poly = self.selected
        if poly is None:
            self.set_status("Сначала выберите полигон")
            return
        try:
            new_poly = affine.transformed(poly, make_matrix(poly))
        except NotImplementedError:
            self.set_status(NOT_IMPLEMENTED.format("affine"))
            return
        except ValueError as e:
            self.set_status(str(e))
            return
        poly.vertices = list(new_poly.vertices)
        self.set_status(description)
        if self.mode.get() == MODE_INTERSECT and self.inter_start is not None:
            self.update_intersection(self.inter_end or self.cursor or self.inter_start)
        self.redraw()

    def do_translate(self):
        self.apply_matrix(lambda poly: affine.translate(self._float("dx"), self._float("dy")),
                          "Смещено")

    def do_rotate_pivot(self):
        self.apply_matrix(lambda poly: affine.rotate_around(self._pivot(), math.radians(self._float("angle"))),
                          "Повёрнуто вокруг опорной точки")

    def do_rotate_center(self):
        self.apply_matrix(lambda poly: affine.rotate_around(affine.polygon_center(poly),
                                                            math.radians(self._float("angle"))),
                          "Повёрнуто вокруг центра")

    def do_scale_pivot(self):
        self.apply_matrix(lambda poly: affine.scale_around(self._pivot(), self._float("sx"), self._float("sy")),
                          "Отмасштабировано от опорной точки")

    def do_scale_center(self):
        self.apply_matrix(lambda poly: affine.scale_around(affine.polygon_center(poly),
                                                           self._float("sx"), self._float("sy")),
                          "Отмасштабировано от центра")

    # ------------------------------------------------------ проверки (Ч.3)

    def reset_intersection(self):
        self.inter_first = None
        self.inter_draft = []
        self.inter_start = None
        self.inter_end = None
        self.inter_point = None

    def intersect_click(self, p: Point):
        if self.inter_first is None:
            self.inter_draft.append(p)
            if len(self.inter_draft) == 2:
                self.inter_first = Polygon(self.inter_draft)
                self.inter_draft = []
            self.set_status(self._mode_prompt())
        elif self.inter_start is None or self.inter_end is not None:
            self.inter_start, self.inter_end, self.inter_point = p, None, None
            self.set_status("ЛКМ — конец второго ребра")
        else:
            self.inter_end = p
            self.update_intersection(p)

    def update_intersection(self, end: Point):
        a, b = self.inter_first.vertices
        try:
            kind, point = ga.segment_intersection(a, b, self.inter_start, end)
        except NotImplementedError:
            self.inter_point = None
            self.set_status(NOT_IMPLEMENTED.format("segment_intersection"))
            return
        self.inter_point = point if kind == ga.INTERSECT else None
        texts = {
            ga.INTERSECT: lambda: f"Точка пересечения: ({point.x:.2f}, {point.y:.2f})",
            ga.NO_INTERSECTION: lambda: "Рёбра не пересекаются",
            ga.PARALLEL: lambda: "Рёбра параллельны",
            ga.COLLINEAR: lambda: "Рёбра на одной прямой, общих точек нет",
            ga.OVERLAP: lambda: "Рёбра на одной прямой и перекрываются",
        }
        self.set_status(texts.get(kind, lambda: f"Результат: {kind}")())

    def check_inside(self, p: Point):
        poly = self.selected
        if poly is None or len(poly) < 3:
            self.set_status("Выберите ПКМ полигон с 3+ вершинами")
            return
        try:
            convex = ga.is_convex(poly)
            result = ga.point_in_convex_polygon(p, poly) if convex else ga.point_in_polygon(p, poly)
        except NotImplementedError:
            self.set_status(NOT_IMPLEMENTED.format("geom_algos"))
            return
        text, color = {
            ga.INSIDE: ("внутри", "#2a9d3f"),
            ga.OUTSIDE: ("снаружи", COLOR_HIT),
            ga.ON_BOUNDARY: ("на границе", "#e9a400"),
        }.get(result, (str(result), "gray"))
        self.markers.append((p, color))
        kind = "Выпуклый" if convex else "Невыпуклый"
        self.set_status(f"{kind} полигон: точка ({p.x:g}, {p.y:g}) {text}")

    def check_classify(self, p: Point):
        poly = self.selected
        if poly is None or len(poly) != 2:
            self.set_status("Выберите ребро ПКМ")
            return
        a, b = poly.vertices
        try:
            result = ga.classify_point(p, a, b)
        except NotImplementedError:
            self.set_status(NOT_IMPLEMENTED.format("classify_point"))
            return
        text, color = {
            ga.LEFT: ("слева", "#2a9d3f"),
            ga.RIGHT: ("справа", COLOR_HIT),
            ga.ON_LINE: ("на прямой", "#e9a400"),
        }.get(result, (str(result), "gray"))
        self.markers.append((p, color))
        self.set_status(f"Точка ({p.x:g}, {p.y:g}) {text} от ребра")

    # ----------------------------------------------------------- отрисовка

    def redraw(self):
        c = self.canvas
        c.delete("all")
        for poly in self.polygons:
            self.draw_polygon(poly, poly is self.selected)
        self.draw_selected_center()
        self.draw_draft()
        if self.mode.get() == MODE_INTERSECT:
            self.draw_intersection()
        self.draw_pivot()
        for p, color in self.markers:
            self.draw_dot(p, 4, color, outline="black")

    def draw_dot(self, p: Point, r: float, fill: str, outline: str = ""):
        x, y = self.to_screen(p)
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=outline)

    def draw_cross(self, p: Point, r: float, color: str, width: int = 2):
        x, y = self.to_screen(p)
        self.canvas.create_line(x - r, y, x + r, y, fill=color, width=width)
        self.canvas.create_line(x, y - r, x, y + r, fill=color, width=width)

    def draw_polygon(self, poly: Polygon, selected: bool):
        color = COLOR_SELECTED if selected else COLOR_POLY
        width = 3 if selected else 2
        v = poly.vertices
        if len(v) == 1:
            self.draw_dot(v[0], 5, color)
            return
        if len(v) == 2:
            self.canvas.create_line(*self.flat_screen(v), fill=color, width=width,
                                    arrow=tk.LAST, arrowshape=(12, 14, 5))
        else:
            self.canvas.create_polygon(*self.flat_screen(v), outline=color, width=width,
                                       fill=COLOR_SELECTED_FILL if selected else COLOR_POLY_FILL)
        for p in v:
            self.draw_dot(p, 3, color)

    def draw_selected_center(self):
        if self.selected is None or len(self.selected) < 2:
            return
        try:
            center = affine.polygon_center(self.selected)
        except NotImplementedError:
            return
        self.draw_cross(center, 5, "#777", width=1)

    def draw_draft(self):
        if not self.draft:
            return
        pts = self.draft + ([self.cursor] if self.cursor else [])
        if len(pts) >= 2:
            self.canvas.create_line(*self.flat_screen(pts), fill=COLOR_DRAFT, width=2)
        if self.mode.get() == MODE_POLY and self.cursor and len(self.draft) >= 2:
            self.canvas.create_line(*self.flat_screen([self.cursor, self.draft[0]]),
                                    fill=COLOR_DRAFT, dash=(4, 4))
        for p in self.draft:
            self.draw_dot(p, 3, COLOR_DRAFT)

    def draw_intersection(self):
        if self.inter_draft:
            pts = self.inter_draft + ([self.cursor] if self.cursor else [])
            if len(pts) >= 2:
                self.canvas.create_line(*self.flat_screen(pts), fill=COLOR_EDGE1, width=3, dash=(6, 3))
            self.draw_dot(self.inter_draft[0], 3, COLOR_EDGE1)
        if self.inter_first is not None:
            self.canvas.create_line(*self.flat_screen(self.inter_first.vertices), fill=COLOR_EDGE1, width=4)
        if self.inter_start is not None:
            end = self.inter_end or self.cursor
            if end is not None:
                self.canvas.create_line(*self.flat_screen([self.inter_start, end]), fill=COLOR_EDGE2, width=3,
                                        dash=() if self.inter_end else (6, 3))
            self.draw_dot(self.inter_start, 3, COLOR_EDGE2)
        if self.inter_point is not None:
            self.draw_dot(self.inter_point, 6, COLOR_HIT, outline="black")

    def draw_pivot(self):
        p = self._pivot_or_none()
        if p is None:
            return
        self.draw_cross(p, 8, COLOR_PIVOT)
        x, y = self.to_screen(p)
        self.canvas.create_text(x + 10, y - 10, text="P", fill=COLOR_PIVOT, font=("Segoe UI", 10, "bold"))
