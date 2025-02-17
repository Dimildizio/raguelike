import ollama
import json
from typing import Dict, Optional, Any
import logging
from .rag_manager import RAGManager
from systems.monsters_decisions import MonsterDecisionMaker
from constants import replacer



class DialogueProcessor:
    def __init__(self, host="http://localhost:11434", model="gemma2:2b"):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        try:
            self.client = ollama.Client(host=host)
            self.model = model
            self.rag_manager = RAGManager()
            self.decision_maker = MonsterDecisionMaker(self)
        except Exception as e:
            self.logger.error(f"Failed to initialize DialogueProcessor: {e}")
            raise

    def _get_relevant_knowledge(self, entity_id: str, current_input: str,
                                interaction_history: list = None, k: int = 5) -> str:
        """Get formatted relevant knowledge for an entity"""
        try:
            # Create combined query from history and current input
            combined_query = current_input
            if interaction_history:
                last_interaction = interaction_history[-1]
                # Handle both NPC and monster interactions
                npc_response = last_interaction.get('npc', last_interaction.get('monster', ''))
                combined_query = f"{last_interaction['player']} {npc_response} {current_input}"

            # Query the knowledge base
            relevant_info = self.rag_manager.query(entity_id, combined_query, k=k)

            # Format the knowledge with proper prefixes
            context_from_rag = "\nRelevant information:\n"
            for info, score, source in relevant_info:
                #print(info, score, source)
                if score < 100:  # Only include relevant matches
                    # Debug information
                    self.logger.debug(f"\nSource: {source}")
                    self.logger.debug(f"Similarity Score: {score}")
                    self.logger.debug(f"Content: {info[:200]}...")  # Preview

                    # Format based on source type
                    prefix = self._get_knowledge_prefix(source, entity_id)
                    context_from_rag += f"{prefix}{info}\n"

            return context_from_rag

        except Exception as e:
            self.logger.error(f"Error getting relevant knowledge: {e}")
            return "\nNo relevant information available.\n"

    def _get_knowledge_prefix(self, source: str, entity_id: str) -> str:
        """Get appropriate prefix for knowledge source"""
        if source == 'world':
            return "General knowledge: "
        elif source == 'monster_base':
            return "Monster knowledge: "
        else:
            # Get entity name from id (handle both NPCs and monsters)
            entity_name = entity_id.split('_')[1] if '_' in entity_id else entity_id
            return f"{entity_name}'s knowledge: "

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
            context_from_rag = self._get_relevant_knowledge(npc_id, player_input, interaction_history)

            # Get quest information
            quest_info = game_state.quest_manager.format_quest_status(npc_id)
            active_quests = [
                quest for quest in game_state.quest_manager.get_active_quests()
                if quest.giver_npc == npc_id
            ]
            current_quest_context = ""
            if active_quests:
                quest = active_quests[0]  # Assuming one active quest per NPC for now
                current_quest_context = f"\nCurrent active quest ID: {quest.quest_id}"

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
            
            
            Respond in character as {npc.name}, {npc.description}, considering your mood, the player's reputation, and your knowledge.
            Try to include proper from mentioned above list of quest_id if the topic is related to the quest.
            Format your response as JSON with these fields:
            - player_inappropriate_request (boolean)
            - further_action (string: "give_quest", "reward", "stop", "negotiate_reward", or "wait")
            - quest_id (string, if further_action is "reward" or "negotiate_reward" or "give_quest", must be one of the available quest IDs listed above)
            - negotiated_amount (integer, only if further_action is "negotiate_reward", cannot be more than max_reward gold amount)
            - text (string: your in-character response)
            
            Quest giving rules:
            
            - You cannot give any quests that are not listed in available quests. You can't give quests if there are no quest available.
            - Only use "give_quest" when the player explicitly agrees to take on the quest
            - If player asks about available quests, describe them but use "wait" as further_action
            - If player shows interest but hasn't agreed, describe quest details and use "wait"
            - You can offer less reward for the quest when you give the quest
            - If player tries to negotiate quest reward:
              * Use "negotiate_reward" as further_action but don't forget to indicate "quest_id"
              * Set negotiated_amount to the agreed amount (must be less than or equal to original reward) and state "quest_id"
              * You cannot promise more gold than you currently have or the quest max_reward: 'gold' 'amount' indicates but you can try to negotiate less
              * Consider player's reputation in negotiation
            - If player reports completing a quest and meets conditions, use "reward" and related "quest_id"
            - You can only negotiate rewards for quests that haven't been negotiated yet
            - If player talks about the reward - try to assign related to te topic "quest_id"

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

    def process_shouts(self, monster_input: str) -> Dict:
        try:
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': monster_input}],
                                      stream=False, options={'max_tokens': 16})['message']['content'].strip()
            return stream
        except Exception as e:
            self.logger.error(f"Error processing taunt: {e}")
            return {"text": "Fuck you there! And here!"}

    def process_monster_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:
        print('processing dialogue', npc.monster_type)
        try:
            context_from_rag = self._get_relevant_knowledge(npc.entity_id, player_input, npc.interaction_history)

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
            
            Your nearby allies:
            {npc.detect_nearby_monsters(npc.game_state.current_map)}
            
            Other relevant information including your knowledge and memories:
            {context_from_rag}
            
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


    def process_riddle_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:
        try:
            context_from_rag = self._get_relevant_knowledge(npc.entity_id, player_input, npc.interaction_history)

            system_prompt = f"""You are a playful monster {npc.monster_type} named {npc.name} in a fantasy RPG game. 
            Your personality is {npc.personality}. You need to reply as a {npc.monster_type} who loves riddles. 
            Sometimes you make mistakes in word forms and pronouns, speaking like a big and dumb creature.

            You are aware of the following information:
            - {context_from_rag}
            - You have challenged the adventurer to solve your riddle
            - If they solve it correctly, you'll give them all your money ({npc.money} gold) and leave
            - If they get it wrong, you'll continue with your riddle game
            - You can only use simple, slightly dumb, classic riddles appropriate for your monster type

            Your status:
            {npc.get_dialogue_context()}

            Player status:
            {game_state.player.get_dialogue_context()}
            
            Your nearby allies:
            {npc.detect_nearby_monsters(npc.game_state.current_map)}

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
            print(system_prompt)
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                                      stream=True)
            print(stream)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing riddle dialogue: {e}")
            return {"text": "The monster seems confused and unable to think clearly."}


    def process_dryad_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:
        try:
            context_from_rag = self._get_relevant_knowledge(npc.entity_id, player_input, npc.interaction_history)

            system_prompt = f"""You are a seductive dryad named {npc.name} in a fantasy RPG game. 
            You are {npc.description}. You need to reply as a dryad who tries to lure the adventurer closer to you.
    
            You are aware of the following information:
            - {context_from_rag}
            - You are a forest spirit who can either reward or punish those who approach
            - You are currently {'' if npc.is_near_tree(game_state.current_map) else 'not'} near a tree
            - The player is too far from you: {npc.dist2player((game_state.player.x, game_state.player.x), 2)}
            - You have {npc.money} gold to potentially give as a reward
            - You want to lure the player to come closer to you near a tree
            - If they do, you might reward them or transform into a more powerful form but you do not mention the latter
    
            Your status:
            {npc.get_dialogue_context()}
    
            Player status:
            {game_state.player.get_dialogue_context()}
    
            Your nearby allies:
            {npc.detect_nearby_monsters(npc.game_state.current_map)}
            
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
            print(system_prompt)
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                                      stream=True)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing dryad dialogue: {e}")
            return {"text": "The forest spirit's voice fades into whispers..."}


    def process_kobold_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:
        # Unfortunately gemma doesn't support tool use
        try:
            context_from_rag = self._get_relevant_knowledge(npc.entity_id, player_input, npc.interaction_history)

            if not npc.has_passed_test:
                system_prompt = f"""You are a kobold English teacher named {npc.name} in a fantasy RPG game and the player
                    has been a lazy and annoying student. 
                    Your personality is strict but fair. You need to reply as a kobold who tests adventurers' English.
        
                    You are aware of the following information:
                    - {context_from_rag}
                    - You are a small reptilian creature who loves teaching English 
                    - You have {npc.money} gold
                    - You have already tested the player: {npc.has_passed_test}
                    - If player hasn't passed test yet, you must give them a simple A2 level English test
                    - If they answer incorrectly or say goodbye before passing, you hurt them
                    - If they answer incorrectly you say the correct answer but give them another test
                    - Once they answer correctly once, you become friendly and stop testing them
        
                    Recent conversation history:
                    {json.dumps(npc.interaction_history[-min(5, len(npc.interaction_history)):],
                                indent=2) if npc.interaction_history else "No recent interactions."}
                    Make sure you do NOT use the same tasks or words for the task as you used in your interaction history
        
                    Example test questions (use similar format and difficulty but every time it should be different question):
                    You can give player an example of a sentence where he need to put the correct past form or third person in present simple.
                    You can give a sentence where player needs to say if there should be present simple or present continuous.
                    You can give a task to complete the phrase with a correct form of a verb.
                    You are free to give any other kinds of tasks. 
                    
                    If you are not sure the player is correct - check if the word you wanted him to use is in his reply. If yes - the answer is correct.
            
                    Players questions may vary or contain other information besides the answer, you need to figure out if there is a correct answer in players reply.
                    If the player answers in one word and that word is a correct form of your given example - count that as a correct answer.
                    Format your response as JSON with these fields:
                    - correctly_answered (bool: True if player's answer was correct otherwise False)
                    - text (string: your in-character response, including the test question if not friendly)
        
                    Player says: The correct answer is - {player_input}"""
            else:
                system_prompt = f"""
                    You are a kobold English teacher named {npc.name} in a fantasy RPG game and the player
                    has been a lazy and annoying student but he gave a correct answer recently so you are happy about it.
        
                    - You are a small reptilian creature who loves teaching English 
                    - You have {npc.money} gold
                    - You have already tested the player: {npc.has_passed_test}
                    - Once they answer correctly once, you become friendly and stop testing them
                    - {context_from_rag}
        
                    Recent conversation history:
                    {json.dumps(npc.interaction_history[-min(5, len(npc.interaction_history)):],
                                indent=2) if npc.interaction_history else "No recent interactions."}
                    Since the player has already answered you are here just for a little talk.
                    Do not provide explanation on your decisions about building JSON.
            
                    Format your response as JSON with these fields:
                    - text (string: your in-character response)
        
                    Player says: {player_input}
                """
            print(system_prompt)
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                                      stream=True)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing kobold dialogue: {e}")
            return {"text": "The kobold adjusts its tiny glasses nervously..."}


    def process_demon_bard_dialogue(self, player_input: str, npc: Any, game_state: Any) -> Dict:
        try:
            context_from_rag = self._get_relevant_knowledge(npc.entity_id, player_input, npc.interaction_history)

            if not npc.has_passed_test:
                player_word, demon_word = '', ''
                if npc.interaction_history:
                    player_word = replacer(npc.interaction_history[-1]['player'].strip().split()[-1])
                    demon_word = replacer(npc.interaction_history[-1]['monster'].strip().split()[-1])
                    print(player_word, '==', demon_word)

                system_prompt = f"""You are a tragic poet bard from hell named {npc.name} in a fantasy RPG game. 
                Your personality is melancholic and overdramatic. You test adventurers with rhymes.

                    
                Your nearby allies:
                {npc.detect_nearby_monsters(npc.game_state.current_map)}

                You are aware of the following information:
                - {context_from_rag}
                - You are a damned poet who must make others appreciate poetry
                - You have {npc.money} gold
                - You have already tested the player: {npc.has_passed_test}
                - You always answer in three lines
                - Player must complete the verse after your third line with a fourth line that rhymes
                - If they fail to rhyme or say goodbye before passing, you hurt them
                - Once they create a good rhyme once, you become friendly
                - You are not strict - is the last word of the answer rhymes with the last word of yours - that is good enough as well
                - You never repeat your line from previous interaction and recent conversations
                
                Recent conversation history:
                {json.dumps(npc.interaction_history[-min(5, len(npc.interaction_history)):],
                            indent=2) if npc.interaction_history else "No recent interactions."}
                
                Do not repeat yourself and you cannot say more than three lines
                
                Rules for evaluating player's rhyme:
                1. The last word of player's line should rhyme with your last line's word
                2. Be somewhat lenient - if it's close to rhyming, accept it
                3. The line doesn't need to be perfect poetry
                4. make sure to evaluate as a correct answer the last word of your last line - ({demon_word}) rhymes with players last word - ({player_word})
            
                Format your response as JSON with these fields:
                - correctly_answered (boolean: True if player's word rhymes with your last line's word)
                - text (string: your in-character three lines of verse, only if starting new verse on a current topic)

                Player says: {player_input}"""

            else:
                system_prompt = f"""You are a tragic poet bard from hell named {npc.name} who has found a kindred spirit.
                The player has proven their worth with rhyme. You keep talking to the player in rhymes. 
                You also know {context_from_rag}
                Recent conversation history:
                {json.dumps(npc.interaction_history[-min(5, len(npc.interaction_history)):],
                            indent=2) if npc.interaction_history else "No recent interactions."}
                                
                Do not provide explanation on your decisions about building JSON.
                Format your response as JSON with these fields:
                - text (string: your friendly, poetic response)

                Player says: {player_input}"""
            print(system_prompt)
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                                      stream=True)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing hell bard dialogue: {e}")
            return {"text": "The bard strums a discordant note..."}


    def process_willow_whisper_dialogue(self, player_input: str, npc, game_state) -> Dict:
        try:
            story = npc.death_story
            discovered_new = npc.check_truth_discovery(player_input)

            if not npc.has_found_truth:
                system_prompt = f"""You are the spirit of {story['victim_name']}, who died under tragic circumstances.
                You are trying to find peace by having someone understand your death.

                Your death story:
                - Location: {story['location']}
                - Cause: {story['cause']}
                - Key details: {', '.join(story['key_details'])}
                - Perpetrator: {story['perpetrator']}
                - Your story: {story['text']}

                Currently discovered clues: {list(npc.discovered_clues)}
                Still hidden clues: {set(story['key_details']) - npc.discovered_clues}

                Interaction rules:
                - Answer questions about your death in metaphor
                - Explicitly say that you want an answer to how you died
                - If players message is unrelated to your story (like hello or what do you want) - tell that the player needs to solve your mistery
                - If player guesses something correctly, acknowledge it
                - Do not directly say undiscovered key details let player derive them from your answers
                - If all truths are discovered, express gratitude and peace

                Recent conversation history:
                {json.dumps(npc.interaction_history[-3:], indent=2) if npc.interaction_history else "No recent interactions."}
                
                Do not provide explanation on your decisions about building JSON.
                Format your response as JSON with these fields:
                - correctly_answered (boolean: if you think the player has at least vaguely discovered the story of your death)
                - key_details (list: list of important single word clues taken from the player's answer)
                - text (string: your ghostly response)

                Player says: {player_input}"""
            else:
                system_prompt = f"""You are the spirit of {story['victim_name']}, now at peace.
                Express gratitude and share your story summary {story['text']}  before departing.
                
                Do not provide explanation on your decisions about building JSON.
                Format your response as JSON with these fields:
                - text (string: your gratitude, story summary and farewell)

                Player says: {player_input}"""
            print(system_prompt)
            stream = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                     stream=True)
            return stream

        except Exception as e:
            self.logger.error(f"Error processing will'o'whisper dialogue: {e}")
            return {"text": "The spirit flickers dimly..."}


    def generate_death_story(self):
        """Generate a unique death story for this spirit using LLM"""
        fallback = {"victim_name": "Unknown Soul",
                    "location": "the old crossroads",
                    "cause": "mysterious circumstances",
                    "key_details": ["alone", "cold", "betrayed", "crossroad", "beloved"],
                    "perpetrator": "your beloved Geoffrey",
                    "text": "You were betrayed at the crossroad by your beloved one who left you to die cold and alone"}
        try:
            system_prompt = """Create a tragic death story for a ghost character in a fantasy RPG so the player could ask it questions about it.
            The story should:
            - Include specific details about time, place, and circumstances
            - Have five to eight simple key elements that need to be discovered
            - Be solvable through asking questions
            - Include a motive or perpetrator if murder
            
            IMPORTANT: key_details must be SINGLE WORDS that are crucial to the story.
                                
            Do not provide explanation on your decisions about building JSON.
            Format the response as JSON with these fields:
            - victim_name (string: the ghost's original name)
            - location (string: where they died)
            - cause (string: how they died)
            - key_details (array: list of from five to eight SINGLE-WORD crucial facts about the death)
            - perpetrator (string: who caused the death, if any)
            - text (string: summary of your story)
            """

            response = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}])
            content = response['message']['content'].replace('```json', '').replace('```', '')
            print('response', content)
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx + 1]

            try:
                story = json.loads(content)
                print(story)
            except json.JSONDecodeError:
                print('json error')
                return fallback
            return story

        except Exception as e:
            print(f"Error generating death story: {e}")
            return fallback

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

    def get_summary(self, npc):
        """Generate a summary"""
        if hasattr(npc, 'interaction_history') and npc.interaction_history and len(npc.interaction_history) > 1:
            try:
                # Generate summary using LLM
                system_prompt = f"""Summarize this conversation between {npc.monster_type} {npc.name} and the player in 1-2 sentences.
                Focus on the key points, decisions, or agreements made.
    
                Recent conversation:
                {json.dumps(npc.interaction_history, indent=2)}
    
                Format response as a single string without any JSON special formatting nor explanations."""

                response = self.client.chat(model=self.model, messages=[{'role': 'system', 'content': system_prompt}],
                    stream=False)
                if response and 'message' in response and 'content' in response['message']:
                    summary = response['message']['content'].strip()
                    print(summary)
                    return summary
                    # Add summary to game messages
            except Exception as e:
                print(f"Error generating conversation summary: {e}")

    def evaluate_intimidation(self, text: str) -> int:
        try:
            system_prompt = f"""You are an expert in evaluating intimidating phrases in a fantasy RPG setting.
            Rate the following phrase on a scale from 0 to 10, where:
            0 = not intimidating at all, casual phrase
            5 = common threats like "I'll kill you" or basic profanity like "Fuck you"
            10 = extremely creative and terrifying intimidation that would strike fear into enemies

            Rules:
            - Consider creativity, psychological impact, and delivery
            - Generic threats should score low (4-6)
            - High scores (7-10) require unique, creative, or particularly menacing content
            - Short intimidation is better
            - Fantasy/magical references can enhance score if used creatively

            Format response as JSON with single field:
            - intimidation_level (integer between 1 and 10)
            DO NOT include explanations, descriptions, or any other text.

            
            Phrase to evaluate: {text}"""

            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'system', 'content': system_prompt}]
            )

            content = response['message']['content']
            print(content)
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx + 1]
            result = json.loads(content)
            return int(result.get('intimidation_level', 0))
        except Exception as e:
            print(f"Error evaluating intimidation: {e}")
            return 0
