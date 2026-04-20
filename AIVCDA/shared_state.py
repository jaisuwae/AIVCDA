import queue

# Queues for cross-thread communication between Background Voice loop and Main GUI loop
dialog_queue = queue.Queue()
response_queue = queue.Queue()

# Global states
gemini_enabled = True
cage_protocol = True
health_warning = ""

# Session tracking
quota_message_played = False
pending_action = None # For multi-step flows like confirmation
pending_data = {}    # Stores context for the pending action

# Assistant thread status
is_running = False

# Multi-task queue
task_queue = []
