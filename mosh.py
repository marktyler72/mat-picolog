from sys import exit
from usys import print_exception
from micropython import const
from machine import SPI, Pin
import os
import os_path
import mpy_utils

_FILE = const(0x8000)
_DIR = const(0x4000)

class Mosh():
    def __init__(self):
        self._sd = mpy_utils.SDVolume()
        self._sd.mount("/sd")
        print("SD card mounted on /sd")
        self._go()

    def _exit(self, args):
        self._sd.umount()
        print("SD card unmounted")
        exit()
        
    def cat(self, args):
        if len(args) > 0:
            path = os_path.abspath(args[0])
            if os_path.exists(path):
                with open(path, "r") as f:
                    for line in f:
                        print(line, end='')

    def cd(self, args):
        if len(args) > 0:
            path = os_path.abspath(args[0])
            if os_path.isdir(path):
                os.chdir(path)
            else:
                print("?? Cannot change directory to ", path)

    def pwd(self, args):
        print(os.getcwd())
        
    def ls(self, args):
        if len(args) == 0:
            path = os.getcwd()
        else:
            path = args[0]
        path = os_path.abspath(path)
        if os_path.isdir(path):
            dir_lister = os.ilistdir(path)
            for dir_entry in dir_lister:
                fname = dir_entry[0]

                if dir_entry[1] == _DIR:
                    fname = fname + '/'
                    fsize = "        "
                else:
                    fsize = str(dir_entry[3])
                print(fsize + "  " + fname)
        elif os_path.exists(path):
            info = os.stat(path)
            fname = os_path.basename(path)
            print(str(info[6]) + "  " + fname)

    def mkdir(self, args):
        for arg in args:
            path = os_path.abspath(arg)
            print("Creating ", path)
            try:
                os.mkdir(path)
            except OSError:
                print("?? Could not create ", path)

    def rmdir(self, args):
        for arg in args:
            path = os_path.abspath(arg)
            print("Removing ", path)
            try:
                os.rmdir(path)
            except OSError as err:
                print(err.errno, err.strerror)
                print("?? Could not remove ", path)

    def rm(self, args):
        for arg in args:
            path = os_path.abspath(arg)
            if os_path.exists(path):
                print("Deleting ", path)
                try:
                    os.remove(path)
                except OSError:
                    print("?? Could not remove ", path)

    def mv(self, args):
        if len(args) == 2:
            old_path = os_path.abspath(args[0])
            new_path = os_path.abspath(args[1])
            if os_path.exists(old_path):
                if os_path.isdir(new_path):
                    new_path = os_path.join(new_path, os_path.basename(old_path))
                print("Moving ", old_path, ' to ', new_path)
                try:
                    os.rename(old_path, new_path)
                except OSError:
                    print("?? Could not find ", old_path)

    def cp(self, args):
        if len(args) == 2:
            src = os_path.abspath(args[0])
            dst = os_path.abspath(args[1])
            if os_path.exists(src):
                if os_path.isdir(dst):
                    dst = os_path.join(dst, os_path.basename(src))
                if src != dst:
                    if os_path.exists(dst):
                        ans = input("cp: overwrite '" + dst + "'? ")
                        if ans.lower() != 'y':
                            return
                    print('Copying ', src, ' to ', dst, ' ',end='')
                    try:
                        with open(src,'rb') as src_f:
                            with open(dst, 'wb') as dst_f:
                                buf = bytearray(20*1024)
                                done = False
                                cnt = 0
                                spin = ['|','/','-','\\']
                                i = 0
                                while not done:
                                    n = src_f.readinto(buf)
                                    if n is None or n == 0:
                                        done = True
                                    else:
                                        b_out = dst_f.write(buf[:n])
                                        cnt += 1
                                        if cnt > 4:
                                            print('\b\b',spin[i],end='')
                                            i += 1
                                            if i > 3:
                                                i = 0
                                            cnt = 0
                                        if b_out != n:
                                            print("\n?? Could only write ",b_out)
                                            done = True
                        print(" Done")
                    except Exception as err:
                        print_exception(err)
                        print("?? Error copying.")

    def fsinfo(self, args):
        try:
            if len(args) == 0:
                fs_path = '/'
            else:
                fs_path = os_path.abspath(args[0])
            info = os.statvfs(fs_path)
            fs_size = info[0]*info[2]
            fs_free = info[0]*info[3]
            fs_used = fs_size - fs_free
            human_vals = mpy_utils.format_human((fs_size, fs_used, fs_free))
            print("File system: {0}\n  Size: {1:,} ({2:s}), Used: {3:,} ({4:s}), Free: {5:,} ({6:s})".format( \
                    fs_path, fs_size, human_vals[0], fs_used, human_vals[1], fs_free, human_vals[2]))
        except OSError:
            pass

    def mem_info(self, args):
        import micropython
        micropython.mem_info(True)

    def _go(self):
        command_table = {
            'cat': self.cat,
            'ls': self.ls,
            'cd': self.cd,
            'pwd': self.pwd,
            'mkdir': self.mkdir,
            'rmdir': self.rmdir,
            'mv': self.mv,
            'cp': self.cp,
            'rm': self.rm,
            'fsinfo': self.fsinfo,
            'mem_info': self.mem_info,
            'exit': self._exit,
        }

        try:
            while True:
                try:
                    inp = input("$ ")
                except EOFError:
                    self._exit(None)
                parts = inp.strip().split(None, 1)
                if len(parts) > 0:
                    cmd = parts[0]
                    if len(parts) > 1:
                        args = (parts[1]).strip().split()
                    else:
                        args = []

                    try:
                        command_table[cmd](args)
                    except KeyError:
                        print("?? Unknown command")
        except KeyboardInterrupt:
            self._exit(None)
        except Exception as err:
            print("Caught exception ", repr(err), str(err))
            self._exit(None)
