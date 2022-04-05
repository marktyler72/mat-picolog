from uerrno import ENOENT, EINVAL
from micropython import const
import os

_FILE = const(0x8000)
_DIR = const(0x4000)
sep = '/'

def normcase(s):
    return s


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


def abspath(s):
    if s[0] != sep:
        cwd = os.getcwd()
        if cwd == sep:
            cwd = ''
        s =  cwd + sep + s
    return normpath(s)


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


def split(p):
    i = p.rfind(sep) + 1
    head, tail = p[:i], p[i:]
    if head and head != sep*len(head):
        head = head.rstrip(sep)
    return head, tail


def dirname(path):
    return split(path)[0]


def basename(path):
    return split(path)[1]


def exists(path):
    result = False
    try:
        if os.stat(path)[0] == _FILE:
            result = True
    except OSError as err:
        if err.errno == ENOENT:
            pass
        elif err.errno == EINVAL:
            pass        
    return result


# TODO
lexists = exists


def isdir(path):
    result = False
    try:
        if os.stat(path)[0] == _DIR:
            result = True
    except OSError as err:
        if err.errno == ENOENT:
            pass
        elif err.errno == EINVAL:
            pass
    return result


# def expanduser(s):
#     if s == "~" or s.startswith("~/"):
#         h = os.getenv("HOME")
#         return h + s[1:]
#     if s[0] == "~":
#         # Sorry folks, follow conventions
#         return "/home/" + s[1:]
#     return s