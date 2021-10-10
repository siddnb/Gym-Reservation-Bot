from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ChatAction
import logging
from caps import caps
import os

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
    slots = []
    for cell in caps[day]:
        slots.append(slotsSheet.acell(cell).value)
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
    reply_keyboard = [['BNHQ', 'ALPHA', 'BRAVO','BOAT', 'SUPPORT']]
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
    reply_keyboard = [['Monday'],['Tuesday'], ['Wednesday'], ['Thursday'], ['Friday']]
    update.message.reply_text(
        'What day would you like to make a booking for?\n'
        'Enter one: Monday, Tuesday, Wednesday, Thursday, Friday \n'
        'Send /cancel to stop talking to me.\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )
    return TIME

def timeslot(update: Update, context):
    day = update.message.text
    if (
        day == 'Monday' 
        or day == 'Tuesday' 
        or day == 'Wednesday' 
        or day == 'Thursday'
        ):
        userID = str(update.message.chat_id)
        user_info[userID].append(str(update.message.text))

        caps = get_slots(str(update.message.text))

        reply_keyboard = [['0730-0845 ('+caps[0]+' slots remaining)'], ['0850-1005 ('+caps[1]+' slots remaining)'], ['1010-1125 ('+caps[2]+' slots remaining)'], 
        ['1300-1415 ('+caps[3]+' slots remaining)'], ['1420-1535 ('+caps[4]+' slots remaining)'], ['1540-1655 ('+caps[5]+' slots remaining)'], ['1830-1955 ('+caps[6]+' slots remaining)'],['2000-2130 ('+caps[7]+' slots remaining)']]
        update.message.reply_text(
            'What time would you like to book?\n'
            'Send /cancel to stop talking to me.\n',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )
        return CONFIRMATION
    elif update.message.text == 'Friday':
        userID = str(update.message.chat_id)
        user_info[userID].append(str(update.message.text))
        
        caps = get_slots(str(update.message.text))

        reply_keyboard = [['0730-0845 ('+caps[0]+' slots remaining)'], ['0850-1005 ('+caps[1]+' slots remaining)'], ['1010-1125 ('+caps[2]+' slots remaining)'], 
        ['1300-1415 ('+caps[3]+' slots remaining)'], ['1420-1535 ('+caps[4]+' slots remaining)'], ['1540-1655 ('+caps[5]+' slots remaining)']]
        update.message.reply_text(
            'What time would you like to book?\n'
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
        if day == 'Monday':
            booking = [UID,name, coy,timeslot]
        elif day == 'Tuesday':
            booking = [UID,name, coy,"",timeslot]
        elif day == 'Wednesday':
            booking = [UID,name, coy,"","",timeslot]
        elif day == 'Thursday':
            booking = [UID,name, coy,"","","", timeslot]
        else:
            booking = [UID,name, coy,"","","","", timeslot]
        trackingSheet.insert_row(booking)

        update.message.reply_text('Booking successful.',
        reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END
    else:
        update.message.reply_text('submission cancelled.')
        return ConversationHandler.END

def cancel(update: Update, context):
    #if user sends /cancel command, ends conversation
    #user = update.message.from_user
    #logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Byebye'
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