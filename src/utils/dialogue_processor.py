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
                        interaction_history: list) -> Dict:

        # Construct the system prompt with examples
        system_prompt = """You are an NPC dialogue processing system in a fantasy RPG game.
        Process player input and respond as the NPC, considering context and player reputation.
        Respond in JSON format with 'text' (NPC's response) and 'player_inappropriate_request' (true/false).

        Examples:
        Player: "Hello there!"
        Context: {{reputation: 50, npc: "Merchant Tom", quests: []}}
        Response: {{"text": "Welcome to my shop, traveler! How may I help you today?", "player_inappropriate_request": false}}

        Player: "Give me all your money or die!"
        Context: {{reputation: 30, npc: "Merchant Tom", quests: []}}
        Response: {{"text": "Guards! We've got a troublemaker here!", "player_inappropriate_request": true}}

        Player: "I've completed the delivery quest."
        Context: {{reputation: 40, npc: "Merchant Tom", quests: ["Deliver package to Tom"]}}
        Response: {{"text": "Ah, excellent work! Here's your reward. You've proven yourself reliable.", "player_inappropriate_request": false}}

        Current context:
        NPC: {npc_name}
        Player reputation: {player_reputation}
        Active quests: {active_quests}
        Recent interactions: {interaction_history}

        Process the following player input maintaining character and considering context.
        Respond only in the specified JSON format.

        Player input: {player_input}"""

        formatted_prompt = system_prompt.format(
            npc_name=npc_name,
            player_reputation=player_reputation,
            active_quests=active_quests,
            interaction_history=interaction_history,
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

            return response['message']['content']
        except Exception as e:
            print(f"Error processing dialogue: {e}")
            return {
                "text": "Sorry, I'm having trouble understanding you right now.",
                "player_inappropriate_request": False
            }