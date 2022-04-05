import os.path as op

sep = '/'

def normpath(s):
    init_slash = s.startswith(sep)
    ns = [i for i in s.split(sep) if i not in ('','.')]

    if ns.count('..') != 0:
        tmp = []
        lvl = 0
        for itm in reversed(ns):
            if itm == '..':
                lvl += 1
            elif lvl > 0:
                lvl -= 1
            else:
                tmp.append(itm)
        tmp.reverse()
        ns = tmp
        if not init_slash and lvl > 0:
            ns = (['..'] * lvl) + ns

    s = sep.join(ns)
    if init_slash:
        s = sep + s
    elif s == '':
        s = '.'

    return s

def join(a, *p):
    path = a
    try:
        if not p:
            path[:0] + sep
        for b in p:
            if b.startswith(sep):
                path = b
            elif not path or path.endswith(sep):
                path += b
            else:
                path += sep + b
    except (TypeError, AttributeError, BytesWarning):
#        genericpath._check_arg_types('join', a, *p)
        raise
    return path

    # TODO: this is non-compliant
    if type(args[0]) is bytes:
        return b"/".join(args)
    else:
        return "/".join(args)

def split(p):
    i = p.rfind(sep) + 1
    head, tail = p[:i], p[i:]
    if head and head != sep*len(head):
        head = head.rstrip(sep)
    return head, tail

    if path == "":
        return ("", "")
    r = path.rsplit("/", 1)
    if len(r) == 1:
        return ("", path)
    head = r[0]  # .rstrip("/")
    if not head:
        head = "/"
    return (head, r[1])


test_cases = [
    '',
    '.',
    ' .',
    '..',
    '/',
    '//',
    '/..',
    'bob',
    ' bob ',
    'bob/',
    'bob//',
    '/bob',
    '//bob',
    '///bob',
    '////bob',
    '/bob/',
    '/bob/..',
    '/bob/../',
    'bob/../',
    'bob/apple',
    '/bob/apple',
    'bob/apple/',
    'bob/../apple',
    'bob/../apple',
    'bob/..apple',
    '../apple',
    '../../apple',
    '/../apple',
    '/../../apple',
    'bob/./apple',
    'bob/././apple',
    'bob/./.././apple',
    'bob/./.apple',
    'bob/apple/pear/frog/a/path',
    'bob/apple/../pear/frog/../a/path',
    'bob/apple/../pear/frog/../a/path/..',
    '../../apple/../pear/frog',
    '/../bob/apple/../pear/frog/../a/path/..',
    '../bob/../apple/../pear/frog/../a/path/..',
    ]

print('*** Testing normpath ***')
for path in test_cases:
    r1 = normpath(path)
    r2 = op.normpath(path)

    if r1 != r2:
        print('Test case fail: "',path,'"')
        print('os_path: ',r1)
        print('os.path: ',r2)

print('*** Testing split ***')
for path in test_cases:
    r1 = split(path)
    r2 = op.split(path)

    if r1 != r2:
        print('Test case fail: "',path,'"')
        print('os_path: ',r1)
        print('os.path: ',r2)
    
print('*** Testing join ***')
for path in test_cases:
    head, tail = split(path)
    r1 = join(head)
    r1 = join(head, tail)
    r2 = op.join(head, tail)

    if r1 != r2:
        print('Test case fail: "',path,'"')
        print('os_path: ',r1)
        print('os.path: ',r2)