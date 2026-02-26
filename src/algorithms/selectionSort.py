from counters import increment_comparisons, increment_swaps

def selectionSort(array, *args):
    """
    Sorts an array using the Selection Sort Algorithm.

    Selection Sort Algorithm works by finding the smallest element in the unsorted
    part of the array and moving it to the beginning of the unsorted part. This is
    repeated until the entire array is sorted.

    Time complexity: O(n^2), where n is the number of elements in the list. 
    """
    size = len(array)
    for i in range(size-1):
        smallIndex = i
        for j in range(i, size):
            yield array, j, -1, i, -1
            increment_comparisons()
            if array[j] < array[smallIndex]:
                smallIndex = j
        if smallIndex != i:
            array[i], array[smallIndex] = array[smallIndex], array[i]
            increment_swaps()
