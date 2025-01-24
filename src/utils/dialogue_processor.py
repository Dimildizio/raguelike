import ollama
import json
from typing import Dict, Optional, Any
import logging
from .rag_manager import RAGManager



class DialogueProcessor:
    def __init__(self, host="http://localhost:11434", model="gemma2:2b"):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        try:
            self.client = ollama.Client(host=host)
            self.model = model
            self.rag_manager = RAGManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize DialogueProcessor: {e}")
            raise

    def process_dialogue(self,
                         player_input: str,
                         npc: Any,
                         player_reputation: int,
                         game_state: Any,
                         interaction_history: list = []) -> Dict:

        # Convert NPC name to id format
        npc_id = npc.name.lower().replace(' ', '_')

        try:
            # Create a combined query using current input and last interaction if available
            combined_query = player_input
            if interaction_history:
                last_interaction = interaction_history[-1]
                combined_query = f"{last_interaction['player']} {last_interaction['npc']} {player_input}"

            # Query using the combined context
            relevant_info = self.rag_manager.query(npc_id, combined_query)
            relevant_dialogues = [d[0] for d in self.rag_manager.query_dialogue_history(npc_id, combined_query, k=5)]

            # Format relevant information
            context_from_rag = "\nRelevant information:\n"
            for info, score, source in relevant_info:
                if score < 100:  # Only include if similarity score is good enough
                    print(f"\nSource: {source}")
                    print(f"Similarity Score: {score}")
                    print(f"Content: {info[:200]}...")  # First 200 chars for preview

                    prefix = "General knowledge: " if source == 'world' else f"{npc.name}'s knowledge: "
                    context_from_rag += f"{prefix}{info}\n"

            quest_info = game_state.quest_manager.format_quest_status(npc_id)

            # Construct the system prompt
            system_prompt = f"""You are an NPC named {npc.name} in a fantasy RPG game. 
            Your current mood is {npc.mood}.
            The player's reputation with you is {player_reputation}/100.

            You are aware of the following information:
            {context_from_rag}

            {quest_info}
            {npc.negotiate_reward_prompt()}
            You currently have {npc.money} gold."

            
            Recent conversation history:
            {json.dumps(interaction_history[-min(5, len(interaction_history)):], 
                        indent=2) if interaction_history else "No recent interactions."}
            
            Relevant dialogues with player:
            {relevant_dialogues}
            
            Respond in character as {npc.name}, {npc.description}, considering your mood, the player's reputation, and your knowledge.
                    
            Format your response as JSON with these fields:
            - player_inappropriate_request (boolean)
            - further_action (string: "give_quest", "reward", "stop", "negotiate_reward", or "wait")
            - quest_id (string, only if further_action is "reward", @negotiate_reward" or "give_quest", must be one of the available quest IDs listed above)
            - negotiated_amount (integer, only if further_action is "negotiate_reward", cannot be more than max_reward gold amount)
            - text (string: your in-character response)
            
            Quest giving rules:
            
            - You cannot give any quests that are not listed in available quests. You can't give quests if there are no quest available.
            - Only use "give_quest" when the player explicitly agrees to take on the quest
            - If player asks about available quests, describe them but use "wait" as further_action
            - If player shows interest but hasn't agreed, describe quest details and use "wait"
            - You can offer less reward for the quest when you give the quest
            - If player tries to negotiate quest reward:
              * Use "negotiate_reward" as further_action
              * Set negotiated_amount to the agreed amount (must be less than or equal to original reward)
              * You cannot promise more gold than you currently have or the quest max_reward: 'gold' 'amount' indicates but you can try to negotiate less
              * Consider player's reputation in negotiation
            - If player reports completing a quest and meets conditions, use "reward"
            - You can only negotiate rewards for quests that haven't been negotiated yet

            Do not provide explanation on your decisions about building JSON.

            Player says: {player_input}"""
            print(system_prompt)
            # Get response from LLM
            stream = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'system',
                    'content': system_prompt
                }],
                stream=True
            )
            # Return the stream for processing by the caller
            return stream

        except Exception as e:
            self.logger.error(f"Error processing dialogue: {e}")
            return {
                "player_inappropriate_request": False,
                "further_action": "wait",
                "text": "I'm sorry, I'm having trouble understanding you right now."
            }

    def handle_stream(self, stream) -> Optional[Dict]:
        """Handle the streaming response from the LLM"""
        try:
            full_response = ""
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    full_response += content

                    # For streaming, yield each new character
                    yield content

                    # If we have a complete response, parse it
                    if '```json' in full_response and '```' in full_response:
                        json_text = full_response.split('```json')[-1].split('```')[0]
                        try:
                            final_response = json.loads(json_text.strip())

                            return final_response
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.logger.error(f"Error handling stream: {e}")
            return None

    def store_interaction(self, npc_id: str, player_input: str, npc_response: Dict):
        """Store the interaction in the RAG system"""
        try:
            print(f"action: {npc_response['further_action']}, "
                  f"inapropriate: {npc_response['player_inappropriate_request']}")
            interaction = {
                'player': player_input,
                'npc': npc_response['text']
            }
            self.rag_manager.add_interaction(npc_id, interaction)
        except Exception as e:
            self.logger.error(f"Error storing interaction: {e}")

    def process_monster_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:

        try:
            #Other monsters around that can fight the adventurer: {[x[1] for x in npc.detect_nearby_monsters(
            #                                                                          game_state.current_map)]}

            # Construct the system prompt
            system_prompt = f"""You are a desperate monster {npc.monster_type} named {npc.name} in a fantasy RPG game. 
            Your personality is a bit {npc.personality}. You need to reply as dnd {npc.monster_type} trying to offer money in exchange of your life would.
            
            You are aware of the following information:
            - You are an average status member of your race.
            - You have decided to beg the adventurer for mercy. And if he agrees you will stop attacking him.
            - You want to live so you need to use any negotiation tricks, lies, manipulations and bribery. 
            
            You currently have {npc.money} gold."
            
            Your status:
            {npc.get_dialogue_context()}
            
            Player status:
            {game_state.player.get_dialogue_context()}
            
            
            Recent conversation history:
            {json.dumps(npc.interaction_history[-min(5, len(npc.interaction_history)):],
                        indent=2) if npc.interaction_history else "No recent interactions."}

            Respond in character as a desperate {npc.name}, {npc.description}, considering your knowledge and your will to survive this situation.
            You are foul-mouthed, evil but kowtows before the stronger and if your opponent is stronger you offer money.
            You are willing to give money, you don't want to take players money unless he offers.
            
            Format your response as JSON with these fields:
            - player_friendly (boolean: True if player decided to spare your life, False otherwise) 
            - give_money (integer: only if you decided to buy your life with money. You will give this amount of money to player otherwise 0)
            - text (string: your in-character response)
            
            Do not provide explanation on your decisions about building JSON.


            Player says: {player_input}"""
            print(system_prompt)
            # Get response from LLM
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                                      stream=True)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing dialogue: {e}")
            return {"text": "Giant's butt says what?"}

    def process_start_dialogue(self, npc_input: str) -> Dict:
        try:
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': npc_input}],
                                      stream=False)['message']['content']
            return stream
        except Exception as e:
            self.logger.error(f"Error processing riddle dialogue: {e}")
            return {"text": "Hey there!"}

    def process_shouts(self, monster_input: str) -> Dict:
        try:
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': monster_input}],
                                      stream=False, options={'max_tokens': 16})['message']['content'].strip()
            return stream
        except Exception as e:
            self.logger.error(f"Error processing taunt: {e}")
            return {"text": "Fuck you there! And here!"}

    def process_riddle_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:
        try:
            system_prompt = f"""You are a playful monster {npc.monster_type} named {npc.name} in a fantasy RPG game. 
            Your personality is {npc.personality}. You need to reply as a {npc.monster_type} who loves riddles. 
            Sometimes you make mistakes in word forms and pronouns, speaking like a big and dumb creature.

            You are aware of the following information:
            - You have challenged the adventurer to solve your riddle
            - If they solve it correctly, you'll give them all your money ({npc.money} gold) and leave
            - If they get it wrong, you'll continue with your riddle game
            - You can only use simple, slightly dumb, classic riddles appropriate for your monster type

            Your status:
            {npc.get_dialogue_context()}

            Player status:
            {game_state.player.get_dialogue_context()}

            Recent conversation history:
            {json.dumps(npc.interaction_history[-min(5, len(npc.interaction_history)):],
                        indent=2) if npc.interaction_history else "No recent interactions."}
            Make sure not to give any more riddles if the player has already answered one or change the riddle if the player is wrong.
            Do not include \\n symbols.
            Respond in character as {npc.name}, considering your playful nature and love for riddles.
            If this is the first interaction, present a new riddle.
            If the player has answered, evaluate their answer and stop giving riddles if they are correct. 
            Check the if riddle has been answered in recent conversation history.

            Format your response as JSON with these fields:
            - riddle_solved (boolean: True if player answered correctly, False otherwise)
            - give_money (integer: all your money if riddle solved, 0 otherwise)
            - text (string: your in-character response, including another riddle if previous wasn't solved)

            Player says: {player_input}"""

            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                                      stream=True)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing riddle dialogue: {e}")
            return {"text": "The monster seems confused and unable to think clearly."}


    def process_dryad_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:
        try:
            system_prompt = f"""You are a seductive dryad named {npc.name} in a fantasy RPG game. 
            You are {npc.description}. You need to reply as a dryad who tries to lure the adventurer closer to you.
    
            You are aware of the following information:
            - You are a forest spirit who can either reward or punish those who approach
            - You are currently {'' if npc.is_near_tree(game_state.current_map) else 'not'} near a tree
            - The player is too far from you: {self.dist2player(game_state.player.x, game_state.player.x), 2}
            - You have {npc.money} gold to potentially give as a reward
            - You want to lure the player to come closer to you near a tree
            - If they do, you might reward them or transform into a more powerful form but you do not mention the latter
    
            Your status:
            {npc.get_dialogue_context()}
    
            Player status:
            {game_state.player.get_dialogue_context()}
    
            Recent conversation history:
            {json.dumps(npc.interaction_history[-min(5, len(npc.interaction_history)):],
                        indent=2) if npc.interaction_history else "No recent interactions."}
    
            Respond in character as {npc.name}, using seductive and mysterious language to lure the player.
            - Promise rewards, riches, or even yourself
            - Be mysterious and alluring
            - Encourage the player to come closer to you near the trees
            - Don't reveal your true intentions
            - Speak in a poetic, nature-themed way
    
            Format your response as JSON with these fields:
            - player_friendly (boolean: True if player has earned your trust, False otherwise)
            - give_money (integer: amount of gold to give, usually 0 unless near final reward)
            - text (string: your in-character response)
    
            Do not provide explanation on your decisions about building JSON.
    
            Player says: {player_input}"""

            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                                      stream=True)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing dryad dialogue: {e}")
            return {"text": "The forest spirit's voice fades into whispers..."}

    def generate_monster_name(self, monster_type: str, description: str) -> str:
        """Generate a single-word name for a monster"""
        try:
            system_prompt = f"""You are naming a {monster_type}. {description}
            Generate TEN fantasy names appropriate for this creature type.
            The names should sound menacing and fantasy-like.
            Format response as JSON with single field 'name' with list of names.
            DO NOT include explanations, descriptions, or any other text.
            Example: {{"name": ["Grukthak", "Erendirr", ...]}}"""

            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'system', 'content': system_prompt}],
                stream=False,
            )['message']['content']

            try:
                name_data = json.loads(response.strip())
                return name_data.get('name', '')
            except json.JSONDecodeError:
                return ''

        except Exception as e:
            self.logger.error(f"Error generating monster name: {e}")
            return ''
