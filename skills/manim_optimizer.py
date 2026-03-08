"""
Manim 脚本自动优化 Skill - OpenClaw 集成

使用方法:
    优化这个 Manim 脚本，检测并修复乱码和重叠问题
    检测 video.mp4 的视觉质量问题
"""

import os
import sys
from pathlib import Path

# 添加优化器到路径
OPTIMIZER_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(OPTIMIZER_PATH))

from optimizer.visual_checker import VisualChecker
from optimizer.auto_fixer import AutoFixer


async def optimize_manim_script(context, video_path: str = None, script_path: str = None, auto_fix: bool = True):
    """
    优化 Manim 脚本
    
    参数:
        context: OpenClaw 上下文
        video_path: 视频文件路径
        script_path: 脚本文件路径
        auto_fix: 是否自动修复
    """
    
    # 查找文件
    if not video_path or not script_path:
        # 在工作区查找最新的视频和脚本
        workspace = Path("/Users/wenjigkuai/.openclaw/workspace")
        
        if not video_path:
            videos = list(workspace.glob("*.mp4"))
            if videos:
                video_path = str(sorted(videos, key=lambda x: x.stat().st_mtime, reverse=True)[0])
        
        if not script_path:
            scripts = list(workspace.glob("**/script*.py"))
            if scripts:
                script_path = str(sorted(scripts, key=lambda x: x.stat().st_mtime, reverse=True)[0])
    
    if not video_path:
        return "❌ 未找到视频文件，请指定视频路径"
    
    if not script_path:
        return "❌ 未找到脚本文件，请指定脚本路径"
    
    # 运行检测
    await context.send(f"🔍 开始检测视频质量...\n\n视频：{video_path}\n脚本：{script_path}")
    
    checker = VisualChecker()
    issues = checker.detect(video_path)
    
    if not issues:
        return "✅ 视频质量良好，未检测到乱码或重叠问题！"
    
    # 生成报告
    report = checker.get_report()
    await context.send(f"📊 检测完成，发现 {len(issues)} 个问题：\n\n{report}")
    
    # 自动修复
    if auto_fix and issues:
        await context.send("🔧 开始自动修复...")
        
        fixer = AutoFixer(script_path=script_path)
        
        try:
            fixed_script = fixer.fix(issues)
            
            if fixed_script:
                await context.send(f"✅ 脚本已修复！\n\n修复内容：\n{fixer.get_fix_report()}")
                await context.send("💡 下一步：重新渲染视频以验证修复效果\n\n命令：`python run.py --video output.mp4 --script script.py`")
            else:
                await context.send("⚠️ 部分问题需要手动修复，请查看详细报告")
        
        except Exception as e:
            await context.send(f"❌ 修复失败：{str(e)}")
    
    return f"检测完成，发现 {len(issues)} 个问题，已生成修复建议"


# Skill 导出
SKILL_EXPORTS = {
    "optimize_manim_script": {
        "description": "优化 Manim 脚本，检测并修复乱码和重叠问题",
        "function": optimize_manim_script,
        "parameters": {
            "video_path": {"type": "string", "description": "视频文件路径"},
            "script_path": {"type": "string", "description": "脚本文件路径"},
            "auto_fix": {"type": "boolean", "description": "是否自动修复", "default": True}
        }
    }
}
