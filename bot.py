from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ChatAction, message
import logging
from caps import capacities
import os
import buttons
from booking import Booking

from telegram.ext.conversationhandler import ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive.file',
         'https://www.googleapis.com/auth/drive']
jsonfile = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
creds = ServiceAccountCredentials.from_json_keyfile_name(jsonfile, scope)
client = gspread.authorize(creds)
trackingSheet = client.open("Bot Tracking").worksheet('Sheet1')
slotsSheet = client.open("Bot Tracking").worksheet('Sheet2')

TOKEN = os.environ["TOKEN"]
PORT = int(os.environ.get('PORT', '8443'))
 
MENU, CHECKSTATE, VIEWBOOKING, NAME, UNIT, DAY, TIME, CONFIRMATION, SUBMIT, QUIT = range(10)

session_booking = {}

# To store user's booking day 
session_day = {}

def get_slots(day):
    slots = {}
    i = 0
    if day != 'Friday':
        for cell in capacities[day]:
            slots[buttons.timeslotsMonToThur[i]] = int(slotsSheet.acell(cell).value)
            i+=1
    else:
        for cell in capacities[day]:
            slots[buttons.timeslotsFri[i]] = int(slotsSheet.acell(cell).value)
            i+=1

    return slots

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

    return MENU

def menu(update: Update, context):
    if update.message.text == 'Pass':
        user_id = str(update.message.chat_id)
        session_booking[user_id] = Booking()

        user_cell = trackingSheet.find(user_id)

        if user_cell is not None:
            session_booking[user_id].exists = True
            session_booking[user_id].get_existing_user_info(trackingSheet,user_cell.row)

        reply_keyboard = [['Make A New Booking'], ['Edit A Booking'],['View Existing Bookings'],['Quit']]
        update.message.reply_text(
        'What would you like to do?', 
        reply_markup = ReplyKeyboardMarkup(reply_keyboard)
        )

        return CHECKSTATE
    elif update.message.text == '/cancel':

        return quit(update,context)
    else:
        update.message.reply_text('Wrong password, type /start to try signing in again.')

def check_state(update: Update, context):
    user_id = str(update.message.chat_id)

    response = update.message.text

    if response == 'Quit':

        return quit(update,context)

    if response == 'Make A New Booking':
        #Need to return functions because using conversation handler you need an update to prompt a state change otherwise. 
        if session_booking[user_id].exists:

            return day(update,context) 
        else:

            return name(update,context)
    elif response == 'View Existing Bookings':

        return view_booking(update,context)

def view_booking(update: Update, context):
    user_id = str(update.message.chat_id)

    existing_bookings = ""
    for day, timeslot in session_booking[user_id].daily_bookings.items():
        if timeslot != "None":
            existing_bookings = existing_bookings + day+": "+timeslot+"\n"

    update.message.reply_text(f'These are your existing bookings, {session_booking[user_id].rank_name}: \n'
    f'{existing_bookings}',reply_markup= ReplyKeyboardRemove())

    return ConversationHandler.END
    

def name(update: Update, context):
        update.message.reply_text(
        'Enter your name (key in as Rank <Space> Name)', 
        reply_markup=ReplyKeyboardMarkup(['Quit'])
        )

        return UNIT
    

def unit(update: Update, context):
    user_id = str(update.message.chat_id)

    response = update.message.text
    if response == 'Quit':
        
        return QUIT

    session_booking[user_id].rank_name = response

    reply_keyboard = [['BNHQ'], ['ALPHA'], ['BRAVO'],['BOAT'], ['SUPPORT'],['Quit']]
    update.message.reply_text('''
    What subunit are you from? Please enter in CAPS.
    Enter one: BNHQ, ALPHA, BRAVO, BOAT, SUPPORT.''',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard),
    )

    return DAY

def day(update: Update, context):
    user_id = str(update.message.chat_id)

    response = update.message.text
    if response == 'Quit':
        
        return QUIT

    #TODO: Add check whether coming from UNIT or SUBMIT state
    if not session_booking[user_id].exists:
        session_booking[user_id].unit = response

    current_bookings = list(session_booking[user_id].daily_bookings.values())

    # Display a day as an option if there is no previous booking (indicated by 'None')
    reply_keyboard = [[list(session_booking[user_id].daily_bookings.keys())[i]] for i in range(5) if current_bookings[i] == 'None']
    reply_keyboard.append(['Quit'])

    update.message.reply_text('''
    What day would you like to make a booking for?
    Send /cancel to stop talking to me.''',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )

    return TIME

def timeslot(update: Update, context):
    day = update.message.text

    if day == 'Quit':
        
        return quit(update,context)

    if (day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']):
        user_id = str(update.message.chat_id)
        session_day[user_id] = str(update.message.text)

        current_caps = get_slots(str(update.message.text))

        #Adds the timeslots only if there are any free slots remaining.
        reply_keyboard = [[f'{times} ({current_caps[times]})'] for times in buttons.timeslotsMonToThur if current_caps[times]>0]
        reply_keyboard.append(['Quit'])

        update.message.reply_text('''
        What time would you like to book?
        Send /cancel to stop talking to me.''',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )

        return CONFIRMATION
    elif update.message.text == 'Friday':
        user_id = str(update.message.chat_id)
        session_day[user_id] = str(update.message.text)

        current_caps = get_slots(str(update.message.text))

        reply_keyboard = [[f'{times} ({current_caps[times]})'] for times in buttons.timeslotsFri if current_caps[times]>0]
        reply_keyboard.append(['Quit'])

        update.message.reply_text('''
        What time would you like to book?
        Send /cancel to stop talking to me.''',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )

        return CONFIRMATION
    else:
        update.message.reply_text('Please enter Monday, Tuesday, Wednesday, Thursday, or Friday')
        
def confirmation(update: Update, context):
    user_id = str(update.message.chat_id)
    day_to_book = session_day[user_id]

    response = update.message.text

    if response == 'Quit':
        
        return quit(update,context)

    # We only want to store the timeslot. 
    # This update text is in the following format 'timeslot' (8 chars) 'slots remaining' (the rest of the text), so we need to slice it.
    session_booking[user_id].daily_bookings[day_to_book] = response[:9]

    reply_keyboard = [['Submit'],['Change Booking'],['Quit']]
    update.message.reply_text(f'''
    Your booking details are as follows:
    Day: {day_to_book}
    Time: {update.message.text[:9]}

    Do you want to submit this booking?''',
    reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )

    return SUBMIT

def submit(update: Update, context):
    if update.message.text == 'Submit':
        user_id = str(update.message.chat_id)
        session_booking[user_id].add_booking(user_id,trackingSheet)

        update.message.reply_text('Booking successful. Type /start to start over',
        reply_markup=ReplyKeyboardRemove()
        )

        session_booking.pop(user_id)
        session_day.pop(user_id)

        return ConversationHandler.END
    else:
        update.message.reply_text('submission cancelled, type /start to start over.',
        reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END

def quit(update: Update, context):
    update.message.reply_text(
        'The process has been cancelled, type /start to start over.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    updater  = Updater(token=TOKEN, use_context = True)
    dispatcher = updater.dispatcher

    start_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
    states={MENU:[MessageHandler(Filters.text,menu)],
    CHECKSTATE: [MessageHandler(Filters.text, check_state)],
    VIEWBOOKING: [MessageHandler(Filters.text, view_booking)],
    NAME: [MessageHandler(Filters.text,name)],
    UNIT: [MessageHandler(Filters.regex('^\w+\s\.*'),unit)],
    DAY: [MessageHandler(Filters.text,day)],
    TIME: [MessageHandler(Filters.text,timeslot)],
    CONFIRMATION: [MessageHandler(Filters.text,confirmation)],
    SUBMIT: [MessageHandler(Filters.regex('^Submit$|^Quit$'), submit)],
    QUIT: [MessageHandler(Filters.text,quit)]
    },
    fallbacks = [CommandHandler('cancel',quit),MessageHandler(Filters.text|~Filters.text,correct_format)]
    )

    dispatcher.add_handler(start_conv_handler)


    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,webhook_url= 'https://secret-badlands-60887.herokuapp.com/' + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()