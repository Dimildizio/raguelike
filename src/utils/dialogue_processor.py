import ollama
from typing import Dict

class DialogueProcessor:
    def __init__(self, host="http://localhost:11434", model="gemma2:2b"):
        self.client = ollama.Client(host=host)
        self.model = model

    def process_dialogue(self,
                        player_input: str,
                        npc_name: str,
                        npc_mood:str,
                        player_reputation: int,
                        active_quests: list,
                        interaction_history: list = []) -> Dict:

        history_text = ""
        if interaction_history:
            history_text = "Previous interactions:\n"
            for interaction in interaction_history:
                history_text += f"Player: {interaction['player']}\n"
                history_text += f"NPC {npc_name}: {interaction['npc']}\n"

        # Construct the system prompt with examples
        system_prompt = """You are an NPC dialogue processing system in a fantasy RPG game.  Try to keep it short but in character.
        Do not come up with any game-related information that you are not provided with (no quests or rumors except the one that are given to you).
        You can give reward only if the quest has a status 'finished': true, you cannot give reward more than once or change the amount after you have given it, you cannot promise more than reward + extra_bargain_reward but you can promise less if you dont like the adventurer.
        Do not go out of character and discuss non-game things, apologize and say you dont understand.
        Process player input and respond as the NPC, considering context and player reputation.
        Respond in JSON format with 'player_inappropriate_request' (true/false), 'further_action': (reward, stop, wait), 'text' (NPC's response) .

        Examples:
        Player: "Hello there!"
        Context: {{reputation: 50, npc: "Merchant Tom", quests: []}}
        Response: {{"player_inappropriate_request": false, , "further_action": "wait", "text": "Welcome to my shop, traveler! How may I help you today?"}}

        Player: "Give me all your money or die!"
        Context: {{reputation: 30, npc: "Noble Billy", quests: []}}
        Response: {{"player_inappropriate_request": true, "further_action": "stop", "text": "Guards! We've got a troublemaker here!"}}

        Player: "I've completed the delivery quest."
        Context: {{reputation: 40, npc: "Lady Anna", quests: [quest_description: 'Deliver package to Lady Anna', enemies_amount: 'unknown, maybe some bandints', finished: false, reward: '50 gold', extra_bargain_reward:"10 gold"]}}
        Response: {{"player_inappropriate_request": false, "further_action": "reward", "text": "Ah, excellent work! Here's your reward. You've proven yourself reliable!"}}

        
        Player: "Bye! Have good day!"
        Context: {{reputation: 50, npc: "Vallager Amelia", quests: []}}
        Response: {{"player_inappropriate_request": false, "further_action": "stop", "text": "See you, handsome! It was a pleasure to talk to you!", }}


        Current context:
        Your name: {npc_name}
        Your mood: {npc_mood}
        Player reputation: {player_reputation}
        Active quests: {active_quests}
        Recent interactions: {history_text}

        Process the following player input maintaining character and considering context.
        Respond only in the specified JSON format.

        Player input: {player_input}"""


        formatted_prompt = system_prompt.format(
            npc_name=npc_name,
            npc_mood=npc_mood,
            player_reputation=player_reputation,
            active_quests=[{'quest_description': 'kill goblins nearby', 'enemies_amount': '2 goblins 1 wolf', 'finished': 'False', 'reward': '50 gold', 'extra_bargain_reward': "10 gold"}],
            history_text=history_text,
            player_input=player_input
        )
        if not self.client:
            return {"player_inappropriate_request": False,
                    "further_action": "stop",
                    "text": "Sorry, I'm not in a mood for talking today."
            }

        try:
            stream = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'system',
                    'content': formatted_prompt
                }],
                stream=True
            )

            return stream
        except Exception as e:
            print(f"Error processing dialogue: {e}")
            return {"player_inappropriate_request": False,
                    "further_action": "wait",
                    "text": "Sorry, I'm having trouble understanding you right now."
            }