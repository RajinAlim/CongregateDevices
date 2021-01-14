import math
import re
import datetime
import os

from src.python import configs
from src.python.configs import logger
from socket import gethostname
from socket import gethostbyname


def decimal(num: str, base: int=2):
    
    dec = 0
    negative = False
    for pow, n in enumerate(num[::-1]):
        if n.isalpha():
            n = 10 + (ord(n.upper()) - 65)
        else:
            n = int(n)
        k = n * (base ** pow)
        dec += k
    if negative:
        dec *= -1
    return dec

def non_decimal(dec: int, base: int=2):
    
    non_dec = ""
    negative = False
    dec = int(dec)
    while dec != 0:
        k = dec % base
        dec = dec // base
        if k > 9:
            l = chr(65 + (k - 10))
            non_dec += l
        else:
            non_dec += str(k)
    non_dec = non_dec[::-1]
    if negative:
        non_dec = "-" + non_dec
    return non_dec

def get_id(addr: tuple):
    
    ip, port = addr
    ip = ["{:0>3}".format(part) for part in ip.split(".")]
    ip = "".join(ip)
    as_str = "{}{:0>5}".format(ip, port)
    as_int = int(as_str)
    digits = list(non_decimal(as_int, 36))
    digits.insert(3, " ")
    digits.insert(8, " ")
    key = "".join(digits)
    return key
    
def get_addr(key: str):
    
    key = key.replace(" ", "").upper()
    addr = str(decimal(key, 36))
    ip, port = addr[:-5], addr[-5:]
    port = int(port)
    ip_parts = ip[:3], ip[3:6], ip[6:9], ip[9:]
    ip_parts = map(int, ip_parts)
    ip_parts = map(str, ip_parts)
    ip = ".".join(ip_parts)
    return ip, port

def min_ip(ip1, ip2):
    
    if ip1 == ip2:
        return ip1
    if not ip1 or not all(c.isdigit() or c == "." for c in ip1):
        return ip2
    if not ip2 or not all(c.isdigit() or c == "." for c in ip2):
        return ip1
    ip1 = ip1.strip()
    ip2 = ip2.strip()
    ip1_parts = map(int, ip1.split("."))
    ip2_parts = map(int, ip2.split("."))
    for ip1_part, ip2_part in zip(ip1_parts, ip2_parts):
        if ip1_part == ip2_part:
            continue
        return ip1 if ip1_part < ip2_part else ip2

def pretify_time(seconds):
    
    seconds = int(seconds)
    hours, minutes = 0, 0
    if seconds >= 60:
        minutes = seconds // 60
        seconds = seconds % 60
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
    as_str = ''
    if hours > 0:
        as_str += f"{hours} hour"
        as_str = as_str + 's' if hours > 1 else as_str
        as_str += " "
    if minutes > 0 or hours > 0:
        as_str += f"{minutes} minute"
        as_str = as_str + 's' if minutes > 1 else as_str
        as_str += " "
    as_str += f"{seconds} second"
    as_str = as_str + 's' if seconds > 1 else as_str
    return as_str

def pretify(m):
    
    try:
        m = float(int(m))
    except:
        return "0 byte"
    measures = ['byte', 'kb', 'mb', 'gb']
    i = 0
    while m and m >= (i + 1) * 1024:
        m = m / 1024
        i += 1
        if i >= 3:
            break
    return f"{round(m, 2) if not m.is_integer() else int(m)} {measures[i]}"

def pretify_path(path):
    if path.startswith("/storage"):
        if "/storage/emulated/0" in path:
            path = path.replace("/storage/emulated/0", "Internal Storage", 1)
        else:
            path = os.path.join("SD Card", *split_path(path)[3:])
    return path

def split_path(path):
    
    splited = os.path.split(path)
    paths = list()
    while splited[1]:
        path, base = splited
        if base not in paths:
            paths.append(base)
        splited = os.path.split(path)
    if splited:
        paths.append(splited[0])
    paths.reverse()
    return paths

def traverse_dir(path: str, depth=-1):
    prev_wd = os.getcwd()
    try:
        os.chdir(path)
        items = os.listdir()
    except:
        items = []
    
    for f in items:
        if os.path.isfile(f):
            yield os.path.abspath(f)
        elif depth < 0 or depth != 0:
            yield from traverse_dir(f, depth - 1)
    os.chdir(prev_wd)

def dirmap(dr, level=0, ignore=[], fillchar="\t"):
    
    if not os.path.exists(dr):
        return ""
    if os.path.isfile(dr):
        if os.path.abspath(dr) in ignore:
            return ''
        return os.path.basename(dr)
    prev_wd = os.getcwd()
    dr = os.path.abspath(dr)
    os.chdir(dr)
    dirmap_str = (fillchar * level) + os.path.split(dr)[1] + ":\n"
    items = os.listdir()
    items.sort(key=lambda item: item.startswith("."))
    for f in items:
        if os.path.abspath(f) in ignore:
            continue
        if os.path.isfile(f):
            basename = os.path.basename(f)
            dirmap_str += fillchar * (level + 1) + basename + "\n"
    for f in items:
        if os.path.abspath(f) in ignore:
            continue
        if os.path.isdir(f):
            basename = os.path.basename(f)
            dirmap_str += dirmap(f, level + 1, ignore, fillchar)
    os.chdir(prev_wd)
    return dirmap_str

def parse_dirmap(dirmap: str):
    
    paths = []
    lines = dirmap.splitlines()
    folders = [""] * dirmap.count(":")
    for i, line in enumerate(lines):
        if line.endswith(":"):
            folder = line.strip()[:-1]
            level = line.count("\t")
            folders[level] = folder
            if i < len(lines) - 1 and lines[i + 1].count("\t") == level:
                path = os.path.join(*folders[:level], folder, "")
                paths.append(path)
        else:
            level = line.count("\t")
            file = line.strip()
            path = os.path.join(*folders[:level], file)
            paths.append(path)
    
    return paths

def parse_command(cmd_str):
    
    all_patterns = (
        r"(?P<cmd>\bhow)\s*?(?P<subcmd>to)\s*(?P<arg>.+)",
        r"(?P<cmd>\bshare)\s*?(?P<subcmd>this)",
        r"(?P<cmd>\bshare)\s*?(?P<subcmd>status)",
        r"(?P<cmd>\bzone)\s*?(?P<subcmd>info)",
        r"(?P<cmd>\bshare)\s+?(?P<arg>.+)\s+?(?P<subcmd>with)\s+?(?P<subarg>.+)",
        r"(?P<cmd>\bshare)\s+?(?P<arg>.+)",
        r"(?P<cmd>\bview)\s+?(?P<arg>.+)",
        r"(?P<cmd>\bcollect)\s+?(?P<arg>.+)",
        r"(?P<cmd>\bcancel)\s*?(?P<arg>.+)",
        r"(?P<cmd>\busername)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bvisit)\s+?(?P<arg>.+)",
        r"(?P<cmd>\bselect)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bunselect)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bprotect)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bunprotect)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bchat)\s(?P<arg>.+)",
        r"(?P<cmd>\bthrow)\s*?(?P<arg>.+)?",
        r"(?P<cmd>\bkick)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bhelp)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bhelp\b)",
        r"(?P<cmd>\bcd)\s*?(?P<arg>.+)",
        r"(?P<cmd>\bhome)\s+?(?P<arg>.+)",
        r"(?P<cmd>\bhome\b)",
        r"(?P<cmd>\bpwd\b)",
        r"(?P<cmd>\bdirmap)\s*?(?P<arg>.+)?",
        r"(?P<cmd>\bls\b)",
        r"(?P<cmd>\bsearch)\s*(?P<arg>.+)",
        r"(?P<cmd>\breturn\b)",
        r"(?P<cmd>\babout\b)",
        r"(?P<cmd>\bleave\b)",
        r"(?P<cmd>\bclose\b)",
        r"(?P<cmd>\bexit\b)",
        r"(?P<cmd>\busername\b)",
        r"(?P<cmd>\bstart\b)",
        r"(?P<cmd>\bclear\b)",
        r"(?P<cmd>\bjoin\b)\s*?(?P<arg>[\w\d]{3} [\w\d]{4} [\w\d]{4})",
    )
    command = ''
    args = []
    for pattern in all_patterns:
        match = re.fullmatch(pattern, cmd_str, re.I | re.DOTALL)
        if match:
            groups = match.groups()
            command = match.group("cmd")
            try:
                sub_cmd = match.group("subcmd")
                command += " " + sub_cmd
            except:
                pass
            try:
                args.append(match.group("arg"))
            except:
                pass
            try:
                sub_arg = match.group("subarg")
                args.append(sub_arg)
            except:
                pass
            if len(groups) > 2 + len(args):
                args = args + list(groups[len(groups) - 1:])
            while None in args:
                args.remove(None)
            return (command, args)
    return (None, [])

def flexible_select(f, items=None, return_exact=False):
    if "internal storage" in f.lower() or "sd card" in f.lower():
        folders = split_path(f)
        if "internal storage" in f.lower():
            i = [folder.lower() for folder in folders].index("internal storage")
            folders.pop(i)
            folders.insert(0, "0")
            folders.insert(0, "emulated")
            folders.insert(0, "/storage")
            path = os.path.join(*folders)
            logger.debug(path)
            if os.path.exists(path):
                return [path]
        elif "sd card" in f.lower():
            try:
                cwd = os.getcwd()
                while os.getcwd() != "/storage":
                    os.chdir("..")
                dirs = os.listdir()
                dirs.remove("emulated")
                dirs.remove("self")
                if dirs:
                    sd_card = dirs[0]
                    i = [folder.lower() for folder in folders].index("sd card")
                    folders.pop(i)
                    folders.insert(0, sd_card)
                    folders.insert(0, "/storage")
                    path = os.path.join(*folders)
                    logger.debug(path)
                    if os.path.exists(path):
                        return [path]
            except Exception as exc:
                logger.debug(exc)
    if items is None:
        items = os.listdir()
    files = []
    total_items = len(items)
    if f.isdigit():
        n = int(f)
        if n - 1 < total_items:
            file = items[n - 1]
            if return_exact:
                files.append(file)
            else:
                files.append(os.path.abspath(file))
    elif all(str.isdigit(n) for n in map(str.strip, f.split())):
        nums = map(lambda n: int(str.strip(n)), f.split())
        for n in nums:
            if n - 1 < total_items:
                if return_exact:
                    files.append(items[n - 1])
                else:
                    abspath = os.path.abspath(items[n - 1])
                    files.append(abspath)
    elif re.search(r"\d+\s*-\s*\d+", f):
        match = re.search(r"(\d+)\s*-\s*(\d+)", f)
        n, m = match.group(1), match.group(2)
        n, m = int(n), int(m)
        for i in range(n, m + 1):
            if i - 1 < total_items:
                file = items[i - 1]
                if return_exact:
                    files.append(file)
                else:
                    files.append(os.path.abspath(file))
    else:
        for item in items:
            if f in item:
                if return_exact:
                    if f not in os.path.basename(item):
                        continue
                    files.append(item)
                else:
                    files.append(os.path.abspath(item))
    return files

class Message:
    
    def __init__(self, content, headers={}):
        
        self.type = type(content)
        self.headers = {}
        if type(content) is str:
            self.body = content.encode("utf-8")
            self.content = content
            self.headers['type'] = "str"
        elif type(content) is bytes:
            self.body = content
            self.content = content
            self.headers['type'] = "bytes"
        
        else:
            self.body = b''
            self.content = ''
            self.headers['type'] = 'unknown'
        self.headers['length'] = len(content)
        self.headers["sent_time"] = str(int(datetime.datetime.now().timestamp()))
        self.headers["sender"] = configs.data["name"]
        self.headers["min_ip"] = configs.min_ip
        self.headers.update(headers)
    
    @classmethod
    def from_bytes(cls, msg: bytes):
        
        headers_instr = msg[:configs.HEADER_SIZE].strip(configs.FILLCHAR.encode("utf-8")).decode("utf-8")
        body = msg[configs.HEADER_SIZE:]
        headers = {}
        
        for line in headers_instr.split(configs.HEADER_SEP):
            if line.isspace() or configs.HEADER_DELIMITER not in line:
                continue
            key, value = line.split(configs.HEADER_DELIMITER)
            headers[key] = value
        info = {}
        if headers['type'] == "bytes":
            return cls(body, headers)
        body = body.decode("utf-8")
        if headers.get("type") in ("info", "response", "request", "intro"):
            for line in body.split(configs.INFO_LINE_SEP):
                if line.isspace() or configs.INFO_DELIMITER not in line:
                    continue
                key, value = line.split(configs.INFO_DELIMITER)
                info[key] = value.strip()
            return cls.info(info, headers)
                
        return cls(body, headers)
    
    @classmethod
    def info(cls, data: dict, headers={}):
        
        body = []
        for key, value in data.items():
            body.append(f"{key}{configs.INFO_DELIMITER}{value}")
        body = configs.INFO_LINE_SEP.join(body)
        body = body.encode("utf-8")
        if "type" not in headers:
            headers["type"] = "info"
        if "length" not in headers:
            headers["length"] = str(len(body))
        s = cls("", headers)
        s.type = dict
        s.content = data
        s.body = body
        return s
    
    def get_headers(self, *headers):
        
        res = []
        if not headers:
            return self.headers.copy()
        for header in headers:
            res.append(self.headers.get(header))
        return tuple(res)
    
    def __bytes__(self):
        headers = ""
        for key, value in self.headers.items():
            headers += f"{key}{configs.HEADER_DELIMITER}{value}\n"
        headers = headers.ljust(configs.HEADER_SIZE, configs.FILLCHAR)
        headers = headers.encode("utf-8")
        msg = headers + self.body
        return msg
    
    def __repr__(self):
        return str(bytes(self))


#name: parsers.py
#updated: 1610596581
