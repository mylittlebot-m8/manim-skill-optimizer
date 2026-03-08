"""
Manim 脚本优化器 - 主入口（通义千问 VL 版）

使用方法:
    python run_qwen.py --video output.mp4 --script script.py --api-key YOUR_KEY
"""

import argparse
import sys
from pathlib import Path

from optimizer.qwen_vl_checker import QwenVLChecker
from optimizer.auto_fixer import AutoFixer
from optimizer.renderer import RenderController


def main():
    parser = argparse.ArgumentParser(description="Manim 脚本自动优化器（通义千问 VL）")
    
    parser.add_argument("--video", "-v", required=True, help="视频文件路径")
    parser.add_argument("--script", "-s", required=True, help="Manim 脚本路径")
    parser.add_argument("--api-key", "-k", help="通义千问 API Key（或设置 DASHSCOPE_API_KEY 环境变量）")
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
    
    api_key = args.api_key or Path(args.api_key).read_text().strip() if args.api_key and Path(args.api_key).exists() else None
    
    print("🔍 开始使用通义千问 VL 检测视频质量...")
    print(f"📹 视频：{args.video}")
    print(f"📝 脚本：{args.script}")
    
    # 创建检测器
    checker = QwenVLChecker(api_key=api_key)
    results = checker.analyze_video(args.video, args.script)
    
    # 输出结果
    print("\n" + "=" * 60)
    print(checker.get_report())
    print("=" * 60 + "\n")
    
    # 检查是否需要修复
    needs_fix = any(r.quality in ["needs_fix", "bad"] for r in results)
    
    if not needs_fix:
        print("✅ 视频质量完美，无需优化！")
        return 0
    
    # 自动修复
    if args.auto_fix:
        print(f"🔧 开始自动修复（最多 {args.iterations} 次迭代）...")
        
        fixer = AutoFixer(script_path=args.script)
        renderer = RenderController()
        
        for iteration in range(args.iterations):
            print(f"\n--- 迭代 {iteration + 1}/{args.iterations} ---")
            
            # 收集所有问题
            all_suggestions = []
            for result in results:
                all_suggestions.extend(result.suggestions)
            
            # 修复脚本
            fixed_script = fixer.fix_from_suggestions(all_suggestions)
            
            if not fixed_script:
                print("⚠️  无法自动修复所有问题")
                break
            
            # 重新渲染
            print("🎬 重新渲染...")
            new_video = renderer.render(fixed_script, output_dir=args.output)
            
            if not new_video:
                print("❌ 渲染失败")
                break
            
            # 再次检测
            print("🔍 验证修复效果...")
            new_results = checker.analyze_video(new_video, fixed_script)
            
            # 计算改进
            old_avg = sum(r.score for r in results) / len(results)
            new_avg = sum(r.score for r in new_results) / len(new_results)
            
            print(f"📊 评分变化：{old_avg:.1f} → {new_avg:.1f} ({'+' if new_avg > old_avg else ''}{new_avg - old_avg:.1f})")
            
            if new_avg >= 90:
                print("✅ 达到完美标准！")
                break
            
            if new_avg <= old_avg:
                print("⚠️  未检测到改进，停止迭代")
                break
            
            results = new_results
        
        # 生成报告
        if args.report:
            report_path = Path(args.output) / "optimization_report_qwen.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(checker.get_report())
            
            print(f"📄 报告已保存到：{report_path}")
    
    # 返回需要修复的问题数量
    return sum(1 for r in results if r.quality in ["needs_fix", "bad"])


if __name__ == "__main__":
    sys.exit(main())
