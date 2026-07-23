# -*- coding: utf-8 -*-
"""离屏冒烟测试：构造 Pet，跑完 3 种动画+气泡，检查不崩溃且能渲染角色。"""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import main as app_main

app = QApplication(sys.argv)
pet = app_main.Pet()
pet.show()

assert not pet.src.isNull(), "cat.png 未能载入"
assert pet.base.width() > 0 and pet.base.height() > 0
print("loaded cat:", pet.src.size(), "base:", pet.base.size())

# 渲染到 pixmap，确认 paintEvent 不崩溃
from PySide6.QtGui import QPixmap
pm = QPixmap(pet.size()); pm.fill()
pet.render(pm)
print("paint ok, window size:", pet.size())

# 依次触发三种动画，各跑若干帧
results = []
def run_anim(name_expected, done_cb):
    pet._on_click()
    results.append(pet._anim)
    # 手动快进动画帧
    for _ in range(60):
        if pet._anim is None: break
        pet._tick()
    done_cb()

seq = []
def step():
    if len(seq) < 3:
        before = pet._anim_cycle
        pet._on_click()
        anim = pet._anim
        for _ in range(80):
            if pet._anim is None: break
            pet._tick()
        seq.append(anim)
        assert pet._anim is None, f"动画 {anim} 未结束"
        # 气泡应显示过
        step()
    else:
        print("animations cycled:", seq)
        assert seq == ["jump", "squash", "shake"], f"轮流顺序错误: {seq}"
        # 测试缩放
        s0 = pet.scale
        from PySide6.QtGui import QWheelEvent
        # 直接调用逻辑
        pet.scale = min(pet.MAX_SCALE, pet.scale+0.5); pet._relayout()
        assert pet.width() > 0
        print("scale ok:", s0, "->", pet.scale, "size", pet.size())
        print("SMOKE_OK")
        QTimer.singleShot(0, app.quit)

QTimer.singleShot(0, step)
app.exec()
