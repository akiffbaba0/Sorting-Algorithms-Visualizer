"""
Global counters for tracking sorting algorithm operations.
Supports both single global counters and named counter instances for arena mode.
"""

# Global counters
_comparisons = 0
_swaps = 0

# Named counter instances for arena mode (e.g., 'algo1', 'algo2')
_counter_instances = {}

# Current active instance for context-based counting
_current_instance = None

def reset_counters(instance_name=None):
    """Reset both comparison and swap counters to zero.
    
    Args:
        instance_name: If provided, reset counters for that named instance.
                      If None, reset global counters.
    """
    global _comparisons, _swaps
    if instance_name is None:
        _comparisons = 0
        _swaps = 0
    else:
        _counter_instances[instance_name] = {'comparisons': 0, 'swaps': 0}

def set_current_instance(instance_name):
    """Set the current active instance for counter operations.
    
    Args:
        instance_name: Name of the instance to use, or None for global counters.
    """
    global _current_instance
    _current_instance = instance_name

def get_current_instance():
    """Get the current active instance name."""
    return _current_instance

def increment_comparisons(instance_name=None):
    """Increment the comparison counter by 1.
    
    Args:
        instance_name: If provided, increment counter for that named instance.
                      If None and a current instance is set, use current instance.
                      Otherwise increment global counter.
    """
    global _comparisons
    target = instance_name if instance_name is not None else _current_instance
    
    if target is None:
        _comparisons += 1
    else:
        if target not in _counter_instances:
            _counter_instances[target] = {'comparisons': 0, 'swaps': 0}
        _counter_instances[target]['comparisons'] += 1

def increment_swaps(instance_name=None):
    """Increment the swap counter by 1.
    
    Args:
        instance_name: If provided, increment counter for that named instance.
                      If None and a current instance is set, use current instance.
                      Otherwise increment global counter.
    """
    global _swaps
    target = instance_name if instance_name is not None else _current_instance
    
    if target is None:
        _swaps += 1
    else:
        if target not in _counter_instances:
            _counter_instances[target] = {'comparisons': 0, 'swaps': 0}
        _counter_instances[target]['swaps'] += 1

def get_comparisons(instance_name=None):
    """Get the current number of comparisons.
    
    Args:
        instance_name: If provided, get comparisons for that named instance.
                      If None and a current instance is set, use current instance.
                      If None and no current instance, get global comparisons.
    """
    target = instance_name if instance_name is not None else _current_instance
    
    if target is None:
        return _comparisons
    else:
        if target not in _counter_instances:
            return 0
        return _counter_instances[target]['comparisons']

def get_swaps(instance_name=None):
    """Get the current number of swaps.
    
    Args:
        instance_name: If provided, get swaps for that named instance.
                      If None and a current instance is set, use current instance.
                      If None and no current instance, get global swaps.
    """
    target = instance_name if instance_name is not None else _current_instance
    
    if target is None:
        return _swaps
    else:
        if target not in _counter_instances:
            return 0
        return _counter_instances[target]['swaps']

def get_counters(instance_name=None):
    """Get both counters as a tuple (comparisons, swaps).
    
    Args:
        instance_name: If provided, get counters for that named instance.
                      If None and a current instance is set, use current instance.
                      If None and no current instance, get global counters.
    """
    return get_comparisons(instance_name), get_swaps(instance_name)

def reset_all_counters():
    """Reset all counters (global and all instances)."""
    global _comparisons, _swaps
    _comparisons = 0
    _swaps = 0
    _counter_instances.clear()
