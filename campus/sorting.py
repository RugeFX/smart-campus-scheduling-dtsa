# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
def manual_merge_sort(values, key=None):
    """Stable merge sort buatan tim; O(n log n) waktu, O(n) ruang."""
    result = list(values)
    key = (lambda item: item) if key is None else key
    width, n = 1, len(result)
    while width < n:
        merged = []
        for start in range(0, n, width * 2):
            middle, end = min(start + width, n), min(start + width * 2, n)
            left, right = start, middle
            while left < middle and right < end:
                if key(result[left]) <= key(result[right]):
                    merged.append(result[left]); left += 1
                else:
                    merged.append(result[right]); right += 1
            merged.extend(result[left:middle]); merged.extend(result[right:end])
        result, width = merged, width * 2
    return result
