def trunc(s, max, left=0):
    """
    Convert `s` to string, eliminate newlines and truncate the string to `max`
    characters. If there are more characters in the string add ``...`` to the
    string. With `left=True`, the string can be truncated at the beginning.

    >>> trunc('This is a long text.', 8)
    This ...
    >>> trunc('This is a long text.', 8, left)
    ...text.
    """
    s = str(s)
    s = s.replace('\n', '|')
    if len(s) > max:
        if left:
            return '...'+s[len(s)-max+3:]
        else:
            return s[:(max-3)]+'...'
    else:
        return s

def pp(i, base=1024):
    """
    Pretty-print the integer `i` as a human-readable size representation.
    """
    degree = 0
    pattern = "%4d     %s"
    while i > base:
        pattern = "%7.2f %s"
        i = i / float(base)
        degree += 1
    scales = ['B', 'KB', 'MB', 'GB', 'TB', 'EB']
    return pattern % (i, scales[degree])

def pp_timestamp(t):
    """
    Get a friendly timestamp represented as a string.
    """
    if t is None: 
        return ''
    h, m, s = int(t / 3600), int(t / 60 % 60), t % 60
    return "%02d:%02d:%05.2f" % (h, m, s)

