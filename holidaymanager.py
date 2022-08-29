from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import sys
from config import api_key
import os

def print_header(prompt):
    print(f"\n{prompt}\n{'='*20}")

def check_valid_selection(selection_dict):
    valid = False
    while valid == False:
        try:
            selection = int(input(""))
            if selection in selection_dict.keys():
                valid = True
        except:
            valid = False
        if valid == False:
            print("Please enter a valid selection!")
    return selection

def check_valid_date(type_to_check, min_date, max_date):
    valid = False
    while not valid:
        if type_to_check == 'date':
            try:
                date_string = input("Date:")
                date_string = datetime.strptime(date_string, '%Y-%m-%d').date()
                if date_string >= min_date and date_string <= max_date:
                    valid = True
            except:
                valid = False
            if not valid:
                print(f"Please enter a valid date between {datetime.strftime(min_date, '%Y-%m-%d')} and {datetime.strftime(max_date, '%Y-%m-%d')} in yyyy-mm-dd format!")
        elif type_to_check == 'year':
            try:
                date_string = int(input("Year:"))
                if date_string >= min_date.year and date_string <= max_date.year:
                    valid = True
            except:
                valid = False
            if not valid:
                print(f"Please enter a valid year between {min_date.year} and {max_date.year} in yyyy format!")
        elif type_to_check == 'week':
            try:
                date_string = input("Week (1-52, leave blank for current week):")
                if date_string == '':
                    valid = True                
                elif int(date_string) >= 1 and int(date_string) <= 52:
                    valid = True
            except:
                valid = False
            if not valid:
                print("Please enter a valid week between 1 and 52, or leave it blank for the current week!")
       
    return date_string

def check_yes_no(prompt):
    valid = False
    response = ""
    while not valid:
        response = input(f'{prompt}(y/n)\n')
        if response not in ["y", "n"]:
            print("Please enter either y or n!")
        else:
            valid = True
    if response == "y":
        return True
    else:
        return False
        
@dataclass
class Holiday:
    name: str
    date: datetime.date
    def __gt__(self, other):
        if self.date > other.date:
            return True
        else:
            return False
    def __ge__(self, other):
        if self.date >= other.date:
            return True
        else:
            return False
    def __lt__(self, other):
        if self.date < other.date:
            return True
        else:
            return False
    def __le__(self, other):
        if self.date <= other.date:
            return True
        else:
            return False
    def __eq__(self, other):
        if self.date == other.date and self.name == other.name: #After looking into this, I believe this is actually the default logic for '==' in regards to objects and hence didn't need to make this method. Still, better safe than sorry...
            return True
        else:
            return False
    def __dict__(self):
        return {'name': self.name, 'date': datetime.strftime(self.date, '%Y-%m-%d')}

    def __str__(self):
        return f'Name: {self.name} Date: {self.date}'

#@dataclass
class HolidayManager:
    def __init__(self, holiday_list):
        self.holiday_list = sorted(holiday_list)
        self.edited_list = holiday_list.copy()
        self.edited = False
        self.min_date = min(self.edited_list).date
        self.max_date = max(self.edited_list).date

    def add_holiday(self, selection_text):
        valid = False
        while not valid:
            holiday_object = Holiday(input("Holiday name:\n"), check_valid_date('date', self.min_date, self.max_date))
            if holiday_object in self.holiday_list:
                print("This holiday is already in the system!")
                del holiday_object
            else:
                self.edited_list.append(holiday_object)
                self.edited_list.sort()
                self.edited = True
                valid = True
                print(f"{holiday_object.name} has been added to your list.")

    def remove_holiday(self, selection_text):
        valid = False
        while not valid:
            holiday_object = Holiday(input(("Holiday Name:")), check_valid_date('date', self.min_date, self.max_date))
            if holiday_object not in self.edited_list:
                print("Please enter a valid holiday and date!")
            else:
                self.edited_list.remove(holiday_object)
                self.edited_list.sort()
                self.edited = True
                valid = True
                print(f"{holiday_object.name} has been removed from your list.")
            del holiday_object

    def save_holiday(self, selection_text):
        save_confirmed = check_yes_no("Would you like to save your list?")
        if save_confirmed:
            self.holiday_list = self.edited_list.copy() #So I've tested this, and it looks like the new list does not create new objects that happen to have the same contents as the copied one. Could be wrong though.
            self.holiday_list.sort()
            holiday_dicts = json.dumps(list(map(lambda x: x.__dict__(), self.holiday_list)))
            f = open('output_file.json', 'w')
            f.write(holiday_dicts)
            f.close()
            self.edited = False

    def view_holiday(self, selection_text):
        year = int(check_valid_date('year', self.min_date, self.max_date))
        week = check_valid_date('week', self.min_date, self.max_date)
        confirm_view_weather = False
        if week != '':
            week = int(week)
        else:
            week = datetime.today().isocalendar()[1]
            confirm_view_weather = check_yes_no('Would you like to check the weather for this week?')
        view_list = sorted(list(filter(lambda x: x.date.year == year and x.date.isocalendar()[1] == week, self.edited_list))) #Note: Because of how .isocalendar() works, the first days of January can be on the 52nd week of the calendar.
        if confirm_view_weather:
            min_date = datetime.strftime(min(view_list).date, '%Y-%m-%d')
            max_date = datetime.strftime(max(view_list).date, '%Y-%m-%d')
            weather_dicts = self.api_call(api_key, min_date, max_date)
            if weather_dicts is not None:
                weather_info = [{'date': datetime.strptime(day['datetime'], '%Y-%m-%d').date(), 'conditions': day['conditions']} for day in weather_dicts['days']]
            else: 
                print("\nSorry, weather data not available!\n")
        for holiday in view_list:
            display_string = f'{holiday.name} ({holiday.date})'
            if confirm_view_weather and weather_dicts is not None:
                for weather in weather_info:
                    if holiday.date == weather['date']:
                        display_string = f"{display_string} - {weather['conditions']}"
            print(display_string)


    def exit(self, selection_text):
        prompt = "Are you sure you would like to quit?"
        if self.edited:
            prompt = f'{prompt}\nYour changes will be lost!'
        exit_confirmed = check_yes_no(prompt)
        if exit_confirmed:
            exit()

    def api_call(self, api_key, min_date, max_date):
        try:
            response = requests.get(f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/bronx/{min_date}/{max_date}?unitGroup=us&elements=datetime%2Cconditions&key={api_key}&contentType=json')
            result = response.json()
        except:
            result = None
        return result

#@dataclass
class Menu:
    def __init__(self, manager):
        self.manager = manager
        self.selections: dict = {
                    1: ['Add a Holiday', manager.add_holiday],
                    2: ['Remove a Holiday', manager.remove_holiday],
                    3: ['Save Holiday List', manager.save_holiday],
                    4: ['View Holidays', manager.view_holiday],
                    5: ['Exit', manager.exit]
                    }

    def __str__(self):
        menu_string = f"\nMain Menu\n{'='*20}"
        for item in self.selections.items():
            menu_string = f'{menu_string}\n{item[0]}. {item[1][0]}'
        return menu_string

    def select(self):
        selection = check_valid_selection(self.selections)
        print_header(self.selections[selection][0])
        self.selections[selection][1](self.selections[selection][0])
    
    def display_menu(self):
        while True: #The only way to get out is to pick the option for exit.
            print(self)
            self.select()

def startup():
    if not os.path.isfile('output_file.json'):
        f = open('holidays.json', 'r')
        holiday_dicts = json.loads(f.read())['holidays']
        holiday_set = set([(holiday['name'], datetime.strptime(holiday['date'], '%Y-%m-%d').date()) for holiday in holiday_dicts]) #A set, by definition, will only have unique elements. Thus, by adding a new element to this set, it will guarantee its uniqueness. 
        
        try:
            current_year = datetime.now().year
            for year in range(current_year - 2, current_year + 3):
                response = requests.get(f'https://www.timeanddate.com/holidays/us/{year}')
                soup = BeautifulSoup(response.text, 'html.parser')
                holidays = soup.find('tbody').find_all('tr')
                for holiday in holidays:
                    if 'tr' in holiday.attrs['id']:
                        holiday_set.add(
                            (
                                holiday.find('a').text, 
                                datetime.strptime(
                                    f"{holiday.find('th').text} {year}", 
                                    '%b %d %Y'
                                    ).date()
                                ) #This indicates that I want to turn this into a tuple, which is one of those 'hashable types' that Python supports. A set only allows hashable types. Convenient.
                            )
        except:
            print("Unable to scrape data from https://www.timeanddate.com!")

    else:
        f = open('output_file.json', 'r')
        holiday_dicts = json.loads(f.read())
        holiday_set = set([(holiday['name'], datetime.strptime(holiday['date'], '%Y-%m-%d').date()) for holiday in holiday_dicts])

    manager = HolidayManager([Holiday(holiday[0], holiday[1]) for holiday in list(holiday_set)])
    manager.holiday_list.sort()

    print(f"Holiday Manager\n{'='*20}")
    print(f"You have {len(manager.holiday_list)} holidays stored.")
    main_menu = Menu(manager)
    main_menu.display_menu()

if __name__ == '__main__':
    startup()