# -*- coding: utf-8 -*-
"""
桌面宠物（橘猫） - Windows Desktop Pet
- 无边框 / 透明 / 始终置顶
- 左键拖动移动位置
- 点击轮流触发互动：跳跃 -> 压扁回弹 -> 左右抖动
- 互动时在角色上方显示随机中文气泡（白色不透明，不遮挡角色）
- 鼠标滚轮缩放大小
"""
import os
import sys
import random

from PySide6.QtCore import Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QIcon, QAction, QCursor
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QMenu, QSystemTrayIcon
)


def resource_path(rel):
    """兼容 PyInstaller 打包后（_MEIPASS）与源码运行两种情况定位资源文件。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# 随机中文短句：跳跃 / 压扁 / 抖动 通用，随机抽取
PHRASES = [
    "喵～",
    "别戳我啦！",
    "本喵在思考猫生",
    "投喂小鱼干！",
    "又摸鱼被抓到了？",
    "让朕休息会儿",
    "今天也要加油哦",
    "困了困了…",
    "铲屎官来抱抱",
    "我不是胖，是毛多",
    "刚睡醒，勿扰",
    "抖一抖，精神！",
    "喵喵喵？",
    "摸鱼一时爽…",
    "谁动了我的猫窝",
]


class SpeechBubble(QWidget):
    """独立的置顶气泡窗口，显示在桌宠正上方，不遮挡角色。"""

    def __init__(self):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowFlag(Qt.WindowTransparentForInput, True)  # 气泡不吃鼠标事件

        self._text = ""
        self._pad = 12          # 文字内边距
        self._tail = 10         # 底部小三角高度
        self._radius = 12
        self._font = QFont("Microsoft YaHei", 11)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_text(self, text, anchor_center_x, anchor_top_y):
        """anchor_center_x: 桌宠水平中心；anchor_top_y: 桌宠顶部 y（气泡底部对齐到这里上方）。"""
        self._text = text
        fm = self.fontMetrics()
        # 支持根据文字长度自适应宽度
        text_w = fm.horizontalAdvance(text)
        text_h = fm.height()
        w = text_w + self._pad * 2
        h = text_h + self._pad * 2 + self._tail
        self.resize(w, h)

        x = int(anchor_center_x - w / 2)
        y = int(anchor_top_y - h - 6)   # 悬在角色上方 6px，绝不遮挡
        if y < 0:
            y = 0
        self.move(x, y)
        self.show()
        self.raise_()
        self.update()
        self._hide_timer.start(2500)

    def fontMetrics(self):
        from PySide6.QtGui import QFontMetrics
        return QFontMetrics(self._font)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        body = QRectF(0, 0, w, h - self._tail)

        # 不透明白底 + 淡灰描边
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QColor(210, 210, 210))
        p.drawRoundedRect(body, self._radius, self._radius)

        # 底部小三角（指向角色）
        cx = w / 2
        base = h - self._tail
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255))
        from PySide6.QtGui import QPolygonF
        from PySide6.QtCore import QPointF
        tri = QPolygonF([
            QPointF(cx - 8, base),
            QPointF(cx + 8, base),
            QPointF(cx, h),
        ])
        p.drawPolygon(tri)

        # 文字
        p.setPen(QColor(40, 40, 40))
        p.setFont(self._font)
        p.drawText(body, Qt.AlignCenter, self._text)


class Pet(QWidget):
    BASE_MAX = 260   # 角色基准显示高度（像素），配合 scale 缩放

    def __init__(self):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 载入抠好背景的透明 PNG
        img_path = resource_path(os.path.join("assets", "cat.png"))
        self.src = QPixmap(img_path)
        if self.src.isNull():
            # 兜底：找不到图片时用占位方块，避免崩溃
            self.src = QPixmap(200, 260)
            self.src.fill(QColor(240, 160, 60))

        # 把原图等比缩到基准高度，作为 scale=1.0 的基准
        self.base = self.src.scaledToHeight(
            self.BASE_MAX, Qt.SmoothTransformation
        )
        self.scale = 1.0
        self.MIN_SCALE, self.MAX_SCALE = 0.4, 3.0

        # 动画状态
        self.squash_x = 1.0     # 水平缩放（压扁时>1）
        self.squash_y = 1.0     # 垂直缩放（压扁时<1）
        self.shake_dx = 0.0     # 抖动水平偏移
        self.jump_dy = 0.0      # 跳跃垂直偏移（相对窗口内）
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._frame = 0
        self._anim = None
        self._anim_cycle = 0    # 轮流触发计数

        # 拖动状态
        self._press_pos = None      # 全局按下位置
        self._win_pos = None        # 按下时窗口位置
        self._dragging = False
        self.DRAG_THRESHOLD = 5

        self.bubble = SpeechBubble()

        self._relayout()
        self._center_on_screen()
        self._setup_tray()

    # ---------- 尺寸/布局 ----------
    def _margins(self):
        """为压扁变宽/跳跃留出的窗口内边距。"""
        w = self.base.width() * self.scale
        h = self.base.height() * self.scale
        return int(w * 0.3), int(h * 0.35)  # (mx, my)

    def _relayout(self):
        w = self.base.width() * self.scale
        h = self.base.height() * self.scale
        mx, my = self._margins()
        self.resize(int(w + mx * 2), int(h + my * 2))

    def _center_on_screen(self):
        scr = QApplication.primaryScreen().availableGeometry()
        self.move(scr.right() - self.width() - 60,
                  scr.bottom() - self.height() - 60)

    # ---------- 绘制 ----------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)

        base_w = self.base.width() * self.scale
        base_h = self.base.height() * self.scale
        draw_w = base_w * self.squash_x
        draw_h = base_h * self.squash_y

        cx = self.width() / 2 + self.shake_dx
        # 底部锚定：脚掌位置固定在窗口底部内边距处，压扁时向下压
        _, my = self._margins()
        bottom_y = self.height() - my
        x = cx - draw_w / 2
        y = bottom_y - draw_h + self.jump_dy

        target = QRectF(x, y, draw_w, draw_h)
        p.drawPixmap(target, self.base, QRectF(self.base.rect()))

    # ---------- 交互：鼠标 ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press_pos = e.globalPosition().toPoint()
            self._win_pos = self.frameGeometry().topLeft()
            self._dragging = False

    def mouseMoveEvent(self, e):
        if self._press_pos is None:
            return
        gp = e.globalPosition().toPoint()
        delta = gp - self._press_pos
        if not self._dragging and delta.manhattanLength() > self.DRAG_THRESHOLD:
            self._dragging = True
        if self._dragging:
            self.move(self._win_pos + delta)
            if self.bubble.isVisible():
                self.bubble.hide()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        was_drag = self._dragging
        self._press_pos = None
        self._dragging = False
        if not was_drag:
            self._on_click()

    def wheelEvent(self, e):
        step = 0.1 if e.angleDelta().y() > 0 else -0.1
        new_scale = round(self.scale + step, 2)
        new_scale = max(self.MIN_SCALE, min(self.MAX_SCALE, new_scale))
        if new_scale == self.scale:
            return
        center = self.frameGeometry().center()
        self.scale = new_scale
        self._relayout()
        # 缩放后保持中心不动
        rect = self.frameGeometry()
        rect.moveCenter(center)
        self.move(rect.topLeft())
        self.update()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        act_quit = QAction("退出", self)
        act_quit.triggered.connect(QApplication.quit)
        menu.addAction(act_quit)
        menu.exec(e.globalPos())

    # ---------- 点击 -> 轮流触发动画 + 气泡 ----------
    def _on_click(self):
        anims = ["jump", "squash", "shake"]
        self._anim = anims[self._anim_cycle % len(anims)]
        self._anim_cycle += 1
        self._frame = 0
        self._anim_timer.start(16)  # ~60fps
        self._show_bubble()

    def _show_bubble(self):
        text = random.choice(PHRASES)
        geo = self.frameGeometry()
        _, my = self._margins()
        # 角色实际顶部 = 窗口顶部 + 上内边距
        top_y = geo.top() + my
        center_x = geo.center().x()
        self.bubble.show_text(text, center_x, top_y)

    # ---------- 逐帧动画 ----------
    def _tick(self):
        self._frame += 1
        f = self._frame

        if self._anim == "jump":
            dur = 34
            t = f / dur
            if t >= 1.0:
                self.jump_dy = 0.0
                self._end_anim()
            else:
                # 抛物线：-4h*t*(1-t)，向上为负
                height = self.base.height() * self.scale * 0.45
                self.jump_dy = -4 * height * t * (1 - t)

        elif self._anim == "squash":
            dur = 30
            t = f / dur
            if t >= 1.0:
                self.squash_x = self.squash_y = 1.0
                self._end_anim()
            else:
                import math
                # 阻尼回弹：先压扁(y<1,x>1)再回弹震荡
                amp = 0.28 * (1 - t)
                osc = math.sin(t * math.pi * 3)
                self.squash_y = 1.0 - amp * osc
                self.squash_x = 1.0 + amp * osc

        elif self._anim == "shake":
            dur = 36
            t = f / dur
            if t >= 1.0:
                self.shake_dx = 0.0
                self._end_anim()
            else:
                import math
                amp = 14 * self.scale * (1 - t)
                self.shake_dx = amp * math.sin(t * math.pi * 6)

        self.update()

    def _end_anim(self):
        self._anim_timer.stop()
        self._anim = None
        self.jump_dy = 0.0
        self.squash_x = self.squash_y = 1.0
        self.shake_dx = 0.0

    # ---------- 托盘 ----------
    def _setup_tray(self):
        icon = QIcon(resource_path(os.path.join("assets", "cat.png")))
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("桌面猫咪")
        menu = QMenu()
        act_quit = QAction("退出", self)
        act_quit.triggered.connect(QApplication.quit)
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.show()


def main():
    QApplication.setQuitOnLastWindowClosed(False)
    app = QApplication(sys.argv)
    pet = Pet()
    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
