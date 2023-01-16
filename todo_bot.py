import logging
import todo_choices
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, filters

# enables logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# defines the different states of the todo bot as part of a conversation
# see conversationbot2.py on the python-telegram-bot github for ref
CHOOSING, ADD, EDIT, DELETE, EDIT_CHOICE, COMMIT_EDIT, COMMIT_DELETE = range(7)

# This will be the default keyboard with the various options:
# 1. add todo
# 2. edit todo
# 3. delete todo
# 4. view todo
reply_keyboard = [
    ['Add Todo', 'View Todo'],
    ['Edit Todo', 'Delete Todo'],
    ['Exit']
]

markup = ReplyKeyboardMarkup(
    keyboard = reply_keyboard,
    one_time_keyboard = True
)

def task_dict_to_str(task_dict):

    """Helper function to format user info"""

    task_str = [f'{key}: {value}' for key, value in task_dict.items()]
    return '\n'.join(task_str) + '\n\n'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """
    Starts the conversation and sets up the keyboard with user options.
    """

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = 'Hi there! I am a todo bot.\n' + \
            'What can I do for you today?',
        reply_markup = markup
    )

    return CHOOSING

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Asks the user to add a task"""

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = 'Add a task? Sounds good! What is your task?' + \
            '\n\nOr, press /cancel to go back to the menu.'
    )

    return ADD

async def add_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Processes the user's input and adds it into database"""

    task = update.message.text

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = f'New Task: "{task}". I will add this in!'
    )

    try:

        todo_choices.add_task(task)

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'The task has been added successfully! ' + \
                'What else would you like to do?',
            reply_markup = markup
        )
    
    except:

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Something went wrong, or the task may already exist.',
            reply_markup = markup
        )

    return CHOOSING

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Displays all tasks"""

    tasks = todo_choices.view_tasks()

    if not tasks:    # empty list

        text = 'You have not added any tasks. Add some before viewing!'

    else:

        text = 'Your saved tasks:\n\n'

        for task in tasks:

            text += task_dict_to_str(task)

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = text,
        reply_markup = markup
    )

    return CHOOSING

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Allows the user to choose tasks to edit"""

    tasks = todo_choices.view_tasks()

    if not tasks:    # empty list

        text = 'You have not added any tasks. Add some before editing!'

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = text,
            reply_markup = markup
        )

        return CHOOSING

    else:

        task_list = [[task['TaskName'] for task in tasks]]
        tasks_keyboard = ReplyKeyboardMarkup(
            keyboard = task_list,
            one_time_keyboard = True
        )

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Editing? Which task would you like to edit?' + \
                '\n\nOr, press /cancel to go back to the menu.',
            reply_markup = tasks_keyboard
        )

        return EDIT

async def choose_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Choose what to edit"""

    # save the user's choice temporarily in a chat-based dictionary
    user_data = context.user_data
    user_data['task_name'] = update.message.text

    markup = ReplyKeyboardMarkup(
        keyboard = [['Task Name', 'Status']],
        one_time_keyboard = True
    )

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = 'Choose which values to update!' + \
            '\n\nOr, press /cancel to go back to the menu.',
        reply_markup = markup
    )

    return EDIT_CHOICE

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Asks the user to provide the newly edited task name"""

    user_data = context.user_data
    user_data['edit_choice'] = 'TaskName'

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = f'Enter the new task name for "{user_data["task_name"]}".' + \
            '\n\nOr, press /cancel to go back to the menu.',
    )

    return COMMIT_EDIT

async def edit_status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Asks the user to provide the newly edited status"""

    user_data = context.user_data
    user_data['edit_choice'] = 'Status'

    markup = ReplyKeyboardMarkup(
        keyboard = [['Completed', 'Incomplete']],
        one_time_keyboard = True
    )

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = f'Choose a new status for "{user_data["task_name"]}".' + \
            '\n\nOr, press /cancel to go back to the menu.',
        reply_markup = markup
    )

    return COMMIT_EDIT

async def process_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Commits the edit based on the selected options"""

    new_value = update.message.text
    user_data = context.user_data

    try:
        
        # update database
        todo_choices.edit(
            user_data['task_name'],
            user_data['edit_choice'],
            new_value
        )

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Edit is complete! What would you like to do now?',
            reply_markup = markup
        )

    except:

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Something went wrong with the edit. ' + \
                'Duplicate tasks might have occurred',
            reply_markup = markup
        )

    # clears stored data for edits after edit process is finished
    user_data.clear()

    return CHOOSING

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Allows the user to delete tasks"""

    tasks = todo_choices.view_tasks()

    if not tasks:    # empty list

        text = 'You have not added any tasks. Add some before deleting!'

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = text,
            reply_markup = markup
        )

        return CHOOSING

    else:

        task_list = [[task['TaskName'] for task in tasks]]
        tasks_keyboard = ReplyKeyboardMarkup(
            keyboard = task_list,
            one_time_keyboard = True
        )

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Deleting? Which task would you like to delete?' + \
                '\n\nOr, press /cancel to go back to the menu.',
            reply_markup = tasks_keyboard
        )

        return DELETE

async def confirm_del(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Asks the user for confirmation to delete task"""

    user_data = context.user_data
    user_data['task_name'] = update.message.text

    markup = ReplyKeyboardMarkup(
        keyboard = [['Yes', 'No']],
        one_time_keyboard = True
    )

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = f'Are you sure you want to delete "{user_data["task_name"]}"?' + \
            '\n\nOr, press /cancel to go back to the menu.',
        reply_markup = markup
    )

    return COMMIT_DELETE

async def process_del(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Commits the deletion based on user selection"""

    choice = update.message.text

    if choice == 'No':

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = f'No worries! What do you want to do now?',
            reply_markup = markup
        )

    else:

        user_data = context.user_data
        task_name = user_data['task_name']

        todo_choices.delete(task_name)

        user_data.clear()

        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = f'Deletion successful! What do you want to do now?',
            reply_markup = markup
        )

    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Command to allow user to cancel process and return to menu"""

    user_data = context.user_data
    user_data.clear()

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = 'Alright! What would you like to do now?',
        reply_markup = markup
    )

    return CHOOSING

async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Ends and exits the conversation immediately"""

    # clear user_data
    user_data = context.user_data
    user_data.clear()

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = 'Thanks for using me! Press /start to use me again 😋😋',
        reply_markup = ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main():

    """Runs the application"""

    # create application and pass in bot token
    TOKEN = "5699172169:AAE30agPT1rbtXDFrVYuSv5D7IMZwCE6BkM"    # change this to the actual one after tests are done
    app = ApplicationBuilder().token(TOKEN).build()

    # add in conversation handler with the various states
    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start)],
        states = {
            CHOOSING: [
                MessageHandler(
                    filters = filters.Regex("^Add Todo$"),
                    callback = add
                ),
                MessageHandler(
                    filters = filters.Regex("^View Todo$"),
                    callback = view
                ),
                MessageHandler(
                    filters = filters.Regex("^Edit Todo$"),
                    callback = edit
                ),
                MessageHandler(
                    filters = filters.Regex("^Delete Todo$"),
                    callback = delete
                )
            ],
            ADD: [
                MessageHandler(
                    filters = filters.TEXT & ~(filters.COMMAND | filters.Regex("^Exit$")),
                    callback = add_todo
                )
            ],
            EDIT: [
                MessageHandler(
                    filters = filters.TEXT & ~(filters.COMMAND | filters.Regex("^Exit$")),
                    callback = choose_edit
                )
            ],
            EDIT_CHOICE: [
                MessageHandler(
                    filters = filters.Regex("^Task Name$"),
                    callback = edit_name
                ),
                MessageHandler(
                    filters = filters.Regex("^Status$"),
                    callback = edit_status
                )
            ],
            COMMIT_EDIT: [
                MessageHandler(
                    filters = filters.TEXT & ~(filters.COMMAND | filters.Regex("^Exit$")),
                    callback = process_edit
                )
            ],
            DELETE: [
                MessageHandler(
                    filters = filters.TEXT & ~(filters.COMMAND | filters.Regex("^Exit$")),
                    callback = confirm_del
                )
            ],
            COMMIT_DELETE: [
                MessageHandler(
                    filters = filters.Regex("^(Yes|No)$"),
                    callback = process_del
                )
            ]
        },
        fallbacks = [
            MessageHandler(
                filters = filters.Regex("^Exit$"),
                callback = exit
            ),
            CommandHandler('cancel', cancel)
        ]
    )

    app.add_handler(conv_handler)

    # run the bot until ctrl-c
    app.run_polling()

if __name__ == '__main__':

    main()