"""
通义千问 VL 视觉检测器
使用 Qwen-VL 大模型智能判断视频布局质量
"""

import os
import base64
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import requests


class LayoutQuality(Enum):
    """布局质量等级"""
    PERFECT = "perfect"        # 完美
    GOOD = "good"             # 良好
    ACCEPTABLE = "acceptable"  # 可接受
    NEEDS_FIX = "needs_fix"   # 需要修复
    BAD = "bad"               # 差


@dataclass
class FrameAnalysis:
    """帧分析结果"""
    scene_number: int
    frame_number: int
    timestamp: float
    image_path: str
    quality: LayoutQuality
    score: float  # 0-100
    issues: List[str]
    suggestions: List[str]


class QwenVLChecker:
    """通义千问 VL 视觉检测器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化检测器
        
        参数:
            api_key: 通义千问 API Key（从环境变量 DASHSCOPE_API_KEY 读取）
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")
        
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        self.results: List[FrameAnalysis] = []
    
    def analyze_video(self, video_path: str, script_path: str = None) -> List[FrameAnalysis]:
        """
        分析视频关键帧
        
        参数:
            video_path: 视频文件路径
            script_path: 脚本文件路径（用于提取场景信息）
        
        返回:
            分析结果列表
        """
        self.results = []
        
        # 提取关键帧（每幕：第一帧、中间帧、最后一帧）
        keyframes = self._extract_keyframes(video_path, script_path)
        
        print(f"📸 提取到 {len(keyframes)} 个关键帧")
        
        # 分析每个关键帧
        for i, (scene_num, frame_path, timestamp) in enumerate(keyframes, 1):
            print(f"分析帧 {i}/{len(keyframes)} - 场景 {scene_num} ({timestamp:.1f}s)")
            
            result = self._analyze_frame(frame_path, scene_num, timestamp)
            self.results.append(result)
        
        return self.results
    
    def _extract_keyframes(self, video_path: str, script_path: str = None) -> List[Tuple[int, str, float]]:
        """
        提取关键帧
        
        策略：
        1. 从脚本提取场景数量
        2. 每个场景提取 3 帧：开始、中间、结束
        3. 保存为临时文件
        """
        import cv2
        import tempfile
        
        # 估算场景数量（从脚本或默认）
        num_scenes = self._estimate_scenes(script_path)
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps
        
        # 每个场景的帧数
        frames_per_scene = total_frames // num_scenes
        
        keyframes = []
        
        for scene in range(1, num_scenes + 1):
            # 计算三个关键帧位置
            start_frame = (scene - 1) * frames_per_scene
            middle_frame = start_frame + frames_per_scene // 2
            end_frame = min(start_frame + frames_per_scene - 1, total_frames - 1)
            
            for frame_offset, frame_num in [(0, start_frame), (0.5, middle_frame), (0, end_frame)]:
                timestamp = frame_num / fps
                
                # 提取帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    # 保存临时文件
                    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    cv2.imwrite(temp_file.name, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    keyframes.append((scene, temp_file.name, timestamp))
        
        cap.release()
        return keyframes
    
    def _estimate_scenes(self, script_path: str) -> int:
        """从脚本估算场景数量"""
        if not script_path or not Path(script_path).exists():
            return 10  # 默认 10 个场景
        
        content = Path(script_path).read_text(encoding='utf-8')
        
        # 查找 scene_X 方法
        import re
        scenes = re.findall(r'def scene_(\d+)_', content)
        
        if scenes:
            return max(int(s) for s in scenes)
        
        return 10
    
    def _analyze_frame(self, image_path: str, scene_num: int, timestamp: float) -> FrameAnalysis:
        """使用通义千问 VL 分析单帧"""
        
        # 构建提示词
        prompt = self._build_prompt(scene_num)
        
        # 读取图片并转 base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # 调用 API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-vl-max",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:image/jpeg;base64,{image_data}"},
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "temperature": 0.1,
                "max_tokens": 500
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            analysis = result['output']['choices'][0]['message']['content']
            
            # 解析 AI 返回结果
            quality, score, issues, suggestions = self._parse_ai_response(analysis)
            
            return FrameAnalysis(
                scene_number=scene_num,
                frame_number=0,
                timestamp=timestamp,
                image_path=image_path,
                quality=quality,
                score=score,
                issues=issues,
                suggestions=suggestions
            )
        
        except Exception as e:
            print(f"❌ API 调用失败：{str(e)}")
            return FrameAnalysis(
                scene_number=scene_num,
                frame_number=0,
                timestamp=timestamp,
                image_path=image_path,
                quality=LayoutQuality.NEEDS_FIX,
                score=50,
                issues=[f"API 调用失败：{str(e)}"],
                suggestions=["手动检查视频质量"]
            )
    
    def _build_prompt(self, scene_num: int) -> str:
        """构建 AI 提示词"""
        return f"""
你是一个专业的 Manim 教育视频质量评估专家。请分析这个数学教学视频帧的布局质量。

## 评估维度

1. **文字清晰度**
   - 是否有乱码、方框、问号等渲染错误
   - 文字是否清晰可读

2. **布局合理性**
   - 文字/公式是否有重叠
   - 内容是否超出画面边界
   - 元素间距是否合理

3. **视觉美观度**
   - 对比度是否足够
   - 配色是否协调
   - 整体布局是否平衡

4. **教学内容**
   - 数学公式显示是否正确
   - 图形标注是否清晰

## 输出格式

请严格按以下 JSON 格式返回：

```json
{{
  "quality": "perfect|good|acceptable|needs_fix|bad",
  "score": 0-100,
  "issues": ["问题 1", "问题 2"],
  "suggestions": ["建议 1", "建议 2"]
}}
```

## 评分标准

- 90-100: perfect - 完美，无需任何调整
- 75-89: good - 良好，Minor 问题可选优化
- 60-74: acceptable - 可接受，有明显问题但不影响理解
- 40-59: needs_fix - 需要修复，影响观看体验
- 0-39: bad - 差，严重影响理解，必须重新制作

场景编号：{scene_num}
"""
    
    def _parse_ai_response(self, response_text: str) -> Tuple[LayoutQuality, float, List[str], List[str]]:
        """解析 AI 响应"""
        import json
        import re
        
        # 提取 JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = response_text
        
        try:
            data = json.loads(json_str)
            
            quality_map = {
                "perfect": LayoutQuality.PERFECT,
                "good": LayoutQuality.GOOD,
                "acceptable": LayoutQuality.ACCEPTABLE,
                "needs_fix": LayoutQuality.NEEDS_FIX,
                "bad": LayoutQuality.BAD
            }
            
            quality = quality_map.get(data.get("quality", "needs_fix"), LayoutQuality.NEEDS_FIX)
            score = float(data.get("score", 50))
            issues = data.get("issues", [])
            suggestions = data.get("suggestions", [])
            
            return quality, score, issues, suggestions
        
        except:
            # 解析失败，返回默认值
            return LayoutQuality.NEEDS_FIX, 50, ["AI 响应解析失败"], ["手动检查视频"]
    
    def get_report(self) -> str:
        """生成分析报告"""
        if not self.results:
            return "未进行分析"
        
        report = ["# 通义千问 VL 视觉质量分析报告\n"]
        
        # 统计
        total = len(self.results)
        perfect = sum(1 for r in self.results if r.quality == LayoutQuality.PERFECT)
        good = sum(1 for r in self.results if r.quality == LayoutQuality.GOOD)
        needs_fix = sum(1 for r in self.results if r.quality in [LayoutQuality.NEEDS_FIX, LayoutQuality.BAD])
        
        avg_score = sum(r.score for r in self.results) / total
        
        report.append("## 总体评分\n")
        report.append(f"- 总帧数：{total}")
        report.append(f"- 平均分：{avg_score:.1f}/100")
        report.append(f"- 完美帧：{perfect}/{total} ({perfect*100/total:.0f}%)")
        report.append(f"- 良好帧：{good}/{total} ({good*100/total:.0f}%)")
        report.append(f"- 需修复：{needs_fix}/{total} ({needs_fix*100/total:.0f}%)\n")
        
        # 总体评价
        if avg_score >= 90:
            report.append("🎉 **总体评价：完美！** 无需优化\n")
        elif avg_score >= 75:
            report.append("✅ **总体评价：良好** 可选优化\n")
        elif avg_score >= 60:
            report.append("⚠️ **总体评价：可接受** 建议优化\n")
        else:
            report.append("❌ **总体评价：需要优化** 建议重新调整布局\n")
        
        # 详细问题
        problem_frames = [r for r in self.results if r.quality in [LayoutQuality.NEEDS_FIX, LayoutQuality.BAD]]
        
        if problem_frames:
            report.append("\n## 问题帧详情\n")
            for i, result in enumerate(problem_frames, 1):
                report.append(f"### 场景 {result.scene_number} ({result.timestamp:.1f}s)")
                report.append(f"- 质量：{result.quality.value}")
                report.append(f"- 评分：{result.score}/100")
                report.append(f"- 问题：{', '.join(result.issues)}")
                report.append(f"- 建议：{', '.join(result.suggestions)}\n")
        
        return "\n".join(report)


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python qwen_vl_checker.py <video_path> [script_path]")
        sys.exit(1)
    
    checker = QwenVLChecker()
    results = checker.analyze_video(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(checker.get_report())
