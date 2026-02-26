import random
from random import randint
from counters import increment_comparisons, increment_swaps

def quickSort(array, left, right):
    """
    QuickSort works by selecting a pivot element from the array and partitioning the other 
    elements into two sub-arrays, according to whether they are less than or greater 
    than the pivot. The process is then repeated on the two sub-arrays until the sub-arrays 
    contain only one element or are empty. The sub-arrays are then combined to form the final 
    sorted array. 

    Time complexity: O(nlog²n).
    """
    if left >= right:
        return
    index = left
    random_index = randint(left, right)
    array[right], array[random_index] = array[random_index], array[right]
    increment_swaps()
    
    for j in range(left, right):
        yield array, j, right, index, -1
        increment_comparisons()
        if array[j] < array[right]:
            array[j], array[index] = array[index], array[j]
            increment_swaps()
            index += 1
    array[index], array[right] = array[right], array[index]
    increment_swaps()
    yield from quickSort(array, index + 1, right)
    yield from quickSort(array, left, index - 1)
