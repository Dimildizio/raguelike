from constants import MAX_INVENTORY_SLOTS

class Inventory:
    def __init__(self, size=MAX_INVENTORY_SLOTS):
        self.items = []
        self.size = size
        
    def add_item(self, item):
        if len(self.items) < self.size:
            self.items.append(item)
            return True
        return False
        
    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False