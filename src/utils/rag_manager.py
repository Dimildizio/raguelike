import faiss
import numpy as np
import os
import json
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
from collections import defaultdict
from data.initial_knowledge import INITIAL_KNOWLEDGE
import logging

class RAGManager:
    def __init__(self, base_path=None):

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            self.logger.error(f"Failed to initialize SentenceTransformer: {e}")
            raise
        self.embedding_dim = 384
        # Get the project root directory
        if base_path is None:
            # Get the directory where the script is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up two levels (from utils/ to project root)
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

        # Setup data directories
        self.data_dir = os.path.join(base_path, "data", "knowledge_base")
        self.index_dir = os.path.join(self.data_dir, "indices")
        self.text_dir = os.path.join(self.data_dir, "texts")

        # Create directories if they don't exist
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.text_dir, exist_ok=True)

        # Initialize indices and texts
        self.indices = {}
        self.texts = defaultdict(list)

        # Load or initialize knowledge base
        self.load_or_initialize_knowledge()


    def _knowledge_exists(self):
        """Check if knowledge base files exist"""
        world_index_path = os.path.join(self.index_dir, "world.index")
        world_text_path = os.path.join(self.text_dir, "world.json")
        return os.path.exists(world_index_path) and os.path.exists(world_text_path)

    def load_or_initialize_knowledge(self):
        """Load existing knowledge base or initialize a new one"""
        if self._knowledge_exists():
            self.load_knowledge()
        else:
            self.initialize_knowledge()

    def save_knowledge(self):
        """Save all indices and texts to disk"""
        # Save indices
        for name, index in self.indices.items():
            index_path = os.path.join(self.index_dir, f"{name}.index")
            faiss.write_index(index, index_path)

        # Save texts
        for name, texts_list in self.texts.items():
            text_path = os.path.join(self.text_dir, f"{name}.json")
            with open(text_path, 'w', encoding='utf-8') as f:
                json.dump(texts_list, f, ensure_ascii=False, indent=2)

    def load_knowledge(self):
        """Load indices and texts from disk"""
        # Load all .index files
        for filename in os.listdir(self.index_dir):
            if filename.endswith('.index'):
                name = filename[:-6]  # Remove .index
                index_path = os.path.join(self.index_dir, filename)
                self.indices[name] = faiss.read_index(index_path)

        # Load all .json files
        for filename in os.listdir(self.text_dir):
            if filename.endswith('.json'):
                name = filename[:-5]  # Remove .json
                text_path = os.path.join(self.text_dir, filename)
                with open(text_path, 'r', encoding='utf-8') as f:
                    self.texts[name] = json.load(f)

    def add_texts(self, index_name: str, texts: List[str]):
        """Add new texts to an index and save"""
        embeddings = self.encoder.encode(texts)
        self.indices[index_name].add(np.array(embeddings).astype('float32'))
        self.texts[index_name].extend(texts)
        self.save_knowledge()  # Save after each update

    def initialize_knowledge(self):
        """Initialize new knowledge base with default data"""
        # Initialize empty indices for knowledge
        self.indices = {
            'world': faiss.IndexFlatL2(self.embedding_dim),
            'merchant_tom': faiss.IndexFlatL2(self.embedding_dim),
            'villager_amelia': faiss.IndexFlatL2(self.embedding_dim)
        }

        # Initialize separate indices for dialogue history
        self.dialogue_indices = {
            'merchant_tom': faiss.IndexFlatL2(self.embedding_dim),
            'villager_amelia': faiss.IndexFlatL2(self.embedding_dim)
        }

        # Add initial knowledge from imported data
        for index_name, texts in INITIAL_KNOWLEDGE.items():
            self.add_texts(index_name, texts)

        # Save the initial knowledge base
        self.save_knowledge()

    def add_interaction(self, npc_id: str, interaction: Dict):
        """Add new interaction to separate dialogue index"""
        interaction_text = f"Player said: {interaction['player']} | Response was: {interaction['npc']}"
        embeddings = self.encoder.encode([interaction_text])
        self.dialogue_indices[npc_id].add(np.array(embeddings).astype('float32'))
        self.texts[f"{npc_id}_dialogues"].append(interaction_text)
        self.save_knowledge()

    def query(self, npc_id: str, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Query both world knowledge and NPC-specific knowledge"""
        try:
            query_embedding = self.encoder.encode([query])
            query_vector = np.array(query_embedding).astype('float32')

            # Search in knowledge indices
            world_distances, world_indices = self.indices['world'].search(query_vector, k)
            npc_distances, npc_indices = self.indices[npc_id].search(query_vector, k)

            results = []
            # Add world knowledge results
            for i, idx in enumerate(world_indices[0]):
                if idx < len(self.texts['world']):
                    results.append((self.texts['world'][idx], world_distances[0][i], 'world'))

            # Add NPC-specific knowledge results
            for i, idx in enumerate(npc_indices[0]):
                if idx < len(self.texts[npc_id]):
                    results.append((self.texts[npc_id][idx], npc_distances[0][i], 'npc'))

            return results
        except Exception as e:
            self.logger.error(f"Error during query: {e}")
            return []

    def query_dialogue_history(self, npc_id: str, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Query only dialogue history"""
        try:
            dialogue_texts = self.texts.get(f"{npc_id}_dialogues", [])

            if not dialogue_texts:
                return []
            k = min(k, len(dialogue_texts))
            if npc_id not in self.dialogue_indices:
                self.dialogue_indices[npc_id] = faiss.IndexFlatL2(self.embedding_dim)
                return []

            query_embedding = self.encoder.encode([query])
            query_vector = np.array(query_embedding).astype('float32')

            # Search only in dialogue index
            distances, indices = self.dialogue_indices[npc_id].search(query_vector, k)

            results = []
            for i, idx in enumerate(indices[0]):
                dialogue_texts = self.texts.get(f"{npc_id}_dialogues", [])
                if idx < len(dialogue_texts):
                    results.append((dialogue_texts[idx], distances[0][i]))

            return results
        except Exception as e:
            self.logger.error(f"Error during dialogue history query: {e}")
            return []

    def clear_knowledge_base(self):
        """Clear and reinitialize the knowledge base"""
        try:
            self.logger.info("Clearing knowledge base...")

            # Remove all existing index and text files
            for filename in os.listdir(self.index_dir):
                file_path = os.path.join(self.index_dir, filename)
                os.remove(file_path)

            for filename in os.listdir(self.text_dir):
                file_path = os.path.join(self.text_dir, filename)
                os.remove(file_path)

            # Reset in-memory data
            self.indices = {}
            self.texts = defaultdict(list)

            # Reinitialize with fresh data
            self.initialize_knowledge()
            self.logger.info("Knowledge base reinitialized successfully")
        except Exception as e:
            self.logger.error(f"Error clearing knowledge base: {e}")
            raise