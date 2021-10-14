from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ChatAction
import logging
from caps import capacities
import os
import buttons

from telegram.ext.conversationhandler import ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials


scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive.file',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)
trackingSheet = client.open("Bot Tracking").worksheet('Sheet1')
slotsSheet = client.open("Bot Tracking").worksheet('Sheet2')

NAME, UNIT, DAY, TIME, CONFIRMATION, SUBMIT, CANCEL = range(7)

user_info = {}


def get_slots(day):
    slots = {}
    i = 0
    if day != 'Friday':
        for cell in capacities[day]:
            slots[buttons.timeslotsMonToThur[i]] = int(slotsSheet.acell(cell).value)
            i+=1
    else:
        for cell in capacities[day]:
            slots[buttons.timeslotFri[i]] = int(slotsSheet.acell(cell).value)
            i+=1
    return slots

def get_user_bookings(UID):
    prev_user = trackingSheet.find(UID)
    existing_user_info = ["None"]*5
    if prev_user is not None:
        existing_user_info = trackingSheet.row_values(prev_user.row)[3:8]
    return existing_user_info

def correct_format(update: Update, context):
    #for any errors in submission, Bot will send this to user.
    update.message.delete()
    update.message.reply_text(
        'It seems like there was an error. \n'
        'Please type it in the appropriate format: \n\n'
        'For Name: Rank <Space> Name\n\n'
        'For Subunit: BNHQ/ALPHA/BRAVO/BOAT/SUPPORT \n\n'
        'Please input the correct format', reply_markup=ReplyKeyboardRemove() )

def start(update: Update, context):
    update.message.reply_text(
        "Hello there. Input the password to continue or type /cancel to end the conversation.",reply_markup=ReplyKeyboardRemove()
        )
    return NAME

def name(update: Update, context):
    if(update.message.text == 'Pass'):
        userID = str(update.message.chat_id)
        user_info[userID] = []
        update.message.reply_text(
        'What is your name? (Please key in as Rank <Space> Name)', 
        reply_markup=ReplyKeyboardRemove()
        )
        return UNIT
    else:
        update.message.reply_text('Wrong password, type /start to try signing in again.')
    

def unit(update: Update, context):
    userID = str(update.message.chat_id)
    user_info[userID].append(str(update.message.text))
    reply_keyboard = [['BNHQ'], ['ALPHA'], ['BRAVO'],['BOAT'], ['SUPPORT']]
    update.message.reply_text(
        'What subunit are you from? Please enter in CAPS.\n'
        'Enter one: BNHQ, ALPHA, BRAVO, BOAT, SUPPORT \n'
        'Send /cancel to stop talking to me.\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard),
    )
    return DAY

def day(update: Update, context):
    userID = str(update.message.chat_id)
    user_info[userID].append(str(update.message.text))

    current_bookings = get_user_bookings(userID)
    print(current_bookings)
    print(list(capacities.keys()))
    reply_keyboard = [[list(capacities.keys())[i]] for i in range(5) if current_bookings[i] == "None"]

    update.message.reply_text(
        '''What day would you like to make a booking for?
        Send /cancel to stop talking to me.
        ''',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )
    return TIME

def timeslot(update: Update, context):
    day = update.message.text
    if (day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']):
        userID = str(update.message.chat_id)
        user_info[userID].append(str(update.message.text))

        current_caps = get_slots(str(update.message.text))

        #Adds the timeslots only if there are any free slots remaining.
        reply_keyboard = [[f'{times} ({current_caps[times]})'] for times in buttons.timeslotsMonToThur if current_caps[times]>0]
        update.message.reply_text(
            'What time would you like to book?\n'
            'Send /cancel to stop talking to me.\n',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )
        return CONFIRMATION
    elif update.message.text == 'Friday':
        userID = str(update.message.chat_id)
        user_info[userID].append(str(update.message.text))

        current_caps = get_slots(str(update.message.text))

        reply_keyboard = [[f'{times} ({current_caps[times]})'] for times in buttons.timeslotsFri if current_caps[times]>0]
        update.message.reply_text(
            'What timeslot would you like to book?\n'
            'Send /cancel to stop talking to me.\n',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )
        return CONFIRMATION
    else:
        update.message.reply_text('Please enter Monday, Tuesday, Wednesday, Thursday, or Friday')
        
def confirmation(update: Update, context):
    userID = str(update.message.chat_id)
    user_info[userID].append(str(update.message.text))
    reply_keyboard = [['Yes','No']]
    update.message.reply_text('ya sure??',
    reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )
    return SUBMIT

def submit(update: Update, context):
    if update.message.text == 'Yes':

        UID = str(update.message.chat_id)
        name = user_info[UID][0]
        coy = user_info[UID][1]
        day = user_info[UID][2]
        timeslot = user_info[UID][3][:9]
        day_to_index = {'Monday': 3, "Tuesday":4, "Wednesday":5, "Thursday":6, "Friday":7}
        booking = [UID,name, coy,"None", "None","None","None","None"]
        
        booking[day_to_index[day]] = timeslot
        
        trackingSheet.append_row(booking)

        update.message.reply_text('Booking successful.',
        reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END
    else:
        update.message.reply_text('submission cancelled.',
        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

def cancel(update: Update, context):
    #if user sends /cancel command, ends conversation
    #user = update.message.from_user
    #logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Byebye', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    updater  = Updater(token=os.environ["TOKEN"], use_context = True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    

    start_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
    states={NAME: [MessageHandler(Filters.text,name)],
    UNIT: [MessageHandler(Filters.regex('^\w+\s\.*'),unit)],
    DAY: [MessageHandler(Filters.regex('^BNHQ$|^ALPHA$|^BRAVO$|^BOAT$|^SUPPORT$'),day)],
    TIME: [MessageHandler(Filters.regex('^Monday$|^Tuesday$|^Wednesday$|^Thursday$|^Friday$'),timeslot)],
    CONFIRMATION: [MessageHandler(Filters.regex(
        '^0730-0845|^0850-1005|^1010-1125|^1300-1415|^1420-1535|^1540-1655|^1830-1955|^2000-2130'),confirmation)],
    SUBMIT: [MessageHandler(Filters.regex('^Yes$|^yes$|^No$|^no$'), submit)]
    },
    fallbacks = [CommandHandler('cancel',cancel),MessageHandler(Filters.text, correct_format)]
    )

    dispatcher.add_handler(start_conv_handler)


    updater.start_polling()
    

if __name__ == '__main__':
    main()