"""
LTX2.3 System Prompt Generator for Prompt Relay
自动生成优化的 LTX2.3 视频提示词

Usage:
    generator = SystemPromptGenerator()
    result = generator.generate(
        subject="Elderly man walks on beach at sunset",
        reference_image_analysis="Beach scene with golden hour lighting, man in brown jacket"
    )
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SyntaxType(Enum):
    """提示词语法类型"""
    INLINE = "inline"      # 单行管道分隔
    BLOCK = "block"        # 多行块语法


@dataclass
class SegmentConfig:
    """单个段落配置"""
    text: str
    weight: float
    tokens: int
    is_initial: bool = False


@dataclass
class GenerationResult:
    """生成结果"""
    global_prompt: str
    local_prompts: List[str]
    segment_weights: List[float]
    segment_lengths: List[int]
    epsilon: float
    syntax_type: SyntaxType
    normalize_by_tokens: bool
    total_tokens: int
    quality_checks: Dict[str, bool]
    formatted_prompt: str
    relay_config: Dict


class SystemPromptGenerator:
    """LTX2.3 系统提示词生成器"""

    # 内容关键词映射
    AESTHETIC_STYLES = {
        "realistic": "photorealistic",
        "cinematic": "cinematic",
        "stylized": "stylized animation",
        "fantasy": "fantasy art style",
        "retro": "retro aesthetic",
        "modern": "contemporary style",
        "vintage": "vintage film",
        "scifi": "sci-fi aesthetic",
    }

    LIGHTING_PRESETS = {
        "day": "bright daylight, natural lighting",
        "sunset": "golden hour sunset, warm orange tones",
        "sunrise": "warm sunrise light, golden colors",
        "night": "night scene, soft ambient lighting",
        "neon": "neon lights, vibrant colors",
        "overcast": "soft overcast light, diffused shadows",
        "dramatic": "dramatic lighting, strong shadows",
        "soft": "soft diffused light, gentle shadows",
    }

    SHOT_TYPES = {
        "wide": "wide establishing shot",
        "medium": "medium shot",
        "closeup": "close-up shot",
        "overhead": "overhead perspective",
        "lowangle": "low angle shot",
        "profile": "side profile shot",
    }

    MOTION_DESCRIPTORS = {
        "walk": ["walks forward", "walking slowly", "strolls"],
        "turn": ["turns head", "rotates body", "faces direction"],
        "sit": ["sits down", "settles into seat", "takes seat"],
        "stand": ["stands up", "rises to feet", "lifts body"],
        "gaze": ["gazes at", "looks toward", "stares at"],
        "gesture": ["gestures with hand", "makes motion", "points toward"],
        "lean": ["leans forward", "bends body", "tilts toward"],
    }

    # Token 预算常量
    GLOBAL_TOKENS_MIN = 60
    GLOBAL_TOKENS_MAX = 80
    LOCAL_TOKENS_TOTAL = 150
    CLIP_TOKENS_LIMIT = 256

    def __init__(self):
        """初始化生成器"""
        self.quality_checks: Dict[str, bool] = {}

    def generate(
        self,
        subject: str,
        reference_image_analysis: str,
        force_syntax: Optional[SyntaxType] = None,
        target_segment_count: Optional[int] = None,
    ) -> GenerationResult:
        """
        主生成方法

        Args:
            subject: 视频主题描述
            reference_image_analysis: 参考图片分析文本
            force_syntax: 强制使用特定语法（内联或块）
            target_segment_count: 目标段数（如果不指定自动计算）

        Returns:
            GenerationResult 对象包含所有生成结果
        """
        # 1. 从参考图提取全局锚点
        global_prompt = self._extract_global_prompt(reference_image_analysis)

        # 2. 分析主题并生成段落
        segments = self._analyze_subject_and_generate_segments(
            subject, target_segment_count
        )

        # 3. 分配权重
        segment_weights = self._distribute_weights(segments)

        # 4. 决定语法类型
        syntax_type = force_syntax or self._determine_syntax(len(segments))

        # 5. 转换为 token 长度
        segment_lengths = self._convert_weights_to_lengths(
            segment_weights, self.LOCAL_TOKENS_TOTAL
        )

        # 6. 优化参数
        epsilon = self._calculate_epsilon(len(segments))
        normalize_by_tokens = len(segments) >= 3

        # 7. 格式化提示词
        local_prompts = [seg.text for seg in segments]
        formatted_prompt = self._format_prompt(
            global_prompt, local_prompts, segment_weights, syntax_type
        )

        # 8. 计算总 token 数
        total_tokens = self._estimate_tokens(global_prompt, local_prompts)

        # 9. 质量检查
        quality_checks = self._quality_check(
            global_prompt, local_prompts, segment_weights, total_tokens, syntax_type
        )

        # 10. 生成 Relay 配置
        relay_config = self._generate_relay_config(
            global_prompt,
            local_prompts,
            segment_weights,
            epsilon,
            normalize_by_tokens,
        )

        return GenerationResult(
            global_prompt=global_prompt,
            local_prompts=local_prompts,
            segment_weights=segment_weights,
            segment_lengths=segment_lengths,
            epsilon=epsilon,
            syntax_type=syntax_type,
            normalize_by_tokens=normalize_by_tokens,
            total_tokens=total_tokens,
            quality_checks=quality_checks,
            formatted_prompt=formatted_prompt,
            relay_config=relay_config,
        )

    def _extract_global_prompt(self, reference_analysis: str) -> str:
        """从参考图分析提取全局锚点"""
        # 关键词提取
        keywords = []

        # 检测美学风格
        for style_key, style_val in self.AESTHETIC_STYLES.items():
            if style_key.lower() in reference_analysis.lower():
                keywords.append(style_val)

        # 检测光照
        for light_key, light_val in self.LIGHTING_PRESETS.items():
            if light_key.lower() in reference_analysis.lower():
                keywords.append(light_val)

        # 检测镜头类型
        for shot_key, shot_val in self.SHOT_TYPES.items():
            if shot_key.lower() in reference_analysis.lower():
                keywords.append(shot_val)

        # 提取场景描述（环境细节）
        # 简单启发式：查找形容词和名词组合
        scene_keywords = self._extract_scene_keywords(reference_analysis)
        keywords.extend(scene_keywords)

        # 添加质量标签
        quality_tags = ["professional", "high detail", "4K cinematic"]
        keywords.extend(quality_tags)

        # 组合成全局提示词
        global_prompt = ", ".join(keywords[:10])  # 限制长度
        return global_prompt

    def _extract_scene_keywords(self, text: str) -> List[str]:
        """从文本中提取场景关键词"""
        keywords = []

        # 检测常见场景类型
        scenes = {
            "beach": "peaceful beach",
            "forest": "lush forest",
            "office": "professional office",
            "mountain": "mountain landscape",
            "river": "flowing river",
            "city": "urban cityscape",
            "garden": "beautiful garden",
            "room": "interior room",
        }

        for scene_key, scene_desc in scenes.items():
            if scene_key.lower() in text.lower():
                keywords.append(scene_desc)

        # 提取颜色信息
        colors = {
            "golden": "golden tones",
            "blue": "blue hues",
            "red": "warm red tones",
            "green": "lush green",
            "dark": "dark ambient",
            "bright": "bright lighting",
        }

        for color_key, color_desc in colors.items():
            if color_key.lower() in text.lower():
                keywords.append(color_desc)

        return keywords

    def _analyze_subject_and_generate_segments(
        self, subject: str, target_count: Optional[int] = None
    ) -> List[SegmentConfig]:
        """分析主题并生成段落"""

        # 自动计算段数（如果未指定）
        word_count = len(subject.split())
        if target_count is None:
            if word_count < 30:
                target_count = 2
            elif word_count < 60:
                target_count = 3
            elif word_count < 100:
                target_count = 4
            else:
                target_count = min(6, 2 + word_count // 40)

        segments = []

        # 第1段：初始静态状态
        initial_segment = self._create_initial_segment(subject)
        segments.append(initial_segment)

        # 生成后续段落
        for i in range(1, target_count):
            segment = self._create_motion_segment(subject, i, target_count)
            segments.append(segment)

        return segments

    def _create_initial_segment(self, subject: str) -> SegmentConfig:
        """创建初始静态段落"""
        # 提取名词和形容词，避免动词
        words = subject.split()
        static_words = []

        dynamic_verbs = {
            "walk",
            "run",
            "jump",
            "turn",
            "sit",
            "stand",
            "move",
            "gesture",
            "lean",
            "reach",
            "grab",
            "look",
            "gaze",
        }

        for word in words:
            clean_word = word.lower().rstrip(",.")
            if clean_word not in dynamic_verbs:
                static_words.append(word)

        # 添加静态描述符
        static_desc = " ".join(static_words[:8])
        static_desc += ", standing in natural pose, peaceful expression"

        return SegmentConfig(
            text=static_desc, weight=1.0, tokens=20, is_initial=True
        )

    def _create_motion_segment(
        self, subject: str, segment_index: int, total_segments: int
    ) -> SegmentConfig:
        """创建动作段落"""
        # 根据段位置推断动作
        progress = segment_index / total_segments

        # 简单的动作序列推断
        if progress < 0.4:
            motion_desc = "begins motion, body posture changes slightly"
        elif progress < 0.7:
            motion_desc = "continues deliberate movement, focused expression"
        else:
            motion_desc = "completing action, settling into final pose"

        # 添加方向或情感变化
        if "emotional" in subject.lower() or "expression" in subject.lower():
            motion_desc += ", facial expression shifts"
        elif "walk" in subject.lower() or "move" in subject.lower():
            motion_desc += ", measured steps forward"

        weight = 1.0 + (0.2 * segment_index)  # 逐段增加权重

        return SegmentConfig(text=motion_desc, weight=weight, tokens=15)

    def _distribute_weights(self, segments: List[SegmentConfig]) -> List[float]:
        """分配段落权重"""
        base_weights = [seg.weight for seg in segments]
        total_weight = sum(base_weights)

        # 归一化为相对权重
        normalized = [w / total_weight * 100 for w in base_weights]
        return normalized

    def _determine_syntax(self, segment_count: int) -> SyntaxType:
        """根据段数决定语法类型"""
        if segment_count <= 3:
            return SyntaxType.INLINE
        else:
            return SyntaxType.BLOCK

    def _convert_weights_to_lengths(
        self, weights: List[float], total_tokens: int
    ) -> List[int]:
        """将权重转换为绝对长度"""
        lengths = [int(w / 100 * total_tokens) for w in weights]

        # 确保和为 total_tokens
        diff = total_tokens - sum(lengths)
        if diff != 0:
            lengths[0] += diff

        return lengths

    def _calculate_epsilon(self, segment_count: int) -> float:
        """根据段数计算 epsilon 值"""
        if segment_count <= 2:
            return 0.001  # 锐利切割
        elif segment_count <= 5:
            return 0.15  # 平滑过渡
        else:
            return 0.3  # 极度平滑

    def _format_prompt(
        self,
        global_prompt: str,
        local_prompts: List[str],
        weights: List[float],
        syntax_type: SyntaxType,
    ) -> str:
        """格式化为最终提示词字符串"""

        if syntax_type == SyntaxType.INLINE:
            return self._format_inline(global_prompt, local_prompts, weights)
        else:
            return self._format_block(local_prompts, weights)

    def _format_inline(
        self, global_prompt: str, local_prompts: List[str], weights: List[float]
    ) -> str:
        """内联格式"""
        parts = [f"{global_prompt} [0-{weights[0]:.0f}]"]

        cumulative = weights[0]
        for i, prompt in enumerate(local_prompts[1:], 1):
            start = cumulative
            end = cumulative + weights[i]
            parts.append(f"{prompt} [{start:.0f}-{end:.0f}]")
            cumulative = end

        return " | ".join(parts)

    def _format_block(self, local_prompts: List[str], weights: List[float]) -> str:
        """块格式"""
        lines = []
        cumulative = 0

        for i, prompt in enumerate(local_prompts):
            if i == 0:
                lines.append("Scene 1:")
            else:
                start = cumulative
                end = cumulative + weights[i]
                lines.append(f"Scene {start:.0f}-{end:.0f}:")

            lines.append(prompt)
            lines.append("")
            cumulative += weights[i]

        return "\n".join(lines)

    def _estimate_tokens(self, global_prompt: str, local_prompts: List[str]) -> int:
        """估计总 token 数（简单启发式）"""
        # 粗略估计：每个单词 ~1.3 token
        all_text = global_prompt + " " + " ".join(local_prompts)
        word_count = len(all_text.split())
        return int(word_count * 1.3)

    def _quality_check(
        self,
        global_prompt: str,
        local_prompts: List[str],
        weights: List[float],
        total_tokens: int,
        syntax_type: SyntaxType,
    ) -> Dict[str, bool]:
        """质量检查"""
        checks = {}

        # 检查1：全局提示词中没有动作词
        dynamic_verbs = {"walk", "run", "turn", "jump", "sit", "stand", "move"}
        global_words = global_prompt.lower().split()
        checks["no_motion_in_global"] = not any(
            word in dynamic_verbs for word in global_words
        )

        # 检查2：第一段是静态描述
        first_local = local_prompts[0].lower()
        checks["first_segment_static"] = not any(
            verb in first_local for verb in dynamic_verbs
        )

        # 检查3：段落不重复
        checks["no_duplicates"] = len(local_prompts) == len(set(local_prompts))

        # 检查4：Token 预算内
        checks["within_token_budget"] = total_tokens <= self.CLIP_TOKENS_LIMIT

        # 检查5：每段有意义的长度
        checks["meaningful_lengths"] = all(len(p.split()) >= 3 for p in local_prompts)

        # 检查6：语法一致
        if syntax_type == SyntaxType.INLINE:
            checks["syntax_consistent"] = "|" in " | ".join(local_prompts)
        else:
            checks["syntax_consistent"] = True

        self.quality_checks = checks
        return checks

    def _generate_relay_config(
        self,
        global_prompt: str,
        local_prompts: List[str],
        weights: List[float],
        epsilon: float,
        normalize_by_tokens: bool,
    ) -> Dict:
        """生成 Prompt Relay JSON 配置"""

        # 将权重转换为绝对值（用于 segment_lengths）
        scale_factor = 100000.0
        segment_lengths = [int(w * scale_factor / 100) for w in weights]

        config = {
            "global_prompt": global_prompt,
            "local_prompts": " | ".join(local_prompts),
            "segment_lengths": ", ".join(str(l) for l in segment_lengths),
            "epsilon": epsilon,
            "normalize_by_tokens": normalize_by_tokens,
            "fps": 24.0,
            "time_units": "frames",
            "segment_count": len(local_prompts),
            "total_tokens_estimated": self._estimate_tokens(global_prompt, local_prompts),
        }

        return config

    def get_quality_report(self) -> str:
        """获取质量检查报告"""
        report = "=== 质量检查报告 ===\n"
        for check_name, result in self.quality_checks.items():
            status = "✓" if result else "✗"
            report += f"{status} {check_name}: {'PASS' if result else 'FAIL'}\n"
        return report


def example_usage():
    """使用示例"""
    generator = SystemPromptGenerator()

    subject = "Elderly man walks along a peaceful beach at sunset, stops to sit on rocks, watches the waves"

    reference_analysis = (
        "Beach scene with golden hour lighting, elderly man in brown jacket, "
        "rocky coastline, soft warm lighting, cinematic depth of field, 4K professional"
    )

    result = generator.generate(subject, reference_analysis)

    print("=== LTX2.3 系统提示词生成结果 ===\n")
    print("全局提示词:")
    print(result.global_prompt)
    print("\n本地提示词:")
    for i, p in enumerate(result.local_prompts, 1):
        print(f"  {i}. {p}")
    print("\n格式化提示词:")
    print(result.formatted_prompt)
    print("\n段数:", len(result.local_prompts))
    print("Epsilon:", result.epsilon)
    print("总 Tokens:", result.total_tokens)
    print("语法类型:", result.syntax_type.value)
    print("\n质量检查:")
    print(generator.get_quality_report())
    print("\nRelay 配置:")
    print(json.dumps(result.relay_config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    example_usage()
