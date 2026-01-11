import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash
from gemini_service import generate_subtasks
import os
# Update this specific import line to include the new functions:
from db import get_user_by_name, create_user, save_list_and_tasks, get_user_lists_with_tasks, delete_task, delete_list, toggle_task_status

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me_in_production'

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_name = request.form.get('user_name').strip()
    
    if not user_name:
        flash("Please enter a valid name.", "danger")
        return redirect(url_for('index'))

    # Check if user exists
    existing_user = get_user_by_name(user_name)
    
    if existing_user:
        session['user_id'] = existing_user['user_id']
        session['user_name'] = existing_user['user_name']
    else:
        # Create new user
        new_id = str(uuid.uuid4())
        if create_user(new_id, user_name):
            session['user_id'] = new_id
            session['user_name'] = user_name
        else:
            flash("Database error creating user.", "danger")
            return redirect(url_for('index'))
            
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_data = get_user_lists_with_tasks(session['user_id'])
    return render_template('dashboard.html', user_name=session['user_name'], todo_data=user_data)

@app.route('/create_list', methods=['POST'])
def create_list():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    list_title = request.form.get('list_title')
    if not list_title:
        flash("Please enter a to-do list title.", "warning")
        return redirect(url_for('dashboard'))
    
    # 1. Generate Sub-tasks via Gemini
    subtasks = generate_subtasks(list_title)
    
    # 2. Prepare Data for DB
    list_id = str(uuid.uuid4())
    tasks_to_save = []
    
    for desc in subtasks:
        task_id = str(uuid.uuid4())
        tasks_to_save.append((task_id, desc))
        
    # 3. Save to DB
    success = save_list_and_tasks(session['user_id'], list_id, list_title, tasks_to_save)
    
    if success:
        flash("AI Agents have planned your tasks successfully!", "success")
    else:
        flash("Failed to save tasks to database.", "danger")
        
    return redirect(url_for('dashboard'))

@app.route('/delete_list/<list_id>', methods=['POST'])
def remove_list(list_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if delete_list(list_id):
        flash("List deleted successfully.", "success")
    else:
        flash("Error deleting list.", "danger")
        
    return redirect(url_for('dashboard'))

@app.route('/delete_task/<task_id>', methods=['POST'])
def remove_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if delete_task(task_id):
        flash("Task deleted.", "success")
    else:
        flash("Error deleting task.", "danger")
        
    return redirect(url_for('dashboard'))

@app.route('/toggle_task/<task_id>', methods=['POST'])
def toggle_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get the value from the form (checkbox). 
    # If checkbox is checked, the browser sends 'on', otherwise nothing.
    # However, since we are just toggling based on a button click or JS submission, 
    # we can pass the DESIRED state or just toggle it in DB. 
    # Let's trust the frontend state sent via a hidden input or just simple logic.
    
    # Simpler approach: Receiving 'completed' as 'true' or 'false' string
    is_completed_str = request.form.get('is_completed')
    is_completed = True if is_completed_str == 'true' else False
    
    toggle_task_status(task_id, is_completed)
    
    # Stay on dashboard
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)