import ollama
from typing import Dict

class DialogueProcessor:
    def __init__(self, host="http://localhost:11434", model="gemma2:2b"):
        self.client = ollama.Client(host=host)
        self.model = model

    def process_dialogue(self,
                        player_input: str,
                        npc_name: str,
                        player_reputation: int,
                        active_quests: list,
                        interaction_history: list = []) -> Dict:

        history_text = ""
        if interaction_history:
            history_text = "Previous interactions:\n"
            for interaction in interaction_history:
                print('KEYS: ', interaction.keys())
                history_text += f"Player: {interaction['player']}\n"
                history_text += f"NPC {npc_name}: {interaction['npc']}\n"

        # Construct the system prompt with examples
        system_prompt = """You are an NPC dialogue processing system in a fantasy RPG game.  Try to keep it short but in character.
        Do not come up with any game-related information that you are not provided with (no quests or rumors except the one that are given to you).
        Do not go out of character and discuss non-game things, apologize and say you dont understand.
        Process player input and respond as the NPC, considering context and player reputation.
        Respond in JSON format with 'text' (NPC's response) and 'player_inappropriate_request' (true/false).

        Examples:
        Player: "Hello there!"
        Context: {{reputation: 50, npc: "Merchant Tom", quests: []}}
        Response: {{"text": "Welcome to my shop, traveler! How may I help you today?", "player_inappropriate_request": false, "further_action": "continue_dialogue"}}

        Player: "Give me all your money or die!"
        Context: {{reputation: 30, npc: "Merchant Tom", quests: []}}
        Response: {{"text": "Guards! We've got a troublemaker here!", "player_inappropriate_request": true, "further_action": "stop_dialogue"}}

        Player: "I've completed the delivery quest."
        Context: {{reputation: 40, npc: "Merchant Tom", quests: ["Deliver package to Tom"]}}
        Response: {{"text": "Ah, excellent work! Here's your reward. You've proven yourself reliable.", "player_inappropriate_request": false, "further_action": "reward_dialogue"}}

        
        Player: "Bye! Have good day!"
        Context: {{reputation: 50, npc: "Vallager Amelia", quests: []}}
        Response: {{"text": "See you, handsome! It was a pleasure to talk to you!", "player_inappropriate_request": false, "further_action": "stop_dialogue"}}


        Current context:
        Your name: {npc_name}
        Player reputation: {player_reputation}
        Active quests: {active_quests}
        Recent interactions: {history_text}

        Process the following player input maintaining character and considering context.
        Respond only in the specified JSON format.

        Player input: {player_input}"""

        formatted_prompt = system_prompt.format(
            npc_name=npc_name,
            player_reputation=player_reputation,
            active_quests=[{'quest_description': 'kill goblins nearby', 'enemies_amount': '2 goblins 1 wolf', 'finished': 'False', 'reward': '50 gold', 'extra_bargain_reward':"10 gold"}],
            history_text=history_text,
            player_input=player_input
        )

        if not self.client:
            return {
                "text": "Sorry, the dialogue system is currently unavailable.",
                "player_inappropriate_request": False
            }

        try:
            response = self.client.chat(model=self.model, messages=[
                {
                    'role': 'system',
                    'content': formatted_prompt
                }
            ])
            print('im response', formatted_prompt, response)
            return response['message']['content']
        except Exception as e:
            print(f"Error processing dialogue: {e}")
            return {
                "text": "Sorry, I'm having trouble understanding you right now.",
                "player_inappropriate_request": False
            }