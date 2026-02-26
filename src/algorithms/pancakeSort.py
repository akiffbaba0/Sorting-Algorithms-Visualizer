from counters import increment_comparisons, increment_swaps

def pancakeSort(array, *args):
    """
    Sorts an array using the Pancake Sort Algorithm and yields the state of the array after each flip.

    Pancake Sort Algorithm is a sorting algorithm that works by repeatedly flipping the largest unsorted 
    element to the front of the unsorted portion of the list, and then flipping the entire unsorted portion 
    of the list to move the largest element to its correct position. This process is repeated until the entire list is sorted.

    Time complexity: O(n^2), where n is the number of elements in the list.
    """
    for i in range(len(array)):
        max_index = 0
        max_val = array[0]
        for j in range(len(array) - i):
            increment_comparisons()
            if array[j] > max_val:
                max_val = array[j]
                max_index = j
        yield array, max_index, -1, -1, -1
        flip(array, max_index)
        increment_swaps()
        yield array, 0, -1, -1, -1
        flip(array, len(array) - 1 - i)
        increment_swaps()
        yield array, -1 , -1, len(array) - 1 - i, -1


def flip(array, n):
    """
    Flips the first n elements of an array.
    """
    for i in range(n):
        if i >= n - i:
            break
        array[n - i], array[i] = array[i], array[n - i]
