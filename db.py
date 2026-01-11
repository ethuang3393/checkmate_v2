import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_user_by_name(user_name):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM public.users WHERE user_name = %s", (user_name,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def create_user(user_id, user_name):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO public.users (user_id, user_name) VALUES (%s, %s)", (user_id, user_name))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def save_list_and_tasks(user_id, list_id, list_name, tasks_data):
    """
    Saves the list and its subtasks in a transaction.
    tasks_data is a list of tuples: (task_id, description)
    """
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        
        # 1. Insert List
        cur.execute(
            "INSERT INTO public.todolists (list_id, user_id, list_name) VALUES (%s, %s, %s)",
            (list_id, user_id, list_name)
        )

        # 2. Insert Tasks
        for task_id, desc in tasks_data:
            cur.execute(
                "INSERT INTO public.tasks (task_id, list_id, task_description, is_completed) VALUES (%s, %s, %s, %s)",
                (task_id, list_id, desc, False)
            )
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving list: {e}")
        if conn: conn.rollback()
        return False

def get_user_lists_with_tasks(user_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Fetch all lists for user
        cur.execute("SELECT * FROM public.todolists WHERE user_id = %s", (user_id,))
        lists = cur.fetchall()
        
        result = []
        for lst in lists:
            # Fetch tasks for each list
            cur.execute("SELECT * FROM public.tasks WHERE list_id = %s", (lst['list_id'],))
            tasks = cur.fetchall()
            
            result.append({
                'list_id': lst['list_id'],
                'list_name': lst['list_name'],
                'tasks': tasks
            })
            
        cur.close()
        conn.close()
        # Sort by creation logic (or reverse order of insertion/display) if needed
        return result
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

# ... (Keep existing imports and functions)

def delete_task(task_id):
    """
    Deletes a single task by ID.
    """
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM public.tasks WHERE task_id = %s", (task_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting task: {e}")
        return False

def delete_list(list_id):
    """
    Deletes a list AND all its associated tasks (Manual Cascade).
    """
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        
        # 1. Delete tasks associated with this list first
        cur.execute("DELETE FROM public.tasks WHERE list_id = %s", (list_id,))
        
        # 2. Delete the list itself
        cur.execute("DELETE FROM public.todolists WHERE list_id = %s", (list_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting list: {e}")
        if conn: conn.rollback()
        return False

def toggle_task_status(task_id, is_completed):
    """
    Toggles the is_completed boolean for a specific task.
    """
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        # Toggle the boolean value
        cur.execute(
            "UPDATE public.tasks SET is_completed = %s WHERE task_id = %s", 
            (is_completed, task_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating task status: {e}")
        return False