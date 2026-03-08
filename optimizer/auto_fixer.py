"""
Manim 脚本自动修复器
根据检测结果自动修复脚本问题
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from optimizer.visual_checker import DetectionIssue, IssueType


class AutoFixer:
    """自动修复器"""
    
    def __init__(self, script_path: str):
        self.script_path = Path(script_path)
        self.original_content = self.script_path.read_text(encoding='utf-8')
        self.fixed_content = self.original_content
        self.fixes_applied: List[str] = []
    
    def fix(self, issues: List[DetectionIssue]) -> Optional[str]:
        """修复脚本"""
        self.fixes_applied = []
        
        for issue in issues:
            if issue.type == IssueType.GARBLE:
                self._fix_garble(issue)
            elif issue.type == IssueType.OVERLAP:
                self._fix_overlap(issue)
            elif issue.type == IssueType.BOUNDARY:
                self._fix_boundary(issue)
            elif issue.type == IssueType.CONTRAST:
                self._fix_contrast(issue)
        
        if not self.fixes_applied:
            return None
        
        # 保存修复后的脚本
        fixed_path = self.script_path.parent / f"{self.script_path.stem}_fixed{self.script_path.suffix}"
        fixed_path.write_text(self.fixed_content, encoding='utf-8')
        
        print(f"修复后的脚本已保存到：{fixed_path}")
        return str(fixed_path)
    
    def _fix_garble(self, issue: DetectionIssue):
        """修复乱码（通常是 LaTeX 或字体问题）"""
        # 尝试将 Text 替换为 MathTex 或反之
        if "MathTex" in self.fixed_content:
            # 可能是 LaTeX 编译问题，添加 xelatex 配置
            if "xelatex" not in self.fixed_content:
                self.fixed_content = self._add_xelatex_config()
                self.fixes_applied.append("添加 xelatex 中文支持配置")
    
    def _fix_overlap(self, issue: DetectionIssue):
        """修复重叠（调整位置或字体大小）"""
        # 查找 font_size 并减小
        def reduce_font(match):
            size = int(match.group(1))
            new_size = max(size - 2, 20)  # 最小 20
            return f"font_size={new_size}"
        
        self.fixed_content = re.sub(r'font_size=(\d+)', reduce_font, self.fixed_content, count=5)
        self.fixes_applied.append("减小字体大小 2px")
    
    def _fix_boundary(self, issue: DetectionIssue):
        """修复边界溢出（调整位置）"""
        # 调整 RIGHT 或 LEFT 的偏移量
        if "RIGHT *" in self.fixed_content:
            self.fixed_content = self.fixed_content.replace(
                "RIGHT * 0.25",
                "RIGHT * 0.5"
            )
            self.fixes_applied.append("调整水平位置：RIGHT * 0.25 → RIGHT * 0.5")
    
    def _fix_contrast(self, issue: DetectionIssue):
        """修复对比度（调整颜色）"""
        # 将暗色背景改为深色，亮色文字保持
        if 'background_color = "' in self.fixed_content:
            self.fixed_content = self.fixed_content.replace(
                'background_color = "#1a1a2e"',
                'background_color = "#0d0d1a"'
            )
            self.fixes_applied.append("加深背景颜色以提高对比度")
    
    def _add_xelatex_config(self) -> str:
        """添加 xelatex 配置"""
        config = '''
# ========== xelatex 中文支持 ==========
config.tex_compiler = "xelatex"
template = TexTemplate()
template.tex_compiler = "xelatex"
template.output_format = ".xdv"
template.add_to_preamble(r"\\usepackage{xeCJK}")
template.add_to_preamble(r"\\setCJKmainfont{WenQuanYi Zen Hei}")
config.tex_template = template
# ====================================
'''
        # 在 import 后插入
        lines = self.fixed_content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('from manim') or line.startswith('import'):
                insert_pos = i + 1
        
        lines.insert(insert_pos, config)
        return '\n'.join(lines)
    
    def get_fix_report(self) -> str:
        """获取修复报告"""
        if not self.fixes_applied:
            return "未应用任何修复"
        
        report = ["## 应用的修复：\n"]
        for i, fix in enumerate(self.fixes_applied, 1):
            report.append(f"{i}. ✅ {fix}")
        
        return "\n".join(report)
