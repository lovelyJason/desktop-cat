# 桌面猫咪 🐱 (Desktop Cat Pet)

用你的橘猫照片做的 Windows 桌面宠物。无边框透明窗口、始终置顶，可拖动、点击互动、滚轮缩放。

## 功能
- 去背景透明角色，窗口无边框、始终置顶
- **左键拖动**：移动位置
- **单击角色**：轮流触发互动 —— 跳跃 → 压扁回弹 → 左右抖动
- 互动时角色**上方**弹出随机中文气泡（白色不透明，不遮挡角色）
- **鼠标滚轮**：缩放大小（0.4x ~ 3.0x）
- **右键角色 / 托盘图标**：退出

## 拿到可双击的 EXE（GitHub Actions 云端打包）
1. 把本文件夹推到一个 GitHub 仓库：
   ```bash
   git init && git add . && git commit -m "init desktop cat"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/<仓库名>.git
   git push -u origin main
   ```
2. 打开仓库页面 → **Actions** 标签 → 左侧选 **Build Windows EXE** → 点 **Run workflow**。
3. 跑完后在该次运行页面底部 **Artifacts** 里下载 `DesktopCat-windows.zip`，解压得到 `DesktopCat.exe`，**双击即可运行**。
4. （可选）打一个版本 tag 会自动发布到 Release：
   ```bash
   git tag v1.0.0 && git push origin v1.0.0
   ```

## 备用：在 Windows 本地打包
双击 `build_windows.bat`，完成后 exe 在 `dist\DesktopCat.exe`。

## 备用：免打包直接运行
双击 `run.bat`（需已装 Python 3.9+），或手动：
```bash
pip install -r requirements.txt
python main.py
```

## 换成别的图片
把新的透明 PNG 覆盖 `assets/cat.png` 即可（建议已去背景）。

## 目录结构
```
desktop-cat/
├─ main.py                 # 主程序
├─ requirements.txt
├─ assets/
│  ├─ cat.png             # 去背景后的角色图
│  └─ cat.ico             # 打包用图标
├─ tools/remove_bg.py     # 抠图脚本（生成 cat.png，仅开发用）
├─ run.bat                # Windows 免打包运行
├─ build_windows.bat      # Windows 本地打包 exe
└─ .github/workflows/build.yml  # GitHub Actions 云端打包
```
