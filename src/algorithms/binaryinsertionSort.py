from counters import increment_comparisons, increment_swaps

def binaryinsertionSort(array, *args):
    """
    Binary insertion sort is an optimized version of insertion sort that uses binary search 
    to find the position to insert the current element in the sorted sublist.

    Time complexity: O(n log n)

    Example:
        >>> array = [5, 2, 4, 6, 1, 3]
        >>> list(binaryinsertionSort(array))
        ([5, 2, 4, 6, 1, 3], 0, 0, 0, 0)
        ([2, 5, 4, 6, 1, 3], 1, 1, 0, 1)
        ([2, 4, 5, 6, 1, 3], 1, 2, 1, 2)
        ([2, 4, 5, 6, 1, 3], 2, 2, 1, 3)
        ([1, 2, 4, 5, 6, 3], 0, 3, 1, 4)
        ([1, 2, 3, 4, 5, 6], 0, 4, 2, 5)
    """
    for i in range(1, len(array)):
        val = array[i]
        j = binary_search(array, val, 0, i - 1)
        yield array, 0, i-1, j, i
        # Count swaps for shifting elements
        for k in range(i, j, -1):
            array[k] = array[k-1]
            increment_swaps()
        array[j] = val


def binary_search(arr, val, start, end):
    """
    Binary search is an efficient search algorithm 
    for finding a target value in a sorted list or array 
    by repeatedly dividing the search interval in half, 
    resulting in a time complexity of O(log n) in the worst case.

    Example:
        >>> arr = [1, 2, 4, 5, 6]
        >>> binary_search(arr, 3, 0, 4)
        2
    """
    if start == end:
        increment_comparisons()
        if arr[start] > val:
            return start
        else:
            return start + 1

    if start > end:
        return start

    mid = round((start + end) / 2)
    increment_comparisons()
    if arr[mid] < val:
        return binary_search(arr, val, mid + 1, end)
    elif arr[mid] > val:
        return binary_search(arr, val, start, mid - 1)
    else:
        return mid
