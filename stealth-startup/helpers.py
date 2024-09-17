def trim_quotations(s):
    if s.startswith(('\'', '"')) and s.endswith(('\'', '"')):
        return s[1:-1]
    return s