# Manim 脚本自动优化器

基于视觉识别的 Manim 脚本自动检测和优化技能。

## 🎯 功能

1. **视觉质量检测**
   - 乱码检测（OCR 识别失败区域）
   - 文字重叠检测
   - 布局边界检测
   - 对比度检测

2. **自动修复**
   - 字体大小调整
   - 位置自动校正
   - 间距优化
   - 场景分割建议

3. **迭代优化**
   - 自动重新渲染
   - 质量验证
   - 版本对比

## 📁 项目结构

```
manim-skill-optimizer/
├── optimizer/
│   ├── __init__.py
│   ├── visual_checker.py      # 视觉检测
│   ├── ocr_analyzer.py        # OCR 分析
│   ├── layout_analyzer.py     # 布局分析
│   ├── auto_fixer.py          # 自动修复
│   └── renderer.py            # 渲染控制
├── skills/
│   ├── manim_optimizer.py     # OpenClaw Skill
│   └── skill.json             # Skill 配置
├── config/
│   └── detection_config.yaml  # 检测配置
├── tests/
│   └── test_samples/          # 测试样本
├── requirements.txt
├── README.md
└── run.py                     # 主入口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行检测

```bash
python run.py --video path/to/video.mp4 --script path/to/script.py
```

### 3. 自动优化

```bash
python run.py --video path/to/video.mp4 --script path/to/script.py --auto-fix --iterations 3
```

## 📊 检测指标

| 指标 | 阈值 | 说明 |
|------|------|------|
| 文字重叠率 | < 5% | 文字区域重叠比例 |
| OCR 识别率 | > 95% | 可识别文字比例 |
| 边界溢出 | 0 | 内容超出画面 |
| 对比度 | > 4.5:1 | WCAG AA 标准 |

## 🔧 配置示例

```yaml
detection:
  ocr:
    enabled: true
    language: chi_sim+eng
    confidence_threshold: 0.6
  
  overlap:
    enabled: true
    max_overlap_ratio: 0.05
  
  boundary:
    enabled: true
    margin_pixels: 50
  
  contrast:
    enabled: true
    min_contrast_ratio: 4.5

optimization:
  max_iterations: 3
  font_size_step: 2
  position_step: 0.5
```

## 📝 使用示例

### Python API

```python
from optimizer import ManimOptimizer

optimizer = ManimOptimizer(
    video_path="output.mp4",
    script_path="script.py"
)

# 运行检测
results = optimizer.detect()
print(f"发现问题：{results.issues}")

# 自动修复
if results.needs_fix:
    fixed_script = optimizer.auto_fix()
    optimizer.rerender(fixed_script)
    
    # 验证
    final_results = optimizer.verify()
    print(f"优化后评分：{final_results.score}")
```

### OpenClaw Skill

在 OpenClaw 中调用：

```
优化这个 Manim 脚本，检测并修复乱码和重叠问题
```

## 🎯 输出报告

优化完成后生成详细报告：

```markdown
# Manim 脚本优化报告

## 检测统计
- 总帧数：1200
- 检测帧数：120（每 10 帧抽样）
- 发现问题：3

## 问题列表
1. [乱码] Scene 3, Frame 45 - MathTex 渲染失败
2. [重叠] Scene 5, Frame 89 - 文字重叠率 8%
3. [边界] Scene 7, Frame 120 - 内容超出右边界

## 修复操作
1. ✅ 调整字体大小：32 → 28
2. ✅ 修正位置：RIGHT * 0.25 → RIGHT * 0.5
3. ✅ 分割场景：Scene 7 → Scene 7a + Scene 7b

## 最终评分
- 优化前：72/100
- 优化后：95/100 ⭐
```

## 📄 许可证

MIT License
