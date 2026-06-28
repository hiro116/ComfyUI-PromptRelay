"""
LTX2.3 Prompt Engineering System for Image-to-Video Generation
支持PromptRelay格式的图生视频提示词工程
"""

class LTX23PromptEngineer:
    """LTX2.3 图生视频系统提示词工程"""
    
    def __init__(self):
        self.supported_models = ["ltx2.3", "ltx-video"]
        self.sensory_keywords = {
            "motion": [
                "fluid motion", "dynamic movement", "explosive energy",
                "kinetic force", "powerful momentum", "graceful flow",
                "rapid acceleration", "vibrant vitality"
            ],
            "visual_intensity": [
                "vivid colors", "sharp contrast", "cinematic lighting",
                "high definition detail", "dramatic shadows",
                "brilliant luminosity", "saturated tones"
            ],
            "human_action": [
                "intense facial expression", "muscular tension",
                "deliberate gestures", "palpable energy",
                "embodied emotion", "visceral impact",
                "authentic physicality", "raw presence"
            ],
            "texture_touch": [
                "tactile quality", "textured surface",
                "material substance", "sensory depth",
                "gritty realism", "smooth elegance"
            ]
        }
    
    def analyze_subject(self, subject: str, image_description: str, include_human_action: bool = False) -> dict:
        """
        分析用户输入的主题和图片
        Analyze user input theme and image
        
        Args:
            subject: 用户输入的主题 (User input theme)
            image_description: 图片描述 (Image description)
            include_human_action: 是否包含人物动作 (Whether to include human action)
        
        Returns:
            分析结果字典 (Analysis result dictionary)
        """
        return {
            "subject": subject,
            "image_analysis": image_description,
            "has_human_action": include_human_action,
            "sensory_focus": self._determine_sensory_focus(image_description, include_human_action)
        }
    
    def _determine_sensory_focus(self, description: str, has_human_action: bool) -> list:
        """确定感官刺激重点"""
        focus = ["visual_intensity", "motion"]
        if has_human_action:
            focus.append("human_action")
        if any(word in description.lower() for word in ["texture", "surface", "fabric", "material"]):
            focus.append("texture_touch")
        return focus
    
    def generate_prompt(self, subject: str, image_description: str, 
                       segments: int = 3, include_human_action: bool = False,
                       syntax_style: str = "block") -> dict:
        """
        生成PromptRelay格式的提示词
        Generate PromptRelay format prompts
        
        Args:
            subject: 主题 (Theme)
            image_description: 图片描述 (Image description)
            segments: 视频段数 (Number of segments)
            include_human_action: 是否包含人物动作 (Include human action)
            syntax_style: 语法风格 - "block" 或 "inline" (Syntax style)
        
        Returns:
            包含英文和中文提示词的字典
        """
        analysis = self.analyze_subject(subject, image_description, include_human_action)
        
        if syntax_style == "block":
            en_prompt = self._generate_block_prompt(subject, image_description, segments, include_human_action)
            zh_prompt = self._generate_block_prompt_zh(subject, image_description, segments, include_human_action)
        else:
            en_prompt = self._generate_inline_prompt(subject, image_description, segments, include_human_action)
            zh_prompt = self._generate_inline_prompt_zh(subject, image_description, segments, include_human_action)
        
        return {
            "analysis": analysis,
            "prompt_relay_english": en_prompt,
            "prompt_relay_chinese": zh_prompt,
            "syntax_style": syntax_style,
            "segments": segments,
            "sensory_keywords_used": self._get_sensory_keywords_for_focus(analysis["sensory_focus"])
        }
    
    def _generate_block_prompt(self, subject: str, image_description: str, 
                              segments: int, include_human_action: bool) -> str:
        """生成Block风格的英文提示词"""
        
        # Segment 1: Static description from image
        segment1 = f"Segment 1:\n{image_description}\n"
        
        # Determine motion intensity
        sensory_words = []
        if include_human_action:
            sensory_words.extend(self.sensory_keywords["human_action"][:2])
        sensory_words.extend(self.sensory_keywords["motion"][:2])
        sensory_words.extend(self.sensory_keywords["visual_intensity"][:2])
        
        segments_text = segment1
        
        # Generate remaining segments based on subject
        motions = self._generate_motion_segments(subject, segments - 1, include_human_action)
        for i, motion in enumerate(motions, 2):
            segments_text += f"Segment {i}:\n{motion}\n"
        
        return segments_text.strip()
    
    def _generate_block_prompt_zh(self, subject: str, image_description: str,
                                 segments: int, include_human_action: bool) -> str:
        """生成Block风格的中文提示词"""
        
        segment1 = f"第1段：\n{image_description}\n"
        
        segments_text = segment1
        
        motions = self._generate_motion_segments_zh(subject, segments - 1, include_human_action)
        for i, motion in enumerate(motions, 2):
            segments_text += f"第{i}段：\n{motion}\n"
        
        return segments_text.strip()
    
    def _generate_inline_prompt(self, subject: str, image_description: str,
                               segments: int, include_human_action: bool) -> str:
        """生成Inline风格的英文提示词"""
        
        parts = [image_description]
        
        motions = self._generate_motion_segments(subject, segments - 1, include_human_action)
        parts.extend(motions)
        
        return " | ".join(parts)
    
    def _generate_inline_prompt_zh(self, subject: str, image_description: str,
                                  segments: int, include_human_action: bool) -> str:
        """生成Inline风格的中文提示词"""
        
        parts = [image_description]
        
        motions = self._generate_motion_segments_zh(subject, segments - 1, include_human_action)
        parts.extend(motions)
        
        return " | ".join(parts)
    
    def _generate_motion_segments(self, subject: str, num_segments: int, 
                                 include_human_action: bool) -> list:
        """生成运动段落 - 英文"""
        
        segments = []
        
        # Common motion patterns
        base_motions = {
            "person": [
                f"character from {subject} begins moving with {self.sensory_keywords['motion'][0]}, {self.sensory_keywords['human_action'][0]}",
                f"intense action sequence, {self.sensory_keywords['motion'][1]}, vivid {self.sensory_keywords['visual_intensity'][0]}",
                f"climactic moment, powerful {self.sensory_keywords['human_action'][2]}, explosive {self.sensory_keywords['motion'][2]}"
            ],
            "object": [
                f"{subject} transforms with {self.sensory_keywords['motion'][0]}, evolving visually",
                f"dynamic interaction, {self.sensory_keywords['motion'][3]}, enhanced {self.sensory_keywords['visual_intensity'][1]}",
                f"climactic transformation, {self.sensory_keywords['motion'][4]}, sustained energy"
            ],
            "scene": [
                f"scene transitions with {self.sensory_keywords['motion'][0]}, {self.sensory_keywords['visual_intensity'][2]} ambiance",
                f"dynamic changes unfold with {self.sensory_keywords['motion'][1]}, evolving environment",
                f"powerful conclusion with {self.sensory_keywords['motion'][2]}, cinematic finale"
            ]
        }
        
        motion_type = "person" if include_human_action else ("object" if any(x in subject.lower() for x in ["object", "thing", "item"]) else "scene")
        motions = base_motions.get(motion_type, base_motions["scene"])
        
        for i in range(min(num_segments, len(motions))):
            segments.append(motions[i])
        
        # Fill remaining with generic motions if needed
        while len(segments) < num_segments:
            segments.append(f"continued motion with {self.sensory_keywords['motion'][-1]}, sustaining momentum")
        
        return segments[:num_segments]
    
    def _generate_motion_segments_zh(self, subject: str, num_segments: int,
                                    include_human_action: bool) -> list:
        """生成运动段落 - 中文"""
        
        segments = []
        
        base_motions = {
            "person": [
                f"{subject}的角色开始移动，充满流畅的运动感，展现强烈的肌肉张力",
                f"激烈的动作序列，动态势能十足，生动的色彩对比和戏剧性光影",
                f"高潮时刻，力量十足的姿态，爆发式的能量释放"
            ],
            "object": [
                f"{subject}伴随流畅运动进行转变，视觉效果不断演化",
                f"动态交互过程，充满动能，视觉对比增强",
                f"高潮转变，力量持续释放，震撼视觉效果"
            ],
            "scene": [
                f"场景以流畅运动进行转换，戏剧性光影营造氛围",
                f"动态变化不断展开，场景环境演化变化",
                f"强有力的结局，史诗级的视觉呈现"
            ]
        }
        
        motion_type = "person" if include_human_action else ("object" if any(x in subject.lower() for x in ["物体", "东西", "物件"]) else "scene")
        motions = base_motions.get(motion_type, base_motions["scene"])
        
        for i in range(min(num_segments, len(motions))):
            segments.append(motions[i])
        
        while len(segments) < num_segments:
            segments.append("持续的动感运动，保持势能")
        
        return segments[:num_segments]
    
    def _get_sensory_keywords_for_focus(self, focus_list: list) -> dict:
        """获取焦点相关的感官词汇"""
        result = {}
        for focus in focus_list:
            if focus in self.sensory_keywords:
                result[focus] = self.sensory_keywords[focus][:3]
        return result
    
    def format_for_promptrelay(self, prompt_data: dict, use_global_prompt: bool = True) -> str:
        """
        格式化为纯文本PromptRelay格式
        Format as plain text for PromptRelay
        
        Args:
            prompt_data: 提示词数据
            use_global_prompt: 是否使用全局提示词
        
        Returns:
            纯文本格式的提示词
        """
        output = "=== LTX2.3 PROMPTRELAY PROMPT ===\n\n"
        
        output += "ENGLISH PROMPT:\n"
        output += "-" * 40 + "\n"
        output += prompt_data["prompt_relay_english"] + "\n\n"
        
        output += "CHINESE TRANSLATION:\n"
        output += "-" * 40 + "\n"
        output += prompt_data["prompt_relay_chinese"] + "\n\n"
        
        if use_global_prompt:
            output += "NOTE: First segment serves as global_prompt anchor\n"
            output += "Global prompt captures static scene details\n"
        
        return output


def create_ltx23_prompt(subject: str, image_description: str, 
                       segments: int = 3, include_human_action: bool = False,
                       syntax_style: str = "block") -> str:
    """
    快速创建LTX2.3提示词的便捷函数
    Quick function to create LTX2.3 prompts
    """
    engineer = LTX23PromptEngineer()
    prompt_data = engineer.generate_prompt(
        subject=subject,
        image_description=image_description,
        segments=segments,
        include_human_action=include_human_action,
        syntax_style=syntax_style
    )
    return engineer.format_for_promptrelay(prompt_data)


if __name__ == "__main__":
    # Example usage
    engineer = LTX23PromptEngineer()
    
    prompt = engineer.generate_prompt(
        subject="professional dancer performing contemporary movement",
        image_description="A female dancer in flowing white silk costume standing in center stage with dramatic blue lighting, poised gracefully with arms extended",
        segments=3,
        include_human_action=True,
        syntax_style="block"
    )
    
    print(engineer.format_for_promptrelay(prompt))
