import json
import sys
import random
from typing import List, Optional
from enum import Enum






class EventStatus(Enum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"
    PARTIAL_PASS = "partial_pass"






class Statistic:
    def __init__(self, name: str, value: int = 0, description: str = "", min_value: int = 0, max_value: int = 100):
        self.name = name
        self.value = value
        self.description = description
        self.min_value = min_value
        self.max_value = max_value

    def __str__(self):
        return f"{self.name}: {self.value}"

    def modify(self, amount: int):
        self.value = max(self.min_value, min(self.max_value, self.value + amount))






class Character:
    def __init__(self, name: str = "Bob"):
        self.name = name
        self.strength = Statistic("Strength", description="Strength is a measure of physical power.")
        self.intelligence = Statistic("Intelligence", description="Intelligence is a measure of cognitive ability.")
        # Add more stats as needed

    def __str__(self):
        return f"Character: {self.name}, Strength: {self.strength}, Intelligence: {self.intelligence}"

    def get_stats(self):
        return [self.strength, self.intelligence]  # Extend this list if there are more stats






class Event:
    def __init__(self, data: dict):
        self.primary_attribute = data['primary_attribute']
        self.secondary_attribute = data['secondary_attribute']
        self.prompt_text = data['prompt_text']
        self.pass_message = data['pass']['message']
        self.fail_message = data['fail']['message']
        self.partial_pass_message = data['partial_pass']['message']
        self.status = EventStatus.UNKNOWN

    def execute(self, party: List[Character], parser):
        print(self.prompt_text)
        character = parser.select_party_member(party)
        chosen_stat = parser.select_stat(character)
        self.resolve_choice(character, chosen_stat)

    def resolve_choice(self, character: Character, chosen_stat: Statistic):
        if chosen_stat.name == self.primary_attribute:
            self.status = EventStatus.PASS
            print(self.pass_message)
        elif chosen_stat.name == self.secondary_attribute:
            self.status = EventStatus.PARTIAL_PASS
            print(self.partial_pass_message)
        else:
            self.status = EventStatus.FAIL
            print(self.fail_message)






class Location:
    def __init__(self, name: str, events: List[Event]):
        self.name = name
        self.events = events
        self.travel_events = {}  # Dictionary mapping destination name to travel events
        
    def add_travel_event(self, destination: str, event: Event):
        """Add a travel event to this location that leads to the specified destination"""
        if destination not in self.travel_events:
            self.travel_events[destination] = []
        self.travel_events[destination].append(event)
    
    def get_event(self) -> Event:
        """Get a random local event for this location"""
        return random.choice(self.events)
    
    def get_travel_options(self) -> List[str]:
        """Get a list of available destinations from this location"""
        return list(self.travel_events.keys())
    
    def get_travel_event(self, destination: str) -> Optional[Event]:
        """Get a random travel event to the specified destination"""
        if destination in self.travel_events and self.travel_events[destination]:
            return random.choice(self.travel_events[destination])
        return None






class Game:
    def __init__(self, parser, characters: List[Character], locations: dict):
        self.parser = parser
        self.party = characters
        self.locations = locations  # Change from List to dict
        self.current_location = None  # Add this line
        self.continue_playing = True
        
    def start(self, starting_location: str = None):
       """Start the game at the specified location or a random one"""
       if starting_location and starting_location in self.locations:
        self.current_location = self.locations[starting_location]
       else:
           self.current_location = random.choice(list(self.locations.values()))
           
        print(f"Your adventure begins in the {self.current_location.name}...")
    
        while self.continue_playing:
            self.location_menu()  # New method to call
        if self.check_game_over():
            self.continue_playing = False
        print("Game Over.")

    def location_menu(self):
        """Present options for the current location"""
        print(f"\n=== {self.current_location.name} ===")
        print("What would you like to do?")
        print("1. Explore this area")
        print("2. Travel to another location")
        print("3. Check party status")
        print("4. Quit game")
     
        choice = int(self.parser.parse("Enter your choice: "))
     
        if choice == 1:
            # Explore the current location
            event = self.current_location.get_event()
            event.execute(self.party, self.parser)
        elif choice == 2:
            # Attempt to travel to a new location
            self.travel_menu()
        elif choice == 3:
            # Show party status
            self.show_party_status()
        elif choice == 4:
            self.continue_playing = False
     
    def travel_menu(self):
        """Present travel options from the current location"""
        travel_options = self.current_location.get_travel_options()
            
        if not travel_options:
            print("There are no known paths from this location yet.")
        return
         
        print(f"\nFrom {self.current_location.name}, you can travel to:")
        for idx, destination in enumerate(travel_options):
            print(f"{idx + 1}. {destination}")
        print(f"{len(travel_options) + 1}. Stay in {self.current_location.name}")
         
        choice = int(self.parser.parse("Enter your choice: "))
         
        if 1 <= choice <= len(travel_options):
            destination = travel_options[choice - 1]
            travel_event = self.current_location.get_travel_event(destination)
             
            if travel_event:
                travel_event.execute(self.party, self.parser)
                 
                # Check if the travel was successful
                if travel_event.status in [EventStatus.PASS, EventStatus.PARTIAL_PASS]:
                    self.current_location = self.locations[destination]
                    print(f"You have arrived at {destination}!")
 
    def show_party_status(self):
        """Display the status of all party members"""
        print("\n=== Party Status ===")
        for character in self.party:
            print(character)


    def check_game_over(self):
        return len(self.party) == 0






class UserInputParser:
    def parse(self, prompt: str) -> str:
        return input(prompt)

    def select_party_member(self, party: List[Character]) -> Character:
        print("Choose a party member:")
        for idx, member in enumerate(party):
            print(f"{idx + 1}. {member.name}")
        choice = int(self.parse("Enter the number of the chosen party member: ")) - 1
        return party[choice]

    def select_stat(self, character: Character) -> Statistic:
        print(f"Choose a stat for {character.name}:")
        stats = character.get_stats()
        for idx, stat in enumerate(stats):
            print(f"{idx + 1}. {stat.name} ({stat.value})")
        choice = int(self.parse("Enter the number of the stat to use: ")) - 1
        return stats[choice]


def load_events_from_json(file_path: str) -> List[Event]:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return [Event(event_data) for event_data in data]



def start_game():
    parser = UserInputParser()
    characters = [
        Character("Warrior"),
        Character("Scholar"),
        Character("Ranger")
    ]
    
    # Initialize character stats
    for char in characters:
        char.strength.value = random.randint(30, 70)
        char.intelligence.value = random.randint(30, 70)
    
    # Create locations
    locations = {
        "Forest": Location("Forest", load_events_from_json('forest_events.json')),
        "Mountain": Location("Mountain", load_events_from_json('mountain_events.json')),
        # Add more locations as needed
    }
    
    # Load travel events
    travel_data = load_events_from_json('travel_events.json')
    
    # Add travel events to locations
    for event_data in travel_data:
        from_loc = event_data["from_location"]
        to_loc = event_data["to_location"]
        
        if from_loc in locations and to_loc in locations:
            event = Event(event_data)
            locations[from_loc].add_travel_event(to_loc, event)
    
    # Create and return the game
    game = Game(parser, characters, locations)
    game.start("Forest")  # Start in the forest

