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
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Knowledge type constants
        self.KNOWLEDGE_TYPES = {
            'WORLD': "world",
            'NPC': "npc",
            'MONSTER': "monster",
            'MONSTER_BASE': "monster_base",
            'PERMANENT': ['world', 'monster_base', 'npc']  # Knowledge types that shouldn't be cleared
        }

        # Initialize encoder
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384
        except Exception as e:
            self.logger.error(f"Failed to initialize SentenceTransformer: {e}")
            raise

        # Setup paths
        if base_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

        self.data_dir = os.path.join(base_path, "data", "knowledge_base")
        self.index_dir = os.path.join(self.data_dir, "indices")
        self.text_dir = os.path.join(self.data_dir, "texts")

        # Create directories if they don't exist
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.text_dir, exist_ok=True)

        # Initialize storage
        self.indices = {}  # FAISS indices
        self.texts = defaultdict(list)  # Text storage
        self.entity_types = {}  # Track entity types

        # Load or initialize knowledge base
        self.load_or_initialize_knowledge()

    def _knowledge_exists(self) -> bool:
        """Check if knowledge base files exist and are valid"""
        try:
            world_index = os.path.join(self.index_dir, f"{self.KNOWLEDGE_TYPES['WORLD']}.index")
            world_text = os.path.join(self.text_dir, f"{self.KNOWLEDGE_TYPES['WORLD']}.json")

            if not (os.path.exists(world_index) and os.path.exists(world_text)):
                return False

            # Verify world.json format
            with open(world_text, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not (isinstance(data, dict) and "texts" in data and "type" in data):
                    return False

            return True
        except Exception:
            return False

    def _cleanup_knowledge_base(self):
        """Clean up corrupted knowledge base files"""
        try:
            self.logger.info("Cleaning up knowledge base...")
            # Remove all files in index directory
            for filename in os.listdir(self.index_dir):
                file_path = os.path.join(self.index_dir, filename)
                os.remove(file_path)

            # Remove all files in text directory
            for filename in os.listdir(self.text_dir):
                file_path = os.path.join(self.text_dir, filename)
                os.remove(file_path)

            self.logger.info("Knowledge base cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up knowledge base: {e}")

    def load_or_initialize_knowledge(self):
        """Load existing knowledge base or initialize a new one"""
        if self._knowledge_exists():
            try:
                self.load_knowledge()
            except Exception as e:
                self.logger.error(f"Error loading knowledge base: {e}")
                self._cleanup_knowledge_base()
                self.initialize_knowledge()
        else:
            self._cleanup_knowledge_base()
            self.initialize_knowledge()

    def _create_entity_index(self, entity_id: str, entity_type: str):
        """Create a new index for an entity"""
        if entity_id not in self.indices:
            if entity_type not in self.KNOWLEDGE_TYPES.values():
                self.logger.warning(f"Creating index with unknown entity type: {entity_type}")

            self.indices[entity_id] = faiss.IndexFlatL2(self.embedding_dim)
            self.texts[entity_id] = []
            self.entity_types[entity_id] = entity_type
            self.logger.info(f"Created new index for {entity_type}: {entity_id}")

    def add_texts(self, entity_id: str, texts: List[str]):
        """Add new texts to an entity's knowledge"""
        if not texts:
            return

        try:
            embeddings = self.encoder.encode(texts)
            self.indices[entity_id].add(np.array(embeddings).astype('float32'))
            self.texts[entity_id].extend(texts)
        except Exception as e:
            self.logger.error(f"Error adding texts for {entity_id}: {e}")
            raise

    def add_interaction(self, entity_id: str, interaction: Dict):
        """Store dialogue interaction"""
        try:
            if entity_id not in self.indices:
                entity_type = (
                    self.KNOWLEDGE_TYPES['MONSTER']
                    if "monster" in entity_id
                    else self.KNOWLEDGE_TYPES['NPC']
                )
                self._create_entity_index(entity_id, entity_type)

            interaction_text = (
                f"Player said: {interaction.get('player', '')} | "
                f"{'Monster' if self.entity_types[entity_id] == self.KNOWLEDGE_TYPES['MONSTER'] else 'NPC'} "
                f"responded: {interaction.get('monster' if 'monster' in interaction else 'npc', '')}"
            )

            embeddings = self.encoder.encode([interaction_text])
            self.indices[entity_id].add(np.array(embeddings).astype('float32'))
            self.texts[entity_id].append(interaction_text)
            self.save_knowledge()

        except Exception as e:
            self.logger.error(f"Error adding interaction for {entity_id}: {e}")

    def query(self, entity_id: str, query: str, k: int = 5) -> List[Tuple[str, float, str]]:
        """Query knowledge base"""
        try:
            self.logger.info(f"Querying RAG for entity {entity_id} with: {query[:50]}...")
            query_embedding = self.encoder.encode([query])
            query_vector = np.array(query_embedding).astype('float32')
            results = []

            # World knowledge
            if self.KNOWLEDGE_TYPES['WORLD'] in self.indices:
                world_distances, world_indices = self.indices[self.KNOWLEDGE_TYPES['WORLD']].search(query_vector, k)
                for i, idx in enumerate(world_indices[0]):
                    if idx < len(self.texts[self.KNOWLEDGE_TYPES['WORLD']]):
                        results.append((
                            self.texts[self.KNOWLEDGE_TYPES['WORLD']][idx],
                            float(world_distances[0][i]),
                            "world"
                        ))

            # Monster base knowledge for monsters
            entity_type = self.entity_types.get(entity_id)
            if entity_type == self.KNOWLEDGE_TYPES['MONSTER']:
                if self.KNOWLEDGE_TYPES['MONSTER_BASE'] in self.indices:
                    base_distances, base_indices = self.indices[self.KNOWLEDGE_TYPES['MONSTER_BASE']].search(
                        query_vector, k)
                    for i, idx in enumerate(base_indices[0]):
                        if idx < len(self.texts[self.KNOWLEDGE_TYPES['MONSTER_BASE']]):
                            results.append((
                                self.texts[self.KNOWLEDGE_TYPES['MONSTER_BASE']][idx],
                                float(base_distances[0][i]),
                                "monster_base"
                            ))

            # Entity-specific knowledge
            if entity_id in self.indices:
                distances, indices = self.indices[entity_id].search(query_vector, k)
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.texts[entity_id]):
                        results.append((
                            self.texts[entity_id][idx],
                            float(distances[0][i]),
                            entity_id
                        ))

            self.logger.info(f"Found {len(results)} relevant pieces of knowledge")
            return sorted(results, key=lambda x: x[1])

        except Exception as e:
            self.logger.error(f"Error during query: {e}")
            return []

    def save_knowledge(self):
        """Save knowledge base to disk"""
        try:
            for entity_id, index in self.indices.items():
                # Save FAISS index
                index_path = os.path.join(self.index_dir, f"{entity_id}.index")
                faiss.write_index(index, index_path)

                # Save texts and metadata
                text_path = os.path.join(self.text_dir, f"{entity_id}.json")
                data = {
                    "type": self.entity_types.get(entity_id, "unknown"),
                    "texts": self.texts[entity_id]
                }
                with open(text_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self.logger.info(f"Saved knowledge for {entity_id}")
        except Exception as e:
            self.logger.error(f"Error saving knowledge base: {e}")
            raise

    def load_knowledge(self):
        """Load knowledge base from disk"""
        try:
            # First load all text data to get entity types
            for filename in os.listdir(self.text_dir):
                if filename.endswith('.json'):
                    entity_id = filename[:-5]  # Remove .json
                    text_path = os.path.join(self.text_dir, filename)
                    try:
                        with open(text_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.logger.info(f"Loading {text_path}, content: {data}")  # Debug log
                            if isinstance(data, dict) and "texts" in data and "type" in data:
                                self.texts[entity_id] = data["texts"]
                                self.entity_types[entity_id] = data["type"]
                            else:
                                self.logger.error(
                                    f"Invalid data format in {text_path}. Expected dict with 'texts' and 'type', got: {data}")
                                # Initialize with correct format
                                self.initialize_knowledge()
                                return
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON decode error in {text_path}: {e}")
                        # Initialize with correct format
                        self.initialize_knowledge()
                        return

            # Then load FAISS indices
            for filename in os.listdir(self.index_dir):
                if filename.endswith('.index'):
                    entity_id = filename[:-6]  # Remove .index
                    if entity_id in self.texts:
                        index_path = os.path.join(self.index_dir, filename)
                        self.indices[entity_id] = faiss.read_index(index_path)
                        self.logger.info(f"Loaded index for {entity_id}")

            self.logger.info(f"Loaded knowledge base with {len(self.indices)} entities")
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
            self.initialize_knowledge()

    def initialize_knowledge(self):
        """Initialize knowledge base with initial data"""
        try:
            self.logger.info("Initializing new knowledge base...")

            # Clear existing data
            self.indices = {}
            self.texts = defaultdict(list)
            self.entity_types = {}

            # Initialize all knowledge from initial data
            for entity_id, data in INITIAL_KNOWLEDGE.items():
                if isinstance(data, dict) and "type" in data and "texts" in data:
                    entity_type = data["type"]
                    texts = data["texts"]
                    self._create_entity_index(entity_id, entity_type)
                    self.add_texts(entity_id, texts)
                    self.logger.info(f"Initialized {entity_type} knowledge for {entity_id}")

            # Save the newly initialized knowledge
            self.save_knowledge()
            self.logger.info("Knowledge base initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing knowledge base: {e}")
            raise

    def remove_entity_knowledge(self, entity_id: str):
        """Remove entity knowledge"""
        try:
            if entity_id in self.indices:
                entity_type = self.entity_types.get(entity_id)

                # Prevent removal of permanent knowledge
                if entity_type in self.KNOWLEDGE_TYPES['PERMANENT']:
                    self.logger.warning(f"Attempted to remove permanent knowledge: {entity_id}")
                    return

                # Remove from memory
                del self.indices[entity_id]
                del self.texts[entity_id]
                del self.entity_types[entity_id]

                # Remove from disk
                index_path = os.path.join(self.index_dir, f"{entity_id}.index")
                text_path = os.path.join(self.text_dir, f"{entity_id}.json")

                if os.path.exists(index_path):
                    os.remove(index_path)
                if os.path.exists(text_path):
                    os.remove(text_path)

                self.logger.info(f"Removed knowledge for {entity_type}: {entity_id}")
        except Exception as e:
            self.logger.error(f"Error removing knowledge for {entity_id}: {e}")

    def clear_knowledge_base(self):
        """Clear non-permanent knowledge"""
        try:
            self.logger.info("Clearing knowledge base...")

            # Remove non-permanent entities
            to_remove = [
                entity_id for entity_id, entity_type in self.entity_types.items()
                if entity_type not in self.KNOWLEDGE_TYPES['PERMANENT']
            ]

            for entity_id in to_remove:
                self.remove_entity_knowledge(entity_id)

            self.logger.info("Knowledge base cleared successfully")
        except Exception as e:
            self.logger.error(f"Error clearing knowledge base: {e}")
            raise

