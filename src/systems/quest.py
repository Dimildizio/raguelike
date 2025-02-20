from enum import Enum
from typing import Dict, List, Optional, Callable
import json
import logging


class QuestStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestCondition:
    def __init__(self, condition_type: str, required_value: int, current_value: int = 0, monster_tags: List[str] = None):
        self.type = condition_type  # e.g., "kill_goblins", "collect_herbs"
        self.required_value = required_value
        self.current_value = current_value
        self.monster_tags = monster_tags or []  # e.g., ["goblin_warrior", "goblin_archer"] for "kill_goblins"

    def is_met(self) -> bool:
        return self.current_value >= self.required_value

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "required_value": self.required_value,
            "current_value": self.current_value,
            "monster_tags": self.monster_tags
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'QuestCondition':
        return cls(
            data["type"],
            data["required_value"],
            data["current_value"],
            data.get("monster_tags", [])
        )


class Quest:
    def __init__(self,
                 quest_id: str,
                 title: str,
                 description: str,
                 giver_npc: str,
                 completion_conditions: List[QuestCondition],
                 reward_conditions: List[Dict],
                 status: QuestStatus = QuestStatus.NOT_STARTED):
        self.quest_id = quest_id
        self.title = title
        self.description = description
        self.giver_npc = giver_npc
        self.completion_conditions = completion_conditions
        self.reward_conditions = reward_conditions
        self.status = status

    def is_completed(self) -> bool:
        return all(condition.is_met() for condition in self.completion_conditions)

    def update_condition(self, condition_type: str, value: int = 1):
        """Update a specific condition's current value"""
        for condition in self.completion_conditions:
            if condition.type == condition_type:
                condition.current_value += value
                break

    def to_dict(self) -> Dict:
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "description": self.description,
            "giver_npc": self.giver_npc,
            "completion_conditions": [c.to_dict() for c in self.completion_conditions],
            "reward_conditions": self.reward_conditions,
            "status": self.status.value
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Quest':
        completion_conditions = [QuestCondition.from_dict(c) for c in data["completion_conditions"]]
        return cls(
            data["quest_id"],
            data["title"],
            data["description"],
            data["giver_npc"],
            completion_conditions,
            data["reward_conditions"],
            QuestStatus(data["status"])
        )


class QuestManager:
    def __init__(self, loading=False):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # Add file handler for quest events
        fh = logging.FileHandler('quest_debug.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.quests: Dict[str, Quest] = {}
        if not loading:
            self.initialize_quests()

    def save_quests(self):
        idict = {}
        for quest_id, quest in self.quests.items():
            idict[quest_id] = quest.to_dict()
        return idict

    def load_quests(self, data):
        self.quests = []
        for quest_id, values in data.items():
            self.quests[quest_id] = Quest.from_dict(values)


    def initialize_quests(self):
        """Initialize available quests"""
        # Example quest: Goblin Threat
        goblin_quest = Quest(
            quest_id="goblin_threat",
            title="The Goblin Threat",
            description="Deal with the goblins threatening the village. Kill two goblins and their wolf.",
            giver_npc="villager_amelia",
            completion_conditions=[
                QuestCondition("kill_goblins", 2, monster_tags=["goblin"]),
                #QuestCondition("kill_wolfs", 1, monster_tags=["wolf"]),
            ],
            reward_conditions=[
                {"type": "gold", "amount": 50},
                #{"type": "conditional", "condition": "has_wolf_pelt", "reward": {"gold": 10}, "consume_item": "wolf_pelt"}
            ]
        )
        self.quests[goblin_quest.quest_id] = goblin_quest

    def get_available_quests(self, npc_id: str) -> List[Quest]:
        """Get list of available quests from specific NPC"""
        return [quest for quest in self.quests.values()
                if quest.giver_npc == npc_id and
                quest.status == QuestStatus.NOT_STARTED]

    def get_active_quests(self) -> List[Quest]:
        """Get all in-progress quests"""
        return [quest for quest in self.quests.values() if quest.status == QuestStatus.IN_PROGRESS]

    def start_quest(self, quest_id: str) -> bool:
        """Start a quest if it exists and is not started"""
        if quest_id in self.quests and self.quests[quest_id].status == QuestStatus.NOT_STARTED:
            self.quests[quest_id].status = QuestStatus.IN_PROGRESS
            return True
        return False

    def update_quest_progress(self, condition_type: str, value: int = 1):
        """Update progress for all active quests with matching condition"""
        self.logger.debug(f"Updating progress for condition: {condition_type} (+{value})")

        for quest in self.get_active_quests():
            self.logger.debug(f"Checking quest: {quest.quest_id}")
            for condition in quest.completion_conditions:
                if condition.type == condition_type:
                    old_value = condition.current_value
                    condition.current_value += value
                    self.logger.info(
                        f"Quest '{quest.quest_id}' condition '{condition.type}' "
                        f"updated: {old_value} -> {condition.current_value} "
                        f"(required: {condition.required_value})")
                    if condition.is_met():
                        self.logger.info(f"Condition '{condition.type}' met for quest '{quest.quest_id}'!")


    def check_quest_completion(self, quest_id: str, player, npc=None) -> Optional[List[Dict]]:
        """Check if quest is complete and return rewards if conditions are met"""
        if quest_id not in self.quests:
            return None

        quest = self.quests[quest_id]
        if quest.status != QuestStatus.IN_PROGRESS or not quest.is_completed():
            return None

        # Verify NPC can pay rewards
        if npc is None:
            self.logger.warning(f"No NPC provided for quest completion: {quest_id}")
            return None

        rewards = []
        for reward_condition in quest.reward_conditions:
            if reward_condition["type"] == "gold":
                # Get actual reward from NPC
                actual_reward = npc.pay_reward(quest_id, reward_condition)
                if actual_reward["amount"] > 0:
                    rewards.append(actual_reward)

            elif reward_condition["type"] == "conditional":
                if reward_condition["condition"] == "has_wolf_pelt" and "wolf_pelt" in player.inventory:
                    # Handle conditional rewards through NPC as well
                    bonus_reward = npc.pay_reward(quest_id + "_bonus",
                                                  {"amount": reward_condition["reward"]["gold"]})
                    if bonus_reward["amount"] > 0:
                        rewards.append(bonus_reward)
                        if reward_condition.get("consume_item"):
                            player.inventory.remove(reward_condition["consume_item"])

            self.logger.info(f"Quest reward {rewards} given")

        if rewards:
            quest.status = QuestStatus.COMPLETED
            return rewards
        else:
            self.logger.warning(f"Quest {quest_id} completed but no rewards could be given")
            return None

    def save_quests(self) -> Dict:
        """Save all quests to dictionary"""
        return {quest_id: quest.to_dict() for quest_id, quest in self.quests.items()}

    def load_quests(self, data: Dict):
        """Load quests from dictionary"""
        self.quests = {quest_id: Quest.from_dict(quest_data)
                      for quest_id, quest_data in data.items()}

    def get_npc_quest_status(self, npc_id: str) -> Dict[str, List[Dict]]:
        """Get all quests and their status for a specific NPC"""
        npc_quests = {
            "available": [],
            "in_progress": [],
            "completed": [],
            "failed": []
        }

        for quest in self.quests.values():
            if quest.giver_npc == npc_id:
                quest_info = {
                    "quest_id": quest.quest_id,
                    "title": quest.title,
                    "description": quest.description,
                    'reward_conditions': quest.reward_conditions,
                    "conditions": [
                        {
                            "type": condition.type,
                            "current": condition.current_value,
                            "required": condition.required_value
                        } for condition in quest.completion_conditions
                    ]
                }

                if quest.status == QuestStatus.NOT_STARTED:
                    npc_quests["available"].append(quest_info)
                elif quest.status == QuestStatus.IN_PROGRESS:
                    npc_quests["in_progress"].append(quest_info)
                elif quest.status == QuestStatus.COMPLETED:
                    npc_quests["completed"].append(quest_info)
                elif quest.status == QuestStatus.FAILED:
                    npc_quests["failed"].append(quest_info)
        return npc_quests

    @staticmethod
    def get_status_quest_data(status, quest_status, quest_info):
        if quest_status[status]:
            quest_info.append(f"{status} quests:")
            for quest in quest_status[status]:
                quest_info.append(f"- {quest['quest_id']}: {quest['title']}, max_reward: {quest['reward_conditions']}")
        return quest_info

    def format_quest_status(self, npc_id: str) -> str:
        """Format quest status information for an NPC into a readable string"""
        quest_status = self.get_npc_quest_status(npc_id)
        quest_info = []
        print('QUEST STATUS: {0}'.format(quest_status))

        if quest_status["in_progress"]:
            quest_info.append("\nOngoing quests:")
            for quest in quest_status["in_progress"]:
                progress = [f"{cond['type']}: {cond['current']}/{cond['required']}"
                            for cond in quest['conditions']]
                quest_info.append(f"- {quest['quest_id']}: {quest['title']}")
                quest_info.append(f"  Progress: {', '.join(progress)}")

        for status in ('failed', 'completed', 'available'):
            quest_info = self.get_status_quest_data(status, quest_status, quest_info)

        return "\n".join(quest_info) if quest_info else "No quests available."

    def format_all_quests_status(self) -> str:
        """Format all quests status into a readable string"""
        quest_info = ["=== QUEST JOURNAL ==="]

        # Group quests by status
        status_groups = {
            "IN_PROGRESS": [],
            "NOT_STARTED": [],
            "COMPLETED": [],
            "FAILED": []
        }

        for quest in self.quests.values():
            status_groups[quest.status.name].append(quest)

        # Active quests first
        if status_groups["IN_PROGRESS"]:
            quest_info.append("\nACTIVE QUESTS:")
            for quest in status_groups["IN_PROGRESS"]:
                quest_info.append(f"\n{quest.title} ({quest.quest_id})")
                quest_info.append(f"Given by: {quest.giver_npc}")
                quest_info.append(f"Description: {quest.description}")
                quest_info.append("Progress:")
                for condition in quest.completion_conditions:
                    quest_info.append(f"- {condition.type}: {condition.current_value}/{condition.required_value}")

        # Available quests
        if status_groups["NOT_STARTED"]:
            quest_info.append("\nAVAILABLE QUESTS:")
            for quest in status_groups["NOT_STARTED"]:
                quest_info.append(f"- {quest.title} (from {quest.giver_npc}  max reward: {quest.reward_conditions})")

        # Completed quests
        if status_groups["COMPLETED"]:
            quest_info.append("\nCOMPLETED QUESTS:")
            for quest in status_groups["COMPLETED"]:
                quest_info.append(f"- {quest.title}")

        # Failed quests
        if status_groups["FAILED"]:
            quest_info.append("\nFAILED QUESTS:")
            for quest in status_groups["FAILED"]:
                quest_info.append(f"- {quest.title}")

        return "\n".join(quest_info)