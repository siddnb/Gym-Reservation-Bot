import gspread
from gspread.models import Worksheet


class Booking:
    def __init__(self, rank_name = "",unit = ""):
        self.rank_name = rank_name
        self.unit = unit
        self.daily_bookings = {
            'Monday':'None', 'Tuesday':'None','Wednesday':'None', 'Thursday':'None','Friday':'None'
        }
        self.exists = False

    def add_booking(self, day, timeslot):
        self.daily_bookings[day] = timeslot

    def get_existing_user_info(self, worksheet, row):
        user_info = worksheet.row_values(row)
        self.rank_name = user_info[1]
        self.unit = user_info[2]
        i = 3
        #Assign the existing booking to each day
        for day in self.daily_bookings.keys():
            self.daily_bookings[day] = user_info[i] 
            i+=1

    def add_booking(self, uid, worksheet):
        row_to_add = [uid, self.rank_name, self.unit]
        if self.exists:
            old_row = worksheet.find(uid).row
            worksheet.delete_row(old_row)
        
        for timeslot in self.daily_bookings.values():
            row_to_add.append(timeslot)
        
        worksheet.append_row(row_to_add)

    def delete_booking(self, day_to_delete, uid, worksheet):
        row_to_add = [uid, self.rank_name, self.unit]
        
        old_row = worksheet.find(uid).row
        worksheet.delete_row(old_row)

        self.daily_bookings[day_to_delete] = 'None'
        
        for timeslot in self.daily_bookings.values():
            row_to_add.append(timeslot)
        
        worksheet.append_row(row_to_add)