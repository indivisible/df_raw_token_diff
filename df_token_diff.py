#!/usr/bin/env python3

import re
from itertools import zip_longest
from pathlib import Path
from difflib import SequenceMatcher

DEFAULT_SAFE_TOKENS = {
    'TILE',
    'T_WORD',
    'GROWTH_PRINT',
    'CREATURE_TILE',
    'TREE_TILE',
    'DEAD_TREE_TILE',
    'PICKED_TILE',
    'SHRUB_TILE',
    'DEAD_SHRUB_TILE',
    'GRASS_TILES',
    'ALT_GRASS_TILES',
    'ITEM_SYMBOL',
    'CREATURE_SOLDIER_TILE',
    }

token_re = re.compile(r'\[([^\]]*)\]')
def get_tokens(stream):
    for line in stream:
        for match in token_re.finditer(line):
            raw_token = match.group(1)
            yield tuple(raw_token.split(':'))

def diff_token_streams_old(stream_a, stream_b):
    for (a, b) in zip_longest(stream_a, stream_b):
        if a[0] != b[0]:
            raise ValueError('Token types do not match: {} <=> {}'.format(a, b))
        if a != b:
            values = []
            for x, y in zip_longest(a, b):
                if x == y:
                    values.append(str(x))
                else:
                    values.append('**{}** => **{}**'.format(x, y))
            print ('[{}]'.format(':'.join(values)))

def token_diff(a, b):
    values = []
    for x, y in zip_longest(a, b):
        if x == y:
            values.append(str(x))
        else:
            values.append('**{}** => **{}**'.format(x, y))
    return '[{}]'.format(':'.join(values))

def diff_token_streams(stream_a, stream_b, safe_tokens=DEFAULT_SAFE_TOKENS):
    list_a = list(stream_a)
    list_b = list(stream_b)
    sm = SequenceMatcher(None, list_a, list_b, False)
    lines = []
    for group in sm.get_grouped_opcodes(0):
        for op, i1, i2, j1, j2 in group:
            if op == 'equal':
                continue
            if op == 'replace':
                assert i2 - i1 == j2 - j1, 'replace OP range lengths should match'
                for offset in range(i2 - i1):
                    a = list_a[i1 + offset]
                    b = list_b[j1 + offset]
                    if a[0] in safe_tokens and b[0] in safe_tokens:
                        continue
                    lines.append('** ' + token_diff(a, b))
            elif op == 'delete':
                for i in range(i1, i2):
                    a = list_a[i]
                    if a[0] in safe_tokens:
                        continue
                    lines.append('-- [{}]'.format(':'.join(a)))
            elif op == 'insert':
                for j in range(j1, j2):
                    b = list_b[j]
                    if b[0] in safe_tokens:
                        continue
                    lines.append('++ [{}]'.format(':'.join(b)))
            else:
                raise ValueError('Unkown diff op: {} {} {} {} {}'.format(op, i1, i2, j1, j2))
    return lines

def diff_files(a, b):
    with open(a, encoding='cp437') as stream_a, open(b, encoding='cp437') as stream_b:
        lines = diff_token_streams(get_tokens(stream_a), get_tokens(stream_b))
        if lines:
            print('Comparing {} <=> {}'.format(a, b))
            print('\n'.join(lines))

def diff_dirs(a, b):
    for child in a.iterdir():
        other = b / child.name
        if child.is_file() and other.is_file() and child.suffix.lower() == '.txt':
            diff_files(child, other)
        elif child.is_dir() and other.is_dir():
            diff_dirs(child, other)

def diff_paths(a, b):
    a = Path(a)
    b = Path(b)
    assert a.is_file() == b.is_file()
    assert a.is_dir() == b.is_dir()

    if a.is_file():
        return diff_files(a, b)
    else:
        return diff_dirs(a, b)

if __name__ == '__main__':
    import sys
    diff_paths(sys.argv[1], sys.argv[2])

