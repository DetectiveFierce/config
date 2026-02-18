#!/usr/bin/env python3
import json
import os
import subprocess
import uuid
from pathlib import Path
import tkinter as tk

NOTE_BG = "#3b5012"
GALLERY_BG = "#1f2b0f"
NOTE_FG = "#d7e9b0"
NOTE_CURSOR = "#a5c73a"
NOTE_SELECT_BG = "#89a84d"
NOTE_SELECT_FG = "#172304"
THUMB_BG = NOTE_BG
ICON_HOVER = "#b6d872"
THUMB_RADIUS = 16

WINDOW_WIDTH = 860
WINDOW_HEIGHT = 620
WINDOW_RATIO = WINDOW_WIDTH / WINDOW_HEIGHT

ANIM_DURATION_MS = 320
ANIM_FRAME_MS = 20
ANIM_MAX_NOTES = 12

EDITOR_OUTER_PAD = 10
EDITOR_SIDEBAR_WIDTH = 68
EDITOR_SIDEBAR_GAP = 6
EDITOR_EDGE_PAD = 10
EDITOR_ICON_SIZE = 42
EDITOR_ICON_STROKE = 4

SVG_RECOLOR_MAP = (
    "#FCD34D",
    "#F59E0B",
    "#FDE68A",
    "#FEF3C7",
    "#D97706",
)
ICON_RENDER_VERSION = "v3"


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    path = Path(base) / "sticky-note"
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = data_dir()
NOTES_DIR = DATA_DIR / "notes"
STATE_FILE = DATA_DIR / "state.json"
LEGACY_NOTE_FILE = DATA_DIR / "note.txt"
CACHE_DIR = DATA_DIR / "cache"
SCRIPT_DIR = Path(__file__).resolve().parent
NOTES_ICON_SVG = SCRIPT_DIR / "assets" / "notes.svg"


def note_file(note_id: str) -> Path:
    return NOTES_DIR / f"{note_id}.txt"


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def new_note_id() -> str:
    return uuid.uuid4().hex


def save_state(note_ids: list[str], active_id: str) -> None:
    payload = {"note_ids": note_ids, "active_id": active_id}
    STATE_FILE.write_text(json.dumps(payload), encoding="utf-8")


def bootstrap_state() -> tuple[list[str], str]:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    existing = [p.stem for p in NOTES_DIR.glob("*.txt") if p.is_file()]
    existing.sort(key=lambda nid: note_file(nid).stat().st_mtime)

    if not existing:
        content = read_file(LEGACY_NOTE_FILE) if LEGACY_NOTE_FILE.exists() else ""
        first = new_note_id()
        write_file(note_file(first), content)
        existing = [first]

    note_ids = existing.copy()
    active_id = note_ids[0]

    if STATE_FILE.exists():
        try:
            payload = json.loads(read_file(STATE_FILE))
            saved_ids = [str(nid) for nid in payload.get("note_ids", [])]
            filtered_saved = [nid for nid in saved_ids if note_file(nid).exists()]
            merged = filtered_saved + [nid for nid in note_ids if nid not in filtered_saved]
            if merged:
                note_ids = merged
            saved_active = str(payload.get("active_id", ""))
            if saved_active in note_ids:
                active_id = saved_active
        except Exception:
            pass

    save_state(note_ids, active_id)
    return note_ids, active_id


def render_colored_svg_icon(source_svg: Path, color_hex: str, output_png: Path, size: int = 26) -> bool:
    if not source_svg.exists():
        return False

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    source = read_file(source_svg)
    if not source:
        return False

    # Keep stacked-note depth by using related shades instead of a single flat tint.
    palette = {
        "#FCD34D": _mix_color(color_hex, NOTE_BG, 0.42),  # back note fill
        "#FDE68A": _mix_color(color_hex, NOTE_BG, 0.30),  # middle note fill
        "#FEF3C7": _mix_color(color_hex, NOTE_BG, 0.16),  # front note fill
        "#F59E0B": _mix_color(color_hex, NOTE_BG, 0.55),  # note strokes
        "#D97706": _mix_color(color_hex, NOTE_BG, 0.62),  # front lines
    }

    for old, new in palette.items():
        source = source.replace(old, new).replace(old.lower(), new).replace(old.upper(), new)

    tmp_svg = output_png.with_suffix(".tmp.svg")
    try:
        write_file(tmp_svg, source)
        subprocess.run(
            [
                "rsvg-convert",
                "-w",
                str(size),
                "-h",
                str(size),
                str(tmp_svg),
                "-o",
                str(output_png),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return output_png.exists()
    except Exception:
        return False
    finally:
        try:
            tmp_svg.unlink()
        except Exception:
            pass


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def _mix_color(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex(
        (
            int(ar + (br - ar) * t),
            int(ag + (bg - ag) * t),
            int(ab + (bb - ab) * t),
        )
    )


def _ease_in_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_rect(start: tuple[float, float, float, float], end: tuple[float, float, float, float], t: float):
    return (
        _lerp(start[0], end[0], t),
        _lerp(start[1], end[1], t),
        _lerp(start[2], end[2], t),
        _lerp(start[3], end[3], t),
    )


class StickyNoteApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.save_job: str | None = None
        self.note_ids, self.current_note_id = bootstrap_state()
        self.in_gallery = False
        self.gallery_edit_mode = False
        self.animating = False
        self.thumb_frames: dict[str, tk.Widget] = {}
        self._gallery_refresh_pending = False
        self._gallery_refresh_force = False
        self._gallery_layout_key: tuple | None = None
        self._last_thumb_canvas_width = 0
        self._last_editor_text_rect: tuple[float, float, float, float] | None = None
        self._last_editor_window_size: tuple[int, int] | None = None

        self.notes_icon_default = self._load_notes_icon(NOTE_FG)
        self.notes_icon_hover = self._load_notes_icon(ICON_HOVER)

        root.title("Sticky Note")
        root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        root.minsize(560, 380)
        root.configure(bg=NOTE_BG)

        try:
            root.wm_class("sticky-note", "StickyNote")
        except Exception:
            pass

        self.container = tk.Frame(root, bg=NOTE_BG)
        self.container.pack(fill="both", expand=True)

        self.editor_frame = tk.Frame(self.container, bg=NOTE_BG)
        self.gallery_frame = tk.Frame(self.container, bg=GALLERY_BG)

        self._build_editor_ui()
        self._build_gallery_ui()

        self._apply_editor_view(self.current_note_id)

        self.root.bind("<Escape>", self._on_escape)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _load_notes_icon(self, color: str) -> tk.PhotoImage | None:
        if not NOTES_ICON_SVG.exists():
            return None

        png_path = CACHE_DIR / f"notes_icon_{ICON_RENDER_VERSION}_{color.lstrip('#')}.png"
        try:
            needs_render = (not png_path.exists()) or (png_path.stat().st_mtime < NOTES_ICON_SVG.stat().st_mtime)
        except Exception:
            needs_render = True

        if needs_render and not render_colored_svg_icon(NOTES_ICON_SVG, color, png_path, size=EDITOR_ICON_SIZE):
            return None

        try:
            return tk.PhotoImage(file=str(png_path))
        except Exception:
            return None

    def _build_editor_ui(self) -> None:
        editor_body = tk.Frame(self.editor_frame, bg=NOTE_BG)
        editor_body.pack(fill="both", expand=True, padx=EDITOR_OUTER_PAD, pady=EDITOR_OUTER_PAD)

        sidebar = tk.Frame(editor_body, bg=NOTE_BG, width=EDITOR_SIDEBAR_WIDTH)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        self.gallery_icon_button = self._notes_svg_button(sidebar, self._zoom_out_to_gallery)
        self.gallery_icon_button.pack(side="top", anchor="ne", padx=(0, EDITOR_EDGE_PAD), pady=(EDITOR_EDGE_PAD, 0))

        self.text = tk.Text(
            editor_body,
            wrap="word",
            undo=True,
            font=("Iosevka", 16),
            padx=12,
            pady=6,
            bg=NOTE_BG,
            fg=NOTE_FG,
            insertbackground=NOTE_CURSOR,
            insertwidth=2,
            selectbackground=NOTE_SELECT_BG,
            selectforeground=NOTE_SELECT_FG,
            inactiveselectbackground=NOTE_SELECT_BG,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self.text.pack(side="left", fill="both", expand=True, padx=(0, EDITOR_SIDEBAR_GAP))

        self.text.bind("<<Modified>>", self._on_modified)

        self.plus_button = tk.Canvas(
            sidebar,
            width=EDITOR_ICON_SIZE,
            height=EDITOR_ICON_SIZE,
            bg=NOTE_BG,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            relief="flat",
        )
        c = EDITOR_ICON_SIZE / 2
        o = EDITOR_ICON_SIZE * 0.28
        self.plus_button.create_line(c, c - o, c, c + o, fill=NOTE_CURSOR, width=EDITOR_ICON_STROKE, capstyle="round", tags=("plus",))
        self.plus_button.create_line(c - o, c, c + o, c, fill=NOTE_CURSOR, width=EDITOR_ICON_STROKE, capstyle="round", tags=("plus",))

        def plus_enter(_event=None):
            for item in self.plus_button.find_withtag("plus"):
                self.plus_button.itemconfigure(item, fill=ICON_HOVER)

        def plus_leave(_event=None):
            for item in self.plus_button.find_withtag("plus"):
                self.plus_button.itemconfigure(item, fill=NOTE_CURSOR)

        self.plus_button.bind("<Enter>", plus_enter)
        self.plus_button.bind("<Leave>", plus_leave)
        self.plus_button.bind("<Button-1>", lambda _event: self._create_new_note())
        self.plus_button.pack(side="bottom", anchor="se", padx=(0, EDITOR_EDGE_PAD), pady=(0, EDITOR_EDGE_PAD))

    def _build_gallery_ui(self) -> None:
        top = tk.Frame(self.gallery_frame, bg=GALLERY_BG)
        top.pack(fill="x", padx=10, pady=(10, 6))

        self.gallery_cancel_button = self._icon_button(top, self._draw_chevron_left, self._exit_gallery_edit_mode)
        self.gallery_cancel_button.pack(side="left")
        self.gallery_cancel_button.pack_forget()

        self.gallery_edit_button = self._icon_button(top, self._draw_pencil_icon, self._enter_gallery_edit_mode)
        self.gallery_edit_button.pack(side="right")

        body = tk.Frame(self.gallery_frame, bg=GALLERY_BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.thumb_canvas = tk.Canvas(body, bg=GALLERY_BG, highlightthickness=0, bd=0)
        self.thumb_scroll = tk.Scrollbar(body, orient="vertical", command=self.thumb_canvas.yview)
        self.thumb_canvas.configure(yscrollcommand=self.thumb_scroll.set)
        self._theme_scrollbar(self.thumb_scroll)

        self.thumb_scroll.pack(side="right", fill="y")
        self.thumb_canvas.pack(side="left", fill="both", expand=True)

        self.thumb_container = tk.Frame(self.thumb_canvas, bg=GALLERY_BG)
        self.thumb_window = self.thumb_canvas.create_window((0, 0), window=self.thumb_container, anchor="nw")

        self.thumb_container.bind("<Configure>", self._on_thumb_container_configure)
        self.thumb_canvas.bind("<Configure>", self._on_thumb_canvas_configure)
        self.thumb_canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _theme_scrollbar(self, scrollbar: tk.Scrollbar) -> None:
        themed_opts = {
            "background": "#516821",
            "activebackground": "#7e9c42",
            "troughcolor": "#23320d",
            "relief": "flat",
            "borderwidth": 0,
            "elementborderwidth": 0,
            "highlightthickness": 0,
            "width": 12,
        }
        for key, value in themed_opts.items():
            try:
                scrollbar.configure(**{key: value})
            except tk.TclError:
                continue

    def _queue_gallery_refresh(self, force: bool = False) -> None:
        if force:
            self._gallery_refresh_force = True
        if self.animating:
            return
        if self._gallery_refresh_pending:
            return
        self._gallery_refresh_pending = True
        self.root.after_idle(self._run_queued_gallery_refresh)

    def _run_queued_gallery_refresh(self) -> None:
        self._gallery_refresh_pending = False
        force = self._gallery_refresh_force
        self._gallery_refresh_force = False
        if self.in_gallery and not self.animating:
            self._refresh_gallery(force=force)

    def _effective_gallery_canvas_width(self) -> int:
        raw_width = self.thumb_canvas.winfo_width()
        if raw_width > 40:
            return raw_width

        root_width = max(self.root.winfo_width(), WINDOW_WIDTH)
        scroll_width = self.thumb_scroll.winfo_width() or self.thumb_scroll.winfo_reqwidth() or 12
        estimated = root_width - scroll_width - 22
        return max(raw_width, estimated)

    def _estimate_editor_text_rect(self) -> tuple[float, float, float, float]:
        root_w = max(self.root.winfo_width(), WINDOW_WIDTH)
        root_h = max(self.root.winfo_height(), WINDOW_HEIGHT)

        if self._last_editor_text_rect and self._last_editor_window_size:
            last_w, last_h = self._last_editor_window_size
            if last_w > 0 and last_h > 0:
                sx = root_w / last_w
                sy = root_h / last_h
                x1, y1, x2, y2 = self._last_editor_text_rect
                return (x1 * sx, y1 * sy, x2 * sx, y2 * sy)

        left = float(EDITOR_OUTER_PAD)
        top = float(EDITOR_OUTER_PAD)
        right = float(root_w) - float(EDITOR_OUTER_PAD + EDITOR_SIDEBAR_WIDTH + EDITOR_SIDEBAR_GAP)
        bottom = float(root_h) - float(EDITOR_OUTER_PAD)
        return (left, top, right, bottom)

    def _on_thumb_container_configure(self, _event=None) -> None:
        self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))

    def _on_thumb_canvas_configure(self, event=None) -> None:
        if event is not None:
            self.thumb_canvas.itemconfigure(self.thumb_window, width=event.width)
            if event.width != self._last_thumb_canvas_width:
                self._last_thumb_canvas_width = event.width
                self._queue_gallery_refresh()
                return
        if self.in_gallery and not self.animating:
            self._queue_gallery_refresh()

    def _on_mousewheel(self, event) -> None:
        if self.in_gallery:
            self.thumb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _notes_svg_button(self, parent: tk.Widget, command):
        bg = str(parent.cget("bg"))
        if self.notes_icon_default is None:
            return self._icon_button(parent, self._draw_notes_icon_fallback, command)

        button = tk.Label(
            parent,
            image=self.notes_icon_default,
            bg=bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )

        def on_enter(_event=None):
            if self.notes_icon_hover is not None:
                button.configure(image=self.notes_icon_hover)

        def on_leave(_event=None):
            button.configure(image=self.notes_icon_default)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", lambda _event: command())
        return button

    def _icon_button(self, parent: tk.Widget, drawer, command):
        canvas = tk.Canvas(
            parent,
            width=34,
            height=34,
            bg=str(parent.cget("bg")),
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            relief="flat",
        )
        drawer(canvas, NOTE_FG)

        def on_enter(_event=None):
            self._set_icon_color(canvas, ICON_HOVER)

        def on_leave(_event=None):
            self._set_icon_color(canvas, NOTE_FG)

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", lambda _event: command())
        return canvas

    def _set_icon_color(self, canvas: tk.Canvas, color: str) -> None:
        for item in canvas.find_withtag("icon"):
            item_type = canvas.type(item)
            if item_type in {"line", "text"}:
                canvas.itemconfigure(item, fill=color)
            if item_type in {"rectangle", "oval", "polygon"}:
                canvas.itemconfigure(item, outline=color)

    def _draw_notes_icon_fallback(self, canvas: tk.Canvas, color: str) -> None:
        canvas.delete("all")
        canvas.create_rectangle(13, 4, 27, 18, outline=color, width=2, tags=("icon",))
        canvas.create_rectangle(9, 8, 23, 22, outline=color, width=2, tags=("icon",))
        canvas.create_rectangle(5, 12, 19, 26, outline=color, width=2, tags=("icon",))
        canvas.create_line(8, 16, 16, 16, fill=color, width=2, capstyle="round", tags=("icon",))
        canvas.create_line(8, 20, 16, 20, fill=color, width=2, capstyle="round", tags=("icon",))
        canvas.create_line(8, 24, 13, 24, fill=color, width=2, capstyle="round", tags=("icon",))

    def _draw_pencil_icon(self, canvas: tk.Canvas, color: str) -> None:
        canvas.delete("all")
        canvas.create_polygon(8, 25, 10, 20, 22, 8, 26, 12, 14, 24, outline=color, fill="", width=2, tags=("icon",))
        canvas.create_line(21, 9, 25, 13, fill=color, width=2, tags=("icon",))
        canvas.create_line(8, 25, 14, 24, fill=color, width=2, tags=("icon",))

    def _draw_chevron_left(self, canvas: tk.Canvas, color: str) -> None:
        canvas.delete("all")
        canvas.create_line(21, 8, 13, 17, fill=color, width=3, capstyle="round", tags=("icon",))
        canvas.create_line(13, 17, 21, 26, fill=color, width=3, capstyle="round", tags=("icon",))

    def _widget_rect(self, widget: tk.Widget) -> tuple[float, float, float, float]:
        self.root.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        x1 = widget.winfo_rootx() - rx
        y1 = widget.winfo_rooty() - ry
        x2 = x1 + widget.winfo_width()
        y2 = y1 + widget.winfo_height()
        return float(x1), float(y1), float(x2), float(y2)

    def _scaled_rect(self, rect: tuple[float, float, float, float], scale: float) -> tuple[float, float, float, float]:
        x1, y1, x2, y2 = rect
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        w = (x2 - x1) * scale
        h = (y2 - y1) * scale
        return cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0

    def _create_overlay(self, bg: str) -> tk.Canvas:
        overlay = tk.Canvas(self.root, bg=bg, highlightthickness=0, bd=0)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.tk.call("raise", str(overlay))
        return overlay

    def _create_overlay_card(
        self,
        overlay: tk.Canvas,
        note_id: str,
        rect: tuple[float, float, float, float],
        active: bool,
        show_text: bool,
    ) -> dict[str, int]:
        x1, y1, x2, y2 = rect
        rect_id = self._rounded_rect(
            overlay,
            x1,
            y1,
            x2,
            y2,
            radius=min(THUMB_RADIUS, int((y2 - y1) / 4)),
            fill=THUMB_BG,
            outline="",
            width=0,
        )
        text_id = overlay.create_text(
            x1 + 10,
            y1 + 10,
            text=self._thumbnail_text(note_id),
            fill=NOTE_FG,
            anchor="nw",
            justify="left",
            font=("Iosevka", 11),
            width=max(80, int((x2 - x1) - 20)),
        )
        if not show_text:
            overlay.itemconfigure(text_id, state="hidden")
        return {"rect": rect_id, "text": text_id, "show_text": show_text}

    def _place_overlay_card(
        self,
        overlay: tk.Canvas,
        card: dict[str, int],
        rect: tuple[float, float, float, float],
    ) -> None:
        x1, y1, x2, y2 = rect
        points = self._rounded_rect_points(
            x1,
            y1,
            x2,
            y2,
            min(THUMB_RADIUS, int((y2 - y1) / 4)),
        )
        overlay.coords(card["rect"], *points)
        overlay.coords(card["text"], x1 + 10, y1 + 10)
        overlay.itemconfigure(card["text"], width=max(80, int((x2 - x1) - 20)))

    def _rounded_rect_points(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float,
    ) -> list[float]:
        r = max(0.0, min(radius, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
        return [
            x1 + r, y1,
            x1 + r, y1,
            x2 - r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1 + r,
            x1, y1,
        ]

    def _rounded_rect(
        self,
        canvas: tk.Canvas,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float,
        fill: str,
        outline: str,
        width: int,
    ) -> int:
        points = self._rounded_rect_points(x1, y1, x2, y2, radius)
        return canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=10,
            fill=fill,
            outline=outline,
            width=width,
        )

    def _animation_note_ids(self, focus_note_id: str) -> list[str]:
        if focus_note_id not in self.note_ids:
            return self.note_ids[:ANIM_MAX_NOTES]
        ordered = [focus_note_id] + [nid for nid in self.note_ids if nid != focus_note_id]
        return ordered[:ANIM_MAX_NOTES]

    def _gallery_rects(self) -> dict[str, tuple[float, float, float, float]]:
        rects: dict[str, tuple[float, float, float, float]] = {}
        for note_id, frame in self.thumb_frames.items():
            if frame.winfo_exists():
                rects[note_id] = self._widget_rect(frame)
        return rects

    def _run_overlay_animation(
        self,
        overlay: tk.Canvas,
        cards: dict[str, dict[str, int]],
        start_rects: dict[str, tuple[float, float, float, float]],
        end_rects: dict[str, tuple[float, float, float, float]],
        bg_from: str,
        bg_to: str,
        focus_note_id: str,
        direction: str,
    ) -> None:
        steps = max(12, int(ANIM_DURATION_MS / ANIM_FRAME_MS))
        note_ids = list(cards.keys())

        for step in range(steps + 1):
            t = step / steps
            e = _ease_in_out_cubic(t)
            overlay.configure(bg=_mix_color(bg_from, bg_to, e))

            for note_id in note_ids:
                start = start_rects[note_id]
                end = end_rects.get(note_id, start)
                rect = _lerp_rect(start, end, e)
                card = cards[note_id]
                self._place_overlay_card(overlay, card, rect)

                width = rect[2] - rect[0]
                is_focus = note_id == focus_note_id

                if direction == "out":
                    text_color = NOTE_FG if is_focus else NOTE_FG
                    overlay.itemconfigure(card["rect"], fill=THUMB_BG)
                    overlay.itemconfigure(card["rect"], outline="")
                    if is_focus:
                        overlay.itemconfigure(card["text"], fill=text_color)
                else:
                    if is_focus:
                        overlay.itemconfigure(card["rect"], fill=THUMB_BG)
                        overlay.itemconfigure(card["rect"], outline="")
                        overlay.itemconfigure(card["text"], fill=NOTE_FG)
                    else:
                        dissolve = min(1.0, max(0.0, (e - 0.12) / 0.88))
                        overlay.itemconfigure(card["rect"], fill=_mix_color(THUMB_BG, bg_to, dissolve))
                        overlay.itemconfigure(card["rect"], outline="")
                        overlay.itemconfigure(card["text"], state="hidden")

                if not card.get("show_text", True):
                    overlay.itemconfigure(card["text"], state="hidden")
                elif width < 150:
                    overlay.itemconfigure(card["text"], state="hidden")
                elif direction == "in" and not is_focus and e > 0.75:
                    overlay.itemconfigure(card["text"], state="hidden")
                else:
                    overlay.itemconfigure(card["text"], state="normal")

            if focus_note_id in cards:
                overlay.tag_raise(cards[focus_note_id]["rect"])
                overlay.tag_raise(cards[focus_note_id]["text"])

            self.root.update_idletasks()
            if step < steps:
                self.root.after(ANIM_FRAME_MS)

        # Let the final keyframe settle before removing the overlay.
        self.root.update_idletasks()

    def _animate_editor_to_gallery(self) -> None:
        if self.animating:
            return

        self.animating = True
        overlay = None
        try:
            self.root.update_idletasks()
            start_focus_rect = self._widget_rect(self.text)
            collapsed = self._scaled_rect(start_focus_rect, 0.22)
            note_ids = self._animation_note_ids(self.current_note_id)

            overlay = self._create_overlay(NOTE_BG)
            self.root.update_idletasks()
            cards: dict[str, dict[str, int]] = {}
            start_rects: dict[str, tuple[float, float, float, float]] = {}

            for note_id in note_ids:
                start_rect = start_focus_rect if note_id == self.current_note_id else collapsed
                start_rects[note_id] = start_rect
                cards[note_id] = self._create_overlay_card(
                    overlay,
                    note_id,
                    start_rect,
                    active=(note_id == self.current_note_id),
                    show_text=(note_id == self.current_note_id),
                )

            self._apply_gallery_view(sync_refresh=True)
            self.root.update_idletasks()
            target_rects = self._gallery_rects()

            for note_id in note_ids:
                if note_id not in target_rects:
                    target_rects[note_id] = collapsed

            self._run_overlay_animation(
                overlay,
                cards,
                start_rects,
                target_rects,
                NOTE_BG,
                GALLERY_BG,
                self.current_note_id,
                "out",
            )
            # Keep the underlying gallery in sync with the final animated frame.
            self._refresh_gallery(force=True)
            self.root.update_idletasks()
        finally:
            if overlay is not None:
                overlay.destroy()
            self.animating = False

    def _animate_gallery_to_editor(
        self,
        note_id: str,
        source_rect: tuple[float, float, float, float] | None,
    ) -> None:
        if self.animating:
            return

        self.animating = True
        overlay = None
        try:
            self.root.update_idletasks()
            note_ids = self._animation_note_ids(note_id)
            source_rects = self._gallery_rects()
            if source_rect is not None:
                source_rects[note_id] = source_rect

            if note_id not in source_rects:
                canvas_rect = self._widget_rect(self.thumb_canvas)
                source_rects[note_id] = self._scaled_rect(canvas_rect, 0.4)

            overlay = self._create_overlay(GALLERY_BG)
            self.root.update_idletasks()
            cards: dict[str, dict[str, int]] = {}
            start_rects: dict[str, tuple[float, float, float, float]] = {}

            for existing_id in note_ids:
                start = source_rects.get(existing_id, source_rects[note_id])
                start_rects[existing_id] = start
                cards[existing_id] = self._create_overlay_card(
                    overlay,
                    existing_id,
                    start,
                    active=(existing_id == note_id),
                    show_text=(existing_id == note_id),
                )

            target_focus = self._estimate_editor_text_rect()
            collapsed = self._scaled_rect(target_focus, 0.2)
            end_rects = {
                existing_id: (target_focus if existing_id == note_id else collapsed)
                for existing_id in note_ids
            }

            self._run_overlay_animation(
                overlay,
                cards,
                start_rects,
                end_rects,
                GALLERY_BG,
                NOTE_BG,
                note_id,
                "in",
            )
            # Switch the real widgets while the overlay still hides layout changes.
            self._apply_editor_view(note_id)
            self.root.update_idletasks()
        finally:
            if overlay is not None:
                overlay.destroy()
            self.animating = False

    def _create_note_file(self, content: str = "") -> str:
        note_id = new_note_id()
        write_file(note_file(note_id), content)
        return note_id

    def _load_note(self, note_id: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", read_file(note_file(note_id)))
        self.text.edit_modified(False)

    def _save_current_note(self) -> None:
        write_file(note_file(self.current_note_id), self.text.get("1.0", "end-1c"))

    def _schedule_save(self) -> None:
        if self.save_job is not None:
            self.root.after_cancel(self.save_job)
        self.save_job = self.root.after(250, self._flush_save)

    def _flush_save(self) -> None:
        self.save_job = None
        self._save_current_note()

    def _on_modified(self, _event=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self._schedule_save()

    def _persist_state(self) -> None:
        save_state(self.note_ids, self.current_note_id)

    def _apply_editor_view(self, note_id: str) -> None:
        self.in_gallery = False
        self.current_note_id = note_id
        self._persist_state()
        self.root.configure(bg=NOTE_BG)
        self.container.configure(bg=NOTE_BG)
        self.gallery_frame.pack_forget()
        if not self.editor_frame.winfo_ismapped():
            self.editor_frame.pack(fill="both", expand=True)
        self._load_note(note_id)
        self.text.focus_set()
        self.root.update_idletasks()
        self._last_editor_text_rect = self._widget_rect(self.text)
        self._last_editor_window_size = (self.root.winfo_width(), self.root.winfo_height())

    def _apply_gallery_view(self, sync_refresh: bool = False) -> None:
        self.in_gallery = True
        self.gallery_edit_mode = False
        self._update_gallery_controls()
        self._flush_if_pending()
        self.root.configure(bg=GALLERY_BG)
        self.container.configure(bg=GALLERY_BG)
        self.editor_frame.pack_forget()
        if not self.gallery_frame.winfo_ismapped():
            self.gallery_frame.pack(fill="both", expand=True)
        if sync_refresh:
            self._gallery_refresh_pending = False
            self._gallery_refresh_force = False
            self._refresh_gallery(force=True)
        else:
            self._queue_gallery_refresh(force=True)
        self.thumb_canvas.yview_moveto(0)
        self.root.update_idletasks()

    def _create_new_note(self) -> None:
        if self.animating:
            return
        self._flush_if_pending()
        new_id = self._create_note_file("")
        self.note_ids.insert(0, new_id)
        self.current_note_id = new_id
        self._persist_state()
        self._show_editor(new_id)

    def _zoom_out_to_gallery(self) -> None:
        if self.animating:
            return
        self._flush_if_pending()
        self._show_gallery(animate=True)

    def _zoom_in_to_note(self, note_id: str) -> None:
        if note_id not in self.note_ids or self.animating:
            return

        source_rect = None
        frame = self.thumb_frames.get(note_id)
        if frame is not None and frame.winfo_exists():
            source_rect = self._widget_rect(frame)

        if self.gallery_edit_mode:
            self.gallery_edit_mode = False
            self._update_gallery_controls()

        self._show_editor(note_id, animate=self.in_gallery, source_rect=source_rect)

    def _show_editor(
        self,
        note_id: str,
        animate: bool = True,
        source_rect: tuple[float, float, float, float] | None = None,
    ) -> None:
        if animate and self.in_gallery:
            self._animate_gallery_to_editor(note_id, source_rect)
        else:
            self._apply_editor_view(note_id)

    def _show_gallery(self, animate: bool = True) -> None:
        if self.in_gallery:
            self._apply_gallery_view()
            return
        if animate:
            self._animate_editor_to_gallery()
        else:
            self._apply_gallery_view()

    def _visual_order(self, columns: int) -> list[str]:
        if not self.note_ids:
            return []
        if self.current_note_id not in self.note_ids:
            return self.note_ids.copy()

        others = [nid for nid in self.note_ids if nid != self.current_note_id]
        total = len(self.note_ids)
        center_idx = min(total - 1, max(0, columns // 2))
        ordered: list[str | None] = [None] * total
        ordered[center_idx] = self.current_note_id

        idx = 0
        for slot in range(total):
            if ordered[slot] is None:
                ordered[slot] = others[idx]
                idx += 1

        return [nid for nid in ordered if nid is not None]

    def _refresh_gallery(self, force: bool = False) -> None:
        canvas_width = max(self._effective_gallery_canvas_width(), 1)
        pad = 14
        min_thumb_w = 210
        max_thumb_w = 260

        columns = max(1, canvas_width // (min_thumb_w + pad))
        available = canvas_width - (pad * (columns + 1))
        if available <= 0:
            available = canvas_width - (pad * 2)
        thumb_w = max(min_thumb_w, min(max_thumb_w, int(available / columns)))
        thumb_h = max(120, int(thumb_w / WINDOW_RATIO))

        order = self._visual_order(columns)
        layout_key = (canvas_width, columns, thumb_w, thumb_h, tuple(order), self.gallery_edit_mode)
        if not force and layout_key == self._gallery_layout_key:
            return
        self._gallery_layout_key = layout_key
        self._last_thumb_canvas_width = canvas_width

        for child in self.thumb_container.winfo_children():
            child.destroy()
        self.thumb_frames = {}

        for col in range(columns):
            self.thumb_container.grid_columnconfigure(col, weight=1)

        for index, note_id in enumerate(order):
            row = index // columns
            col = index % columns
            frame = tk.Canvas(
                self.thumb_container,
                bg=GALLERY_BG,
                width=thumb_w,
                height=thumb_h,
                highlightthickness=0,
                bd=0,
                cursor="hand2",
            )
            frame.grid(row=row, column=col, padx=pad // 2, pady=pad // 2, sticky="n")
            self.thumb_frames[note_id] = frame

            self._rounded_rect(
                frame,
                1,
                1,
                thumb_w - 1,
                thumb_h - 1,
                radius=THUMB_RADIUS,
                fill=THUMB_BG,
                outline="",
                width=0,
            )

            preview = self._thumbnail_text(note_id)
            text_id = frame.create_text(
                12,
                12,
                text=preview,
                justify="left",
                anchor="nw",
                fill=NOTE_FG,
                font=("Iosevka", 11),
                width=max(80, thumb_w - 24),
            )

            frame.bind("<Button-1>", lambda _e, nid=note_id: self._on_thumbnail_click(nid))
            frame.tag_bind(text_id, "<Button-1>", lambda _e, nid=note_id: self._on_thumbnail_click(nid))

            if self.gallery_edit_mode:
                del_bg = frame.create_oval(
                    thumb_w - 28,
                    8,
                    thumb_w - 8,
                    28,
                    fill=NOTE_FG,
                    outline="",
                    width=0,
                    tags=("delete",),
                )
                del_txt = frame.create_text(
                    thumb_w - 18,
                    18,
                    text="✕",
                    fill=NOTE_BG,
                    font=("Iosevka", 11, "bold"),
                    tags=("delete",),
                )
                frame.tag_bind(del_bg, "<Button-1>", lambda event, nid=note_id: self._on_delete_click(event, nid))
                frame.tag_bind(del_txt, "<Button-1>", lambda event, nid=note_id: self._on_delete_click(event, nid))

    def _thumbnail_text(self, note_id: str) -> str:
        content = read_file(note_file(note_id)).strip()
        if not content:
            return "(empty)"

        lines = [line.rstrip() for line in content.splitlines() if line.strip()]
        preview = "\n".join(lines[:6])
        return preview[:360]

    def _on_thumbnail_click(self, note_id: str) -> None:
        if self.gallery_edit_mode:
            self.gallery_edit_mode = False
            self._update_gallery_controls()
        self._zoom_in_to_note(note_id)

    def _on_delete_click(self, _event, note_id: str):
        if note_id not in self.note_ids:
            return "break"

        path = note_file(note_id)
        if path.exists():
            path.unlink()

        self.note_ids = [nid for nid in self.note_ids if nid != note_id]

        if not self.note_ids:
            new_id = self._create_note_file("")
            self.note_ids = [new_id]
            self.current_note_id = new_id
        elif self.current_note_id == note_id:
            self.current_note_id = self.note_ids[0]

        self._persist_state()
        self._queue_gallery_refresh(force=True)
        return "break"

    def _enter_gallery_edit_mode(self) -> None:
        if self.animating:
            return
        self.gallery_edit_mode = True
        self._update_gallery_controls()
        self._queue_gallery_refresh(force=True)

    def _exit_gallery_edit_mode(self) -> None:
        self.gallery_edit_mode = False
        self._update_gallery_controls()
        self._queue_gallery_refresh(force=True)

    def _update_gallery_controls(self) -> None:
        if self.gallery_edit_mode:
            if not self.gallery_cancel_button.winfo_ismapped():
                self.gallery_cancel_button.pack(side="left")
            self._set_icon_color(self.gallery_edit_button, ICON_HOVER)
        else:
            if self.gallery_cancel_button.winfo_ismapped():
                self.gallery_cancel_button.pack_forget()
            self._set_icon_color(self.gallery_edit_button, NOTE_FG)

    def _flush_if_pending(self) -> None:
        if self.save_job is not None:
            self.root.after_cancel(self.save_job)
            self.save_job = None
            self._save_current_note()

    def _on_escape(self, _event=None):
        self._close()
        return "break"

    def _close(self) -> None:
        if not self.in_gallery:
            self._flush_if_pending()
        self._persist_state()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    StickyNoteApp(root)
    root.mainloop()
