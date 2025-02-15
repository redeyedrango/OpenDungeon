import os
from pathlib import Path
from ui.utils import aigirl_generator
from dotenv import load_dotenv

class CharacterImageHandler:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        # Ensure environment variables are loaded
        load_dotenv()
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            print("Warning: OPENROUTER_API_KEY not found in environment variables")

    def parse_character_data(self, char_data) -> dict:
        """Parse character data from either dictionary or string format"""
        print("\n=== Character Data Debugging ===")
        print(f"Input data type: {type(char_data)}")
        print("Raw character data:")
        print(char_data)
        
        if isinstance(char_data, dict):
            # Try to find backstory in multiple possible locations
            backstory = ""
            
            # Check if this is a character from party data
            if isinstance(char_data, str) or (not char_data.get('backstory') and char_data.get('name')):
                # Try to find the character in the party data
                party_members = self.game_manager.party or {}
                for member_data in party_members.values():
                    if isinstance(member_data, str):
                        if char_data.get('name', '') in member_data:
                            # Found the character in party data, extract backstory
                            lines = member_data.split('\n')
                            collecting_backstory = False
                            for line in lines:
                                if 'Backstory:' in line:
                                    collecting_backstory = True
                                    backstory += line.split('Backstory:', 1)[1].strip() + " "
                                elif collecting_backstory and line.strip() and not any(key in line for key in ['Equipment:', 'Personality:', 'Name:']):
                                    backstory += line.strip() + " "
                                elif collecting_backstory and any(key in line for key in ['Equipment:', 'Personality:', 'Name:']):
                                    collecting_backstory = False
                            break
            
            # If no backstory found in party data, check direct backstory field
            if not backstory and char_data.get('backstory'):
                backstory = char_data['backstory']
            
            print(f"\nExtracted backstory: {backstory}")
            
            parsed_data = {
                'name': char_data.get('name', ''),
                'race': char_data.get('race', ''),
                'class': char_data.get('class', ''),
                'backstory': backstory.strip(),
                'equipment': char_data.get('equipment', [])
            }
            
            print("\nParsed Data:")
            print(f"Name: {parsed_data['name']}")
            print(f"Race: {parsed_data['race']}")
            print(f"Class: {parsed_data['class']}")
            print(f"Backstory: {parsed_data['backstory']}")
            
            return parsed_data
            
        elif isinstance(char_data, str):
            # Handle string format with better debugging
            print("\nParsing string format:")
            lines = char_data.split('\n')
            parsed_data = {
                'name': '',
                'race': '',
                'class': '',
                'backstory': '',
                'equipment': []
            }
            
            in_backstory = False
            backstory_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if 'Backstory:' in line:
                    in_backstory = True
                    backstory_lines.append(line.split('Backstory:', 1)[1].strip())
                elif in_backstory and not any(key in line for key in ['Name:', 'Race:', 'Class:', 'Equipment:']):
                    backstory_lines.append(line)
                elif 'Name:' in line:
                    parsed_data['name'] = line.split('Name:', 1)[1].strip()
                elif 'Race:' in line:
                    parsed_data['race'] = line.split('Race:', 1)[1].strip()
                elif 'Class:' in line:
                    parsed_data['class'] = line.split('Class:', 1)[1].strip()
            
            parsed_data['backstory'] = ' '.join(backstory_lines)
            
            print("\nParsed string data:")
            print(f"Name: {parsed_data['name']}")
            print(f"Race: {parsed_data['race']}")
            print(f"Class: {parsed_data['class']}")
            print(f"Backstory: {parsed_data['backstory'][:200]}...")
            
            return parsed_data
        
        return char_data

    def determine_gender(self, char_data: dict) -> str:
        """Determine gender from character data"""
        backstory = char_data.get('backstory', '').lower()
        print("\n=== Gender Determination Debugging ===")
        print(f"Analyzing backstory ({len(backstory)} chars):")
        print(backstory)
        
        # Female indicators with weights
        female_indicators = {
            'her': 2, 'hers': 2, 'herself': 2,
            'female': 3, 'woman': 3, 'girl': 2,
            'priestess': 3, 'actress': 3, 'queen': 3
        }
        
        # Male indicators with weights
        male_indicators = {
            'his': 2, 'him': 2, 'himself': 2,
            'male': 3, 'boy': 2
        }
        
        # Count and log each found indicator
        print("\nFound gender indicators:")
        female_score = 0
        male_score = 0
        
        for word, weight in female_indicators.items():
            count = backstory.count(word)
            if count > 0:
                female_score += count * weight
                print(f"Female indicator '{word}' found {count} times (weight: {weight})")
                
        for word, weight in male_indicators.items():
            count = backstory.count(word)
            if count > 0:
                male_score += count * weight
                print(f"Male indicator '{word}' found {count} times (weight: {weight})")
        
        print(f"\nFinal scores - Female: {female_score}, Male: {male_score}")
        
        if female_score > male_score:
            return 'female'
        elif male_score > female_score:
            return 'male'
        else:
            name = char_data.get('name', '').strip()
            gender = 'female' if name.endswith(('a', 'ia', 'ra')) else 'male'
            print(f"No clear winner, using name '{name}' to determine: {gender}")
            return gender

    def parse_character_features(self, text):
        """Extract physical features from text"""
        features = {}
        text = text.lower()
        
        # Eye color detection
        eye_colors = ['blue', 'green', 'brown', 'hazel', 'amber', 'gray', 'violet', 'red', 'golden']
        for color in eye_colors:
            if f"{color} eye" in text:
                features['eye_color'] = color
                break
        
        # Scale color detection for Dragonborn
        scale_colors = ['blue', 'red', 'green', 'black', 'white', 'gold', 'silver', 
                       'bronze', 'copper', 'brass']
        for color in scale_colors:
            if any(phrase in text for phrase in [
                f"{color} scale", 
                f"{color} dragon", 
                f"{color}-scaled", 
                f"scales are {color}",
                f"scales of {color}"
            ]):
                features['scale_color'] = color
                break
        
        return features

    def generate_character_image_prompt(self, character_data):
        """Generate an optimized prompt for the image generator using a consistent template"""
        try:
            # Parse character data
            char_data = self.parse_character_data(character_data)
            
            # Get basic character info
            gender = self.determine_gender(char_data)
            race = char_data.get('race', 'Unknown')
            char_class = char_data.get('class', 'Unknown')
            
            # Parse backstory and personality for physical features
            all_text = (f"{char_data.get('backstory', '')} {char_data.get('personality', '')} "
                       f"{char_data.get('description', '')}")
            features = self.parse_character_features(all_text)
            
            # Get race-specific details
            race_info = self.race_features.get(race, {
                'features': ['distinctive features'],
                'colors': ['natural'],
                'background': 'fantasy landscape'
            })
            
            # Handle color selection
            import random
            if race == 'Dragonborn':
                # Use mentioned scale color or random if none specified
                color = features.get('scale_color', random.choice(race_info['colors']))
            else:
                color = random.choice(race_info['colors'])
            
            # Process equipment and other parts as before
            # ...existing equipment processing code...
            
            # Build the prompt with all details
            prompt = (
                f"CGI style {gender} {race} {char_class}, "
                f"with {color} {race_info['features'][0]}"
            )
            
            # Add eye color if found
            if 'eye_color' in features:
                prompt += f", {features['eye_color']} eyes"
            
            # Add equipment string
            equip_str = self.format_equipment_string(char_data.get('equipment', []))
            prompt += f", {equip_str}"
            
            # Add style and background
            background = self.class_backgrounds.get(char_class, race_info['background'])
            prompt += (f", 3D cartoon art style, Pixar-inspired, determined expression, "
                      f"magical effects, in a {background}")
            
            print(f"Generated prompt: {prompt}")  # Debug output
            return prompt
            
        except Exception as e:
            print(f"Error generating prompt: {e}")
            return "CGI style fantasy adventurer, 3D cartoon art style, Pixar-inspired, fantasy background"

    def format_equipment_string(self, equipment):
        """Format equipment into a clear string"""
        equipment_details = self.categorize_equipment(equipment)
        
        equip_parts = []
        
        # Add weapons first
        if equipment_details['weapons']:
            equip_parts.append(f"wielding {', '.join(equipment_details['weapons'])}")
        
        # Add armor next
        if equipment_details['armor']:
            equip_parts.append(f"wearing {', '.join(equipment_details['armor'])}")
        
        # Add instruments (important for bards)
        if equipment_details['instruments']:
            equip_parts.append(f"carrying {', '.join(equipment_details['instruments'])}")
        
        # Add accessories last
        if equipment_details['accessories']:
            equip_parts.append(f"adorned with {', '.join(equipment_details['accessories'])}")
        
        return ', '.join(equip_parts) if equip_parts else 'in adventuring gear'

    def categorize_equipment(self, equipment):
        """Categorize equipment items"""
        categories = {
            'weapons': [],
            'armor': [],
            'instruments': [],
            'accessories': []
        }
        
        # Keywords for categorization
        weapon_keywords = ['sword', 'axe', 'bow', 'staff', 'dagger', 'mace', 'weapon', 'blade']
        armor_keywords = ['armor', 'mail', 'shield', 'plate', 'leather', 'robe', 'cloak']
        instrument_keywords = ['lute', 'flute', 'drum', 'horn', 'harp', 'violin', 'instrument']
        accessory_keywords = ['ring', 'amulet', 'necklace', 'pendant', 'bracelet', 'belt', 'pouch']
        
        # Process each item
        items = equipment if isinstance(equipment, list) else [equipment]
        for item in items:
            if isinstance(item, str):
                item = item.strip()
                item_lower = item.lower()
                
                # Categorize based on keywords
                if any(keyword in item_lower for keyword in weapon_keywords):
                    categories['weapons'].append(item)
                elif any(keyword in item_lower for keyword in armor_keywords):
                    categories['armor'].append(item)
                elif any(keyword in item_lower for keyword in instrument_keywords):
                    categories['instruments'].append(item)
                elif any(keyword in item_lower for keyword in accessory_keywords):
                    categories['accessories'].append(item)
                else:
                    # Add to accessories if doesn't match other categories
                    categories['accessories'].append(item)
        
        return categories

    # Add these as class variables
    race_features = {
        'Dragonborn': {
            'features': ['vibrant scales', 'dragon-like head', 'powerful tail'],
            'colors': ['bronze', 'copper', 'brass', 'gold', 'silver', 'blue', 'red', 'black', 'white', 'green'],
            'background': 'ancient dragon temple'
        },
        'Tiefling': {
            'features': ['curved horns', 'pointed tail', 'unusual skin tone'],
            'colors': ['deep red', 'purple', 'blue'],
            'background': 'gothic city streets'
        },
        'Elf': {
            'features': ['pointed ears', 'elegant features', 'slender build'],
            'colors': ['fair', 'pale', 'golden'],
            'background': 'mystical forest'
        },
        'Dwarf': {
            'features': ['braided beard', 'stocky build', 'ornate armor details'],
            'colors': ['ruddy', 'weathered', 'earth-toned'],
            'background': 'dwarven forge'
        },
        'Half-Orc': {
            'features': ['prominent tusks', 'muscular build', 'scarred'],
            'colors': ['green-tinted', 'gray', 'olive'],
            'background': 'tribal warcamp'
        }
    }
    
    class_backgrounds = {
        'Bard': 'vibrant tavern stage',
        'Wizard': 'magical library',
        'Warlock': 'dark ritual chamber',
        'Cleric': 'holy temple sanctuary',
        'Druid': 'ancient stone circle',
        'Ranger': 'deep wilderness',
        'Rogue': 'shadowy alleyway',
        'Fighter': 'training grounds',
        'Paladin': 'holy cathedral',
        'Barbarian': 'tribal wilderness',
        'Sorcerer': 'mystical ruins',
        'Monk': 'mountain monastery'
    }

    def generate_and_save_image(self, character_data, save_dir):
        """Generate and save character image with character-specific filename"""
        try:
            # Create save directory if it doesn't exist
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            # Create a character-specific filename
            char_name = character_data['name'].replace(' ', '_').lower()
            char_race = character_data['race'].lower()
            char_class = character_data['class'].lower()
            filename = f"{char_name}_{char_race}_{char_class}_portrait.png"
            
            # Full path for the image
            image_path = os.path.join(save_dir, filename)
            
            # Generate optimized prompt
            image_prompt = self.generate_character_image_prompt(character_data)
            print(f"Generated image prompt: {image_prompt}")  # Debug print
            
            # Import the module directly to ensure we're using the correct one
            from ui.utils.aigirl_generator import generate_image
            
            # Generate image using the imported function
            result_path = generate_image(image_prompt, image_path)
            
            if result_path and os.path.exists(result_path):
                print(f"Image successfully generated at: {result_path}")
                return result_path
            else:
                print("Image generation failed - no path returned")
                return None
            
        except Exception as e:
            print(f"Error generating character image: {e}")
            import traceback
            traceback.print_exc()  # Print full error traceback
            return None

