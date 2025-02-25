import os
from pathlib import Path
from ui.utils import aigirl_generator
from datetime import datetime

class SceneImageHandler:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.scenes_dir = os.path.join(self.base_path, 'generated_scenes')
        os.makedirs(self.scenes_dir, exist_ok=True)
        
    def optimize_scene_prompt(self, scene_text: str) -> str:
        """Get an optimized image generation prompt from the scene description"""
        prompt = f"""Convert this D&D scene description into a clear, focused image generation prompt.
Focus on visual elements only. Keep within 100 words. Make it suitable for ai image generation.

Scene: {scene_text}

Format as a single detailed description focused on:
- Main subject/action
- Key visual elements
- Lighting and atmosphere
- Art style guidance

Do not include: dialogue, game mechanics, or non-visual elements.
"""
        try:
            response = self.game_manager.get_dm_response_from_api(prompt)
            # Clean up the response
            response = response.replace('\n', ' ').strip()
            return response
        except Exception as e:
            print(f"Error optimizing scene prompt: {e}")
            return f"fantasy scene with {scene_text}"

    def generate_scene_image(self, scene_text: str) -> str:
        """Generate an image for the scene and return the file path"""
        try:
            # Get optimized prompt
            image_prompt = self.optimize_scene_prompt(scene_text)
            
            # Create unique filename using timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"scene_{timestamp}.png"
            image_path = os.path.join(self.scenes_dir, filename)
            
            # Generate image
            result_path = aigirl_generator.generate_image(image_prompt, image_path)
            
            if result_path and os.path.exists(result_path):
                print(f"Scene image generated: {result_path}")
                return result_path
            else:
                print("Failed to generate scene image")
                return None
                
        except Exception as e:
            print(f"Error generating scene image: {e}")
            return None
