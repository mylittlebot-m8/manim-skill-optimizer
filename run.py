"""
Manim 脚本自动优化器 - 主入口

使用方法:
    python run.py --video output.mp4 --script script.py --auto-fix
"""

import argparse
import sys
from pathlib import Path

from optimizer.visual_checker import VisualChecker
from optimizer.auto_fixer import AutoFixer
from optimizer.renderer import RenderController


def main():
    parser = argparse.ArgumentParser(description="Manim 脚本自动优化器")
    
    parser.add_argument("--video", "-v", required=True, help="视频文件路径")
    parser.add_argument("--script", "-s", required=True, help="Manim 脚本路径")
    parser.add_argument("--output", "-o", default="optimized", help="输出目录")
    parser.add_argument("--auto-fix", "-f", action="store_true", help="自动修复问题")
    parser.add_argument("--iterations", "-i", type=int, default=3, help="最大迭代次数")
    parser.add_argument("--report", "-r", action="store_true", help="生成详细报告")
    
    args = parser.parse_args()
    
    # 验证文件
    if not Path(args.video).exists():
        print(f"❌ 视频文件不存在：{args.video}")
        sys.exit(1)
    
    if not Path(args.script).exists():
        print(f"❌ 脚本文件不存在：{args.script}")
        sys.exit(1)
    
    print("🔍 开始检测视频质量...")
    
    # 创建检测器
    checker = VisualChecker()
    issues = checker.detect(args.video)
    
    # 输出结果
    print("\n" + "=" * 50)
    print(checker.get_report())
    print("=" * 50 + "\n")
    
    if not issues:
        print("✅ 视频质量良好，无需优化！")
        return 0
    
    # 自动修复
    if args.auto_fix:
        print(f"🔧 开始自动修复（最多 {args.iterations} 次迭代）...")
        
        fixer = AutoFixer(script_path=args.script)
        renderer = RenderController()
        
        for iteration in range(args.iterations):
            print(f"\n--- 迭代 {iteration + 1}/{args.iterations} ---")
            
            # 修复脚本
            fixed_script = fixer.fix(issues)
            
            if not fixed_script:
                print("⚠️  无法自动修复所有问题")
                break
            
            # 重新渲染
            print("🎬 重新渲染...")
            new_video = renderer.render(fixed_script, output_dir=args.output)
            
            # 再次检测
            print("🔍 验证修复效果...")
            new_issues = checker.detect(new_video)
            
            if not new_issues:
                print("✅ 所有问题已修复！")
                break
            
            # 检查是否有改进
            if len(new_issues) >= len(issues):
                print("⚠️  未检测到改进，停止迭代")
                break
            
            issues = new_issues
        
        # 生成报告
        if args.report:
            report_path = Path(args.output) / "optimization_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# Manim 脚本优化报告\n\n")
                f.write(f"原始脚本：{args.script}\n")
                f.write(f"原始视频：{args.video}\n")
                f.write(f"优化后视频：{new_video}\n\n")
                f.write(checker.get_report())
            
            print(f"📄 报告已保存到：{report_path}")
    
    return len(issues)


if __name__ == "__main__":
    sys.exit(main())
