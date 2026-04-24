import queue

# Queues for cross-thread communication between Background Voice loop and Main GUI loop
dialog_queue = queue.Queue()
response_queue = queue.Queue()

# Global states
cage_protocol = True
health_warning = ""

# Session tracking
pending_action = None  # For multi-step flows like confirmation
pending_data = {}      # Stores context for the pending action

# Assistant thread status
is_running = False

# Multi-task queue
task_queue = []
