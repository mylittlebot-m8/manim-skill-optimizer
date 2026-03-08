"""
渲染控制器
管理 Manim 脚本的渲染过程
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


class RenderController:
    """渲染控制器"""
    
    def __init__(self, quality: str = "h"):
        """
        初始化渲染控制器
        
        参数:
            quality: 渲染质量 (l=低，m=中，h=高，k=4k)
        """
        self.quality = quality
    
    def render(self, script_path: str, output_dir: str = None, scene_name: str = None) -> Optional[str]:
        """
        渲染 Manim 脚本
        
        参数:
            script_path: 脚本文件路径
            output_dir: 输出目录
            scene_name: 场景名称（可选，默认渲染所有场景）
        
        返回:
            渲染输出的视频路径，失败返回 None
        """
        script = Path(script_path)
        
        if not script.exists():
            print(f"❌ 脚本文件不存在：{script_path}")
            return None
        
        # 构建命令
        cmd = [
            sys.executable, "-m", "manim",
            "-q" + self.quality,
            str(script)
        ]
        
        if scene_name:
            cmd.append(scene_name)
        
        if output_dir:
            cmd.extend(["--output_dir", output_dir])
        
        print(f"🎬 执行渲染：{' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 分钟超时
            )
            
            if result.returncode != 0:
                print(f"❌ 渲染失败：\n{result.stderr}")
                return None
            
            print("✅ 渲染完成！")
            
            # 查找输出的视频文件
            video_path = self._find_latest_video(output_dir or "media/videos")
            return video_path
        
        except subprocess.TimeoutExpired:
            print("❌ 渲染超时（>10 分钟）")
            return None
        except Exception as e:
            print(f"❌ 渲染异常：{str(e)}")
            return None
    
    def _find_latest_video(self, directory: str) -> Optional[str]:
        """查找最新的视频文件"""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return None
        
        # 递归查找 mp4 文件
        videos = list(dir_path.rglob("*.mp4"))
        
        if not videos:
            return None
        
        # 返回最新的视频
        latest = max(videos, key=lambda x: x.stat().st_mtime)
        return str(latest)
    
    def render_remote(self, script_path: str, server_url: str, api_key: str = None) -> Optional[str]:
        """
        使用远程服务渲染
        
        参数:
            script_path: 脚本文件路径
            server_url: 远程服务器 URL
            api_key: API 密钥（可选）
        
        返回:
            下载的视频路径，失败返回 None
        """
        # TODO: 实现远程渲染
        # 参考 tutor_skill/tutor/scripts/render_integrated.py
        pass
