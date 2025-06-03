from flask import Flask, render_template, jsonify, request
from jarvis import Jarvis

app = Flask(__name__, 
           template_folder='jarvis/templates',
           static_folder='jarvis/static')
system = Jarvis()  # Initialize our System

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', 
                         stats=system.stats,
                         rank_requirements=system.rank_requirements,
                         tasks=system.tasks)

@app.route('/api/stats')
def get_stats():
    """Get current stats"""
    return jsonify(system.stats)

@app.route('/api/tasks')
def get_tasks():
    """Get all tasks"""
    return jsonify([task.to_dict() for task in system.tasks])

@app.route('/api/complete_task', methods=['POST'])
def complete_task():
    """Complete a task"""
    task_index = request.json.get('task_index')
    if task_index is not None:
        try:
            system.complete_task(task_index)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'No task index provided'})

@app.route('/api/suggest_tasks')
def suggest_tasks():
    """Get task suggestions"""
    system.suggest_tasks()
    return jsonify([task.to_dict() for task in system.tasks])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002) 