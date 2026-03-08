"""
Manim 视觉质量检测器
检测视频中的乱码、重叠、布局问题
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class IssueType(Enum):
    """问题类型"""
    GARBLE = "garble"          # 乱码
    OVERLAP = "overlap"        # 重叠
    BOUNDARY = "boundary"      # 边界溢出
    CONTRAST = "contrast"      # 对比度不足
    BLUR = "blur"              # 模糊


@dataclass
class DetectionIssue:
    """检测到的问题"""
    type: IssueType
    frame_number: int
    timestamp: float
    description: str
    severity: float  # 0-1，严重程度
    bounding_box: Tuple[int, int, int, int]  # x, y, w, h
    suggestion: str


class VisualChecker:
    """视觉质量检测器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.issues: List[DetectionIssue] = []
        
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'ocr': {
                'enabled': True,
                'confidence_threshold': 0.6,
                'language': 'chi_sim+eng'
            },
            'overlap': {
                'enabled': True,
                'max_overlap_ratio': 0.05
            },
            'boundary': {
                'enabled': True,
                'margin_pixels': 50
            },
            'contrast': {
                'enabled': True,
                'min_contrast_ratio': 4.5
            },
            'sampling': {
                'frame_interval': 10  # 每 N 帧检测一次
            }
        }
    
    def detect(self, video_path: str) -> List[DetectionIssue]:
        """检测视频质量问题"""
        self.issues = []
        
        if not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在：{video_path}")
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame_interval = self.config['sampling']['frame_interval']
        
        print(f"开始检测：{total_frames} 帧，抽样间隔：{frame_interval}")
        
        frame_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_num % frame_interval == 0:
                timestamp = frame_num / fps
                print(f"检测帧 {frame_num}/{total_frames} ({timestamp:.1f}s)")
                
                # 运行所有检测
                self._check_garble(frame, frame_num, timestamp)
                self._check_overlap(frame, frame_num, timestamp)
                self._check_boundary(frame, frame_num, timestamp)
                self._check_contrast(frame, frame_num, timestamp)
            
            frame_num += 1
        
        cap.release()
        
        print(f"检测完成，发现 {len(self.issues)} 个问题")
        return self.issues
    
    def _check_garble(self, frame: np.ndarray, frame_num: int, timestamp: float):
        """检测乱码（使用 OCR 识别失败区域）"""
        if not self.config['ocr']['enabled']:
            return
        
        # TODO: 集成 PaddleOCR 或 Tesseract
        # 检测方框、问号等乱码特征
        pass
    
    def _check_overlap(self, frame: np.ndarray, frame_num: int, timestamp: float):
        """检测文字重叠"""
        if not self.config['overlap']['enabled']:
            return
        
        # 检测文字区域重叠
        # 1. 边缘检测
        # 2. 轮廓提取
        # 3. 计算重叠率
        pass
    
    def _check_boundary(self, frame: np.ndarray, frame_num: int, timestamp: float):
        """检测边界溢出"""
        if not self.config['boundary']['enabled']:
            return
        
        margin = self.config['boundary']['margin_pixels']
        h, w = frame.shape[:2]
        
        # 检测内容是否超出边界
        # 使用边缘检测找到内容边界
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 检查四边
        if np.sum(edges[:margin, :]) > 0:
            self.issues.append(DetectionIssue(
                type=IssueType.BOUNDARY,
                frame_number=frame_num,
                timestamp=timestamp,
                description="内容超出上边界",
                severity=0.8,
                bounding_box=(0, 0, w, margin),
                suggestion="向上调整内容位置或减小字体"
            ))
    
    def _check_contrast(self, frame: np.ndarray, frame_num: int, timestamp: float):
        """检测对比度不足"""
        if not self.config['contrast']['enabled']:
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算对比度（标准差）
        contrast = np.std(gray)
        
        # 对比度阈值（经验值）
        if contrast < 30:
            self.issues.append(DetectionIssue(
                type=IssueType.CONTRAST,
                frame_number=frame_num,
                timestamp=timestamp,
                description=f"对比度不足 ({contrast:.1f})",
                severity=0.6,
                bounding_box=(0, 0, frame.shape[1], frame.shape[0]),
                suggestion="增加背景与文字的对比度"
            ))
    
    def get_report(self) -> str:
        """生成检测报告"""
        if not self.issues:
            return "✅ 未检测到任何问题！"
        
        report = ["# Manim 视觉质量检测报告\n"]
        
        # 按类型统计
        stats = {}
        for issue in self.issues:
            key = issue.type.value
            stats[key] = stats.get(key, 0) + 1
        
        report.append("## 问题统计\n")
        for issue_type, count in stats.items():
            report.append(f"- {issue_type}: {count}")
        
        report.append("\n## 详细问题\n")
        for i, issue in enumerate(self.issues, 1):
            report.append(f"{i}. **{issue.type.value}** - 帧 {issue.frame_number} ({issue.timestamp:.1f}s)")
            report.append(f"   - {issue.description}")
            report.append(f"   - 严重程度：{issue.severity:.1f}")
            report.append(f"   - 建议：{issue.suggestion}\n")
        
        return "\n".join(report)


if __name__ == "__main__":
    # 测试
    checker = VisualChecker()
    issues = checker.detect("test_video.mp4")
    print(checker.get_report())
