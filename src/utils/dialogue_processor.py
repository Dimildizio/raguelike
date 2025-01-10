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
                         npc_name: str,
                         npc_mood: str,
                         player_reputation: int,
                         game_state: Any,
                         interaction_history: list = []) -> Dict:

        # Convert NPC name to id format
        npc_id = npc_name.lower().replace(' ', '_')

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

                    prefix = "General knowledge: " if source == 'world' else f"{npc_name}'s knowledge: "
                    context_from_rag += f"{prefix}{info}\n"

            quest_info = game_state.quest_manager.format_quest_status(npc_id)

            # Construct the system prompt
            system_prompt = f"""You are an NPC named {npc_name} in a fantasy RPG game. 
            Your current mood is {npc_mood}.
            The player's reputation with you is {player_reputation}/100.

            You are aware of the following information:
            {context_from_rag}

            {quest_info}

            Recent conversation history:
            {json.dumps(interaction_history[-min(5, len(interaction_history)):], 
                        indent=2) if interaction_history else "No recent interactions."}
            
            Relevant dialogues with player:
            {relevant_dialogues}
            
            Respond in character as {npc_name}, considering your mood, the player's reputation, and your knowledge.
                    
            Format your response as JSON with these fields:
            - player_inappropriate_request (boolean)
            - further_action (string: "give_quest", "reward", "stop", or "wait")
            - quest_id (string, only if further_action is "give_quest", must be one of the available quest IDs listed above)
            - text (string: your in-character response)
            
            Quest giving rules:
            - You cannot give any quests that are not listed in avaliable quests. You can't give anything if no quest available.
            - Only use "give_quest" as further_action when the player explicitly agrees to take on the quest only after clear player acceptance like "I'll do it", "I accept", etc.
            - If player just asks about available quests, describe them but use "wait" as further_action
            - If player shows interest but hasn't explicitly agreed, describe quest details, reward itself, but use "wait"
            - If the player reports completing a quest and meets conditions, use "reward" as further_action.

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
