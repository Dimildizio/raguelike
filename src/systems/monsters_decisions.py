import json
from typing import Dict, Optional


class MonsterDecisionMaker:
    def __init__(self, dialogue_processor):
        self.dialogue_processor = dialogue_processor

    def get_base_prompt(self, monster_context: Dict) -> str:
        """Generate base prompt for monster decision making"""
        return f"""You are a {monster_context['monster type']} named {monster_context['monster name']} with {monster_context['personality']} personality.
        Current situation:
        - Your health status: {monster_context['monster health']}
        - Player health: {monster_context.get('player_health', 'unknown')}
        - Distance to player: {monster_context.get('distance', 'unknown')} tiles
        - Number of nearby allies: {len(monster_context.get('nearby_monsters', []))}
        - Dialog cooldown: {monster_context.get('dialog_cooldown', 0)}
        - You have {monster_context.get('gold', 0)} gold
        - You are{' not' if not monster_context.get('is_fleeing') else ''} fleeing
        
        You cannot talk if Dialog cooldown is above 0

        Based on this situation, decide ONE action to take.

        Format response as JSON with single field:
        "decision": "value"

        Where value must be exactly ONE of:
        - "approach" (move towards player)
        - "attack" (if adjacent to player)
        - "moveto" (wander around if uninterested in player)
        - "talk" (try to initiate dialogue)
        - "flee" (run away from player)
        

        DO NOT include any explanation or additional fields."""

    def get_monster_specific_prompt(self, monster_type: str) -> str:
        """Get monster-specific decision criteria"""
        prompts = {
            "goblin": """You are cowardly and prefer to attack in groups. 
            - More likely to flee when alone or low health
            - Prefer to attack when allies are nearby
            - You try to talk only of you are begging to save your life when low hp""",

            "green_troll": """You are aggressive and confrontational.
            - You do not talk
            - Prefer direct combat
            - Only flee at very low health""",

            "blue_troll": """You are dumb but curious
            - You love talking and you love riddles
            - Prefer direct combat
            - Only flee at very low health""",

            "willow_whisper": """You are a mysterious spirit.
            - Always prefer to talk first
            - You are not interested in player trying to "moveto"
            - You never flee
            - Move around randomly when hostile""",

            "dryad": """You get stronger whe next to tree.
            - Prefer to "moveto" trees 
            - If player is nearby you can attack
            - If you are next to a tree you try to talk and lure player closer
            - More aggressive when transformed
            - Like to talk about nature""",

            "kobold": """You are an intellectual teacher.
            - Always try to talk first
            - You love talking
            - if you cannot talk you attack
            - Flee if heavily damaged""",

            "demon_bard": """You are a cursed bard.
            - Always try to talk and be a poet
            - You love talking
            - if you cannot talk you attack
            - never flee"""

        }
        return prompts.get(monster_type, "")

    def get_decision(self, monster_context: Dict) -> str:
        """Get LLM-based decision for monster action"""
        fallback = 'approach' if monster_context.get('distance', 2) <= 1 else 'approach'
        base_prompt = self.get_base_prompt(monster_context)
        specific_prompt = self.get_monster_specific_prompt(monster_context['monster type'])

        full_prompt = f"{base_prompt}\n\n{specific_prompt}"

        try:
            response = self.dialogue_processor.client.chat(
                model=self.dialogue_processor.model,
                messages=[{'role': 'system', 'content': full_prompt}]
            )

            content = response['message']['content']
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx + 1]
            self.dialogue_processor.logger.info(f'MONSTER DECISION: {content}')
            decision_data = json.loads(content)
            return decision_data.get('decision', fallback)

        except Exception as e:
            print(f"Error getting monster decision: {e}")
            return fallback
