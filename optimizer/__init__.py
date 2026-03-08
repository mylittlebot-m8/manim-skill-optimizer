"""
Manim 脚本优化器
视觉质量检测与自动修复工具
"""

from .visual_checker import VisualChecker, DetectionIssue, IssueType
from .auto_fixer import AutoFixer
from .renderer import RenderController

__version__ = "1.0.0"
__all__ = [
    "VisualChecker",
    "DetectionIssue",
    "IssueType",
    "AutoFixer",
    "RenderController"
]
