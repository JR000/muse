from dataclasses import dataclass
from datetime import datetime
import json
from typing import Optional

@dataclass
class Card:
    id: Optional[str] = ""
    _type: Optional[str] = ""
    content: Optional[str] = ""
    carries: Optional[list[str]] = None
    recall: Optional[float] = 1

    def __str__(self):
        return f"{self.id}@{self._type}@{self.content}@{json.dumps(self.carries)}`"
    
@dataclass
class Log:
    card_id: str
    date: datetime
    model: list 
    result: float = 1
    def __repr__(self):
        # print(f"{self.card_id}@{self.date}@{json.dumps(self.model)}")
        return f"{self.card_id}@{self.date.timestamp()}@{json.dumps(self.model)}@{self.result}"
    
def load_cards() -> (dict[str, Card], dict):
    cards = {}
    
    with open('cards.txt', encoding='utf-8') as cards_file:
        for line in ''.join(cards_file.readlines()).replace('`\n', '`').split('`'):
            if line.find('@') < 0:
                continue
            print(line)
            id, _type, content, carries = line.split('@')
            carries = json.loads(carries)
            cards[id] = Card(id, _type, content, carries)
            
    return cards

def load_logs() -> dict[str, Log]:
    logs = {}
    
    with open('logs.txt', encoding='utf-8') as logs_file:
        for line in logs_file.readlines():
            card, date, model, result = line.split('@')
            date = datetime.fromtimestamp(float(date))
            model = json.loads(model)
            result = float(result)
            
            log = Log(card, date, model)
            if card not in logs:
                logs[card] = [log]
            else:
                logs[card].append(log)
    print(logs)
    return logs

def save_cards(cards: list[Card]):
    with open("cards.txt", 'w', encoding='utf-8') as cards_file:
        for card in cards:
            cards_file.write(str(card) + '\n')
            
def save_logs(logs: list[Log]):
    with open("logs.txt", 'w', encoding='utf-8') as logs_file:
        for log in logs:
            logs_file.write(str(log) + '\n')