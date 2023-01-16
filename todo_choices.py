import sqlite3, datetime

def first_connection():

    """Creates database file and table"""

    conn = sqlite3.connect('todo.db')

    # creates table if table does not exist
    conn.execute(
        'CREATE TABLE IF NOT EXISTS "Todo" ("TaskName" TEXT,' + \
            '"Status" TEXT, "DateAdded" TEXT,' + \
                'PRIMARY KEY("TaskName"))'
    )

    conn.commit()
    conn.close()

def add_task(task_name):

    """Adds the task into the database"""

    conn = sqlite3.connect('todo.db')

    status = 'Incomplete'
    date_added = str(datetime.date.today())

    conn.execute(
        'INSERT INTO Todo (TaskName, Status, DateAdded) ' + \
            'VALUES (?, ?, ?)', (task_name, status, date_added)
    )

    conn.commit()
    conn.close()

def view_tasks():

    """Retrieves all tasks from the database and returns a list of dictionaries"""

    conn = sqlite3.connect('todo.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM Todo'
    )

    # empty list if there are no results
    # else list of dictionaries with table column name as keys
    results = [dict(row) for row in cursor.fetchall()]
    
    return results
    
def edit(task_name, update_field, new_value):

    """Updates the record with `task_name`"""

    conn = sqlite3.connect('todo.db')
    query = 'UPDATE Todo SET TaskName = ? WHERE TaskName = ?'  \
        if update_field == 'TaskName' else \
            'UPDATE Todo SET Status = ? WHERE TaskName = ?'

    conn.execute(query, (new_value, task_name))

    conn.commit()
    conn.close()

def delete(task_name):

    """Deletes the task with TaskName `task_name`"""

    conn = sqlite3.connect('todo.db')

    conn.execute(
        'DELETE FROM Todo WHERE TaskName = ?', (task_name,)
    )

    conn.commit()
    conn.close()

# sets up the DB if the file is run for the first time
first_connection()