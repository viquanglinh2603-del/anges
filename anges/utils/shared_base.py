import os
DATA_DIR = "~/.anges/data/event_streams"

def get_data_dir():
    """Get the current data directory, allowing for runtime override"""
    data_dir = os.getenv('ANGES_EVENT_STREAM_DATA_DIR', DATA_DIR)
    return os.path.expanduser(data_dir)
