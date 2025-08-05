from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    send_from_directory,
    Response
)
from functools import wraps
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
from datetime import timedelta
import queue
from concurrent.futures import ThreadPoolExecutor
import logging
import secrets
import argparse
from collections import defaultdict
from anges.agents.agent_utils.events import Event, EventStream
from anges.utils.event_storage_service import event_storage_service as event_storage
from anges.web_interface.agent_runner import run_agent_task
from anges.config import config

# Global variables
message_queue_dict = defaultdict(queue.Queue)
login_manager = LoginManager()
current_event_stream = None  # Will store the single EventStream
interrupt_flags = {}
active_tasks = {}  # Dictionary to track active tasks for each chat ID

# Function to set the web interface password
def set_password(password):
    """
    Set the password for the web interface.

    Args:
        password (str): The password to set for authentication
    """
    global APP_PASSWORD
    APP_PASSWORD = password

# Default password for testing
APP_PASSWORD = "test_password"

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Add a file handler for debugging
debug_handler = logging.FileHandler("/tmp/web_interface_debug.log")
debug_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
debug_handler = logging.FileHandler("/tmp/web_interface_debug.log")
debug_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return str(self.id)

def format_complete_message(events=None):
    logger.debug("Formatting complete message")
    events_dict = [event.to_dict() for event in events] if events else None
    return json.dumps(
        {"type": "complete", "content": "Task completed", "events": events_dict}
    )

def format_agent_message(message):
    """Format regular agent messages for SSE streaming"""
    return json.dumps({"type": "message", "content": message})

def init_app(password=None):
    global APP_PASSWORD, app
    # Add custom unauthorized handler for API requests
    def unauthorized_handler():
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        return redirect(url_for('login'))

    login_manager.unauthorized_handler(unauthorized_handler)

    # Create custom API login required decorator
    def api_login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if app.config.get('LOGIN_DISABLED', False):
                return f(*args, **kwargs)
            if not current_user.is_authenticated:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            return f(*args, **kwargs)
        return decorated_function

    if password:
        APP_PASSWORD = password

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session lifetime to 7 days
    app.config['SESSION_PERMANENT'] = True
    app.secret_key = config.web_interface.secret_key

    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User(user_id)

    @app.route("/api/auth", methods=["POST"])
    def api_auth():
        try:
            data = request.get_json()
            password = data.get("password")
            if password == APP_PASSWORD:
                user = User(1)
                login_user(user)
                session["user_id"] = "testuser"
                return jsonify({"status": "success", "token": session["user_id"]})
            return jsonify({"status": "error", "message": "Invalid password"}), 401
        except Exception as e:
            logger.error(f"API auth error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/login", methods=["GET", "POST"])
    def login():
        global current_event_stream
        if request.method == "POST":
            password = request.form.get("password")
            if password == APP_PASSWORD:
                user = User(1)
                login_user(user)
                session["user_id"] = "testuser"
                
                # Initialize or load event stream from storage
                if current_event_stream is None:
                    # Try to load existing event stream
                    stream_ids = event_storage.list_streams()
                    if stream_ids:
                        # Load the first available event stream
                        current_event_stream = event_storage.load(stream_ids[0])
                    
                    # If no existing stream or loading failed, create new one
                    if current_event_stream is None:
                        current_event_stream = EventStream()
                        event_storage.save(current_event_stream)
                
                logger.debug(f"New session created: {session['user_id']}")
                return redirect(url_for("home"))
            return render_template("login.html", error="Invalid password")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        session.clear()
        logout_user()
        return redirect(url_for("login"))

    @app.route("/")
    # @login_required
    def home():
        return render_template("chat.html")

    @app.route("/submit/<chat_id>", methods=["POST"])
    @api_login_required
    def submit(chat_id):
        # global current_event_stream
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid session"}), 400

        current_event_stream = event_storage.load(chat_id)
        data = request.json
        message = data.get("message")
        cmd_init_dir = data.get("cmd_init_dir", ".")
        model = data.get("model", "agent_default")  # Default to agent config
        prefix_cmd = data.get("prefix_cmd", "")  # Default to empty string if not specified
        agent_type = data.get("agent_type", "default")  # Default to original agent if not specified
        notes = data.get("notes", [])  # Default to empty list if not specified

        logger.debug(f"Received submit request with message: {message} and agent_type: {agent_type}")

        # Store agent settings in the event stream
        if current_event_stream:
            current_event_stream.agent_settings = {
                "cmd_init_dir": cmd_init_dir,
                "model": model,
                "prefix_cmd": prefix_cmd,
                "agent_type": agent_type,
                "notes": notes
            }
            event_storage.save(current_event_stream)
        
        message_queue = message_queue_dict[current_event_stream.uid]
        # Clear the queue for new messages
        while not message_queue.empty():
            message_queue.get()

        # Mark this chat as having an active task
        active_tasks[chat_id] = True
        logger.debug(f"Marked chat {chat_id} as having an active task")

        # Use ThreadPoolExecutor for better thread management
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(run_agent_task,
                      message,
                      current_event_stream,
                      message_queue,
                      interrupt_flags,
                      chat_id,
                      cmd_init_dir,
                      model,
                      prefix_cmd,
                      agent_type,
                      notes)
        return jsonify({"status": "success"}), 200

    @app.route("/new-chat")
    @api_login_required
    def new_chat():
        global current_event_stream
        # Create new empty event stream
        current_event_stream = EventStream()
        # Save to persistent storage
        event_storage.save(current_event_stream)
        logger.debug("Created new chat")
        return jsonify({"status": "success", "chat_id": current_event_stream.uid})

    @app.route("/list-chats")
    # @login_required
    def list_chats():
        try:
            stream_ids = event_storage.list_streams()
            chats = {}
            for stream_id in stream_ids:
                stream = event_storage.load(stream_id)
                if stream:
                    title = stream.title if hasattr(stream, 'title') and stream.title else "<no title>"
                    created_at = stream.created_at if hasattr(stream, 'created_at') else None
                    chats[stream_id] = {
                        "stream_id": stream_id,
                        "title": title,
                        "created_at": created_at
                    }
            return jsonify({"status": "success", "chats": chats})
        except Exception as e:
            logger.error(f"Error listing chats: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/load-chat/<chat_id>")
    # @login_required
    def load_chat(chat_id):
        # global current_event_stream
        try:
            current_event_stream = event_storage.load(chat_id)
            if current_event_stream is None:
                return jsonify({"status": "error", "message": "Chat not found"}), 404
            all_events = current_event_stream.get_event_list_including_children_events()
            total_est_token_input = 0
            total_est_token_output = 0
            for e in all_events:
                total_est_token_input += e.est_input_token
                total_est_token_output += e.est_output_token
            return jsonify({
                "status": "success",
                "est_input_token": total_est_token_input,
                "est_output_token": total_est_token_output,
                "agent_settings": current_event_stream.agent_settings,
                "events": [{"type": event.type, "message": event.message } for event in all_events]
            })
        except Exception as e:
            logger.error(f"Error loading chat {chat_id}: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/interrupt/<chat_id>", methods=["POST"])
    @api_login_required
    def interrupt(chat_id):
        interrupt_flags[chat_id] = True
        logger.debug(f"Set interrupt flag for chat {chat_id}")
        return jsonify({"status": "success"})

    @app.route("/edit-chat/<chat_id>", methods=["POST"])
    @login_required
    def edit_chat(chat_id):
        try:
            data = request.json
            new_title = data.get("title")
            if not new_title:
                return jsonify({"status": "error", "message": "Title is required"}), 400
            event_storage.update_stream_title(chat_id, new_title)
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error editing chat {chat_id}: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/stream/<chat_id>")
    @api_login_required
    def stream(chat_id):
        # global current_event_stream
        current_event_stream = event_storage.load(chat_id)
        message_queue = message_queue_dict[current_event_stream.uid]
        user_id = session.get("user_id")
        logger.debug(f"Started streaming for user {user_id}")
        
        def generate():
            while True:
                message = message_queue.get()  # This will block until a message is available
                if message == "STREAM_COMPLETE":
                    break
                yield f"data: {format_agent_message(message)}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/delete-chat/<chat_id>", methods=["POST"])
    @api_login_required
    def delete_chat(chat_id):
        try:
            event_storage.delete_stream(chat_id, recursive=True)
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error deleting chat {chat_id}: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/favicon.ico")
    def favicon():
        try:
            return send_from_directory("static", "favicon.ico")
        except Exception as e:
            logger.error(f"Error serving favicon: {str(e)}")
            return str(e), 500
            
    @app.route("/check_stream/<chat_id>")
    @api_login_required
    def check_stream(chat_id):
        """
        Check if a chat has an active task.
        
        Args:
            chat_id (str): The ID of the chat to check
            
        Returns:
            JSON response with the status of the task
        """
        try:
            # Check if the chat exists
            stream = event_storage.load(chat_id)
            if stream is None:
                return jsonify({"status": "error", "message": "Chat not found"}), 404
                
            # Check if the chat has an active task
            is_active = active_tasks.get(chat_id, False)
            logger.debug(f"Checking if chat {chat_id} has an active task: {is_active}")
            
            return jsonify({
                "status": "success",
                "has_active_task": is_active
            })
        except Exception as e:
            logger.error(f"Error checking stream status for chat {chat_id}: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    return app


def main():
    """
    Parse command-line arguments and run the web interface.

    This function is the entry point when running the web interface directly.
    """
    parser = argparse.ArgumentParser(description="Run the AI Agent Web Interface")
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to run the server on"
    )
    parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="Password for accessing the interface",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the server on (127.0.0.1 or 0.0.0.0)",
    )

    args = parser.parse_args()

    # Initialize the app with the provided password
    app = init_app(args.password)

    # Run the app
    run_app(app, host=args.host, port=args.port)


def run_app(app, host="127.0.0.1", port=5000, debug=True):
    """
    Run the Flask application with the specified parameters.

    This function can be called programmatically to run the web interface.

    Args:
        app: The Flask application instance
        host: Host address to bind (default: "127.0.0.1")
        port: Port number to listen on (default: 5000)
        debug: Whether to run in debug mode (default: True)
    """
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()

# Initialize the app with default settings for testing
app = init_app()
