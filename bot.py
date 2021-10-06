from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ChatAction
import logging

from telegram.ext.conversationhandler import ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials


NAME, UNIT, DAY, TIME, CONFIRMATION, SUBMIT, CANCEL = range(7)


def correct_format(update: Update, context):
    #for any errors in submission, Bot will send this to user.
    update.message.delete()
    update.message.reply_text(
        'It seems like there was an error. \n'
        'Please type it in the appropriate format: \n\n'
        'For Name: Rank <Space> Name\n\n'
        'For Subunit: BNHQ/ALPHA/BRAVO/BOAT/SUPPORT \n\n'
        'Please input the correct format', reply_markup=ReplyKeyboardRemove() )

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, 
    text="I'm a bot, hi. Input password to continue or type /cancel to end convo.")
    return NAME

def name(update, context):
    if(update.message.text == 'pass'):
        update.message.reply_text(
        'What is your name? (Please key in as Rank <Space> Name)', reply_markup=ReplyKeyboardRemove() )
    return UNIT

def unit(update, context):
    reply_keyboard = [['BNHQ', 'ALPHA', 'BRAVO','BOAT', 'SUPPORT']]
    update.message.reply_text(
        'What subunit are you from? Please enter in CAPS.\n'
        'Enter one: BNHQ, ALPHA, BRAVO, BOAT, SUPPORT \n'
        'Send /cancel to stop talking to me.\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard),
    )
    return DAY

def day(update, context):
    reply_keyboard = [['Monday','Tuesday', 'Wednesday', 'Thursday', 'Friday']]
    update.message.reply_text(
        'What day would you like to make a booking for?\n'
        'Enter one: Monday, Tuesday, Wednesday, Thursday, Friday \n'
        'Send /cancel to stop talking to me.\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )
    return TIME

def timeslot(update: Update, context):
    if update.message.text == 'Monday'or'Tuesday'or'Wednesday'or'Thursday':
        reply_keyboard = [['0730-0845', '0850-1005', 
        '1010-1125', '1300-1415', '1420-1535', '1540-1655', '1830-1955','2000-2130']]
        update.message.reply_text(
            'What time would you like to book?\n'
            'Send /cancel to stop talking to me.\n',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )
        return CONFIRMATION
    elif update.message.text == 'Friday':
        reply_keyboard = [['0730-0845', '0850-1005', 
        '1010-1125', '1300-1415', '1420-1535', '1540-1655']]
        update.message.reply_text(
            'What time would you like to book?\n'
            'Send /cancel to stop talking to me.\n',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )
        return CONFIRMATION
    else:
        update.message.reply_text('Please enter Monday, Tuesday, Wednesday, Thursday, or Friday')
        
def confirmation(update: Update, context):
    reply_keyboard = [['Yes','No']]
    update.message.reply_text('ya sure??',
    reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )
    return SUBMIT

def submit(update: Update, context):
    if update.message.text == 'Yes':
        update.message.reply_text('submitted')
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
    # updater  = Updater(token='1956967365:AAGGWputg-LsdPN-QMix5GyFrqExkoQ3TA4', use_context = True)
    # dispatcher = updater.dispatcher
    # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #                     level=logging.INFO)
    

    # start_conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler('start', start)],
    # states={NAME: [MessageHandler(Filters.text,name)],
    # UNIT: [MessageHandler(Filters.regex('^\w+\s\.*'),unit)],
    # DAY: [MessageHandler(Filters.regex('^BNHQ$|^ALPHA$|^BRAVO$|^BOAT$|^SUPPORT$'),day)],
    # TIME: [MessageHandler(Filters.regex('^Monday$|^Tuesday$|^Wednesday$|^Thursday$|^Friday$'),timeslot)],
    # CONFIRMATION: [MessageHandler(Filters.regex('^0730-0845$|^0850-1005$|^1010-1125$|^1300-1415$|^1420-1535$|^1540-1655$|^1830-1955$|^2000-2130$'),confirmation)],
    # SUBMIT: [MessageHandler(Filters.regex('^Yes$|^yes$|^No$|^no$'), submit)]
    # },
    # fallbacks = [CommandHandler('cancel',cancel),MessageHandler(Filters.text, correct_format)]
    # )

    # dispatcher.add_handler(start_conv_handler)


    # updater.start_polling()
    #gc = gspread.service_account()
    scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive.file',
         'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("Bot Tracking").sheet1

    sheet.update('B2', "it's down there somewhere, let me take another look.")

if __name__ == '__main__':
    main()