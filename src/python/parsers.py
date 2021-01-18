import math
import re
import datetime
import os

from src.python import configs
from src.python.configs import logger
from socket import gethostname
from socket import gethostbyname
try:
    from functools import cache
except ImportError:
    class cache:
        
        def __init__(self, func):
            self.func = func
            self.caches = {}
        
        def __call__(self, *args, **kwargs):
            if args in self.caches:
                return self.caches[args]
            return_value = self.func(*args, **kwargs)
            self.caches[args] = return_value
            return return_value

all_patterns = (
    re.compile(r"(?P<cmd>\bhow)\s*?(?P<subcmd>to)\s*(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bshare)\s*?(?P<subcmd>this)"),
    re.compile(r"(?P<cmd>\bshare)\s*?(?P<subcmd>status)"),
    re.compile(r"(?P<cmd>\bzone)\s*?(?P<subcmd>info)"),
    re.compile(r"(?P<cmd>\bshare)\s+?(?P<arg>.+)\s+?(?P<subcmd>with)\s+?(?P<subarg>.+)"),
    re.compile(r"(?P<cmd>\bshare)\s+?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bview)\s+?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bcollect)\s+?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bcancel)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\busername)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bvisit)\s+?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bselect)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bunselect)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bprotect)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bunprotect)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bchat)\s(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bthrow)\s*?(?P<arg>.+)?"),
    re.compile(r"(?P<cmd>\bkick)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bhelp)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bhelp\b)"),
    re.compile(r"(?P<cmd>\bcd)\s*?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bhome)\s+?(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\bhome\b)"),
    re.compile(r"(?P<cmd>\bpwd\b)"),
    re.compile(r"(?P<cmd>\bdirmap)\s*?(?P<arg>.+)?"),
    re.compile(r"(?P<cmd>\bls\b)"),
    re.compile(r"(?P<cmd>\bsearch)\s*(?P<arg>.+)in\s*(?P<subarg>.+)"),
    re.compile(r"(?P<cmd>\bsearch)\s*(?P<arg>.+)"),
    re.compile(r"(?P<cmd>\breturn\b)"),
    re.compile(r"(?P<cmd>\babout\b)"),
    re.compile(r"(?P<cmd>\bleave\b)"),
    re.compile(r"(?P<cmd>\bclose\b)"),
    re.compile(r"(?P<cmd>\bexit\b)"),
    re.compile(r"(?P<cmd>\busername\b)"),
    re.compile(r"(?P<cmd>\bstart\b)"),
    re.compile(r"(?P<cmd>\bclear\b)"),
    re.compile(r"(?P<cmd>\bjoin\b)\s*?(?P<arg>[\w\d]{3} [\w\d]{4} [\w\d]{4})"),
)
now = datetime.datetime.now()
today = datetime.datetime.strptime(now.strftime("%d-%m-%Y"), "%d-%m-%Y")
time_pat = re.compile(r"""
\b(?:tm|time):(?P<time1>(:?now|today|yesterday|\d{2}\s*[./-]\s*\d{2}\s*[./-]\s*\d{2,4})
(?:\s+\d{2}(?:\s*:\s*\d{2}(?:\s*:\s*\d{2})?)?)?
)
(?:
\s*-\s*
(?P<time2>(:?now|today|yesterday|\d{2}\s*[./-]\s*\d{2}\s*[./-]\s*\d{2,4})
(?:\s+\d{2}(?:\s*:\s*\d{2}(?:\s*:\s*\d{2})?)?)?
)
)?\b
""", re.VERBOSE) #tm:(now|today|yesterday|dd-mm-yyyy (hh:mm:ss)?)(-now|today|yesterday|dd-mm-yyyy (hh:mm:ss)?)? #5
timelimit_pat = re.compile(r"\bin:(\d+)([YyMmWwDdHhSs]|min|Min|MIN)\b") #in:{n}[yYmMdYHhsS]|min|Min|MIN #8
item_pat = re.compile(r"\b(?:i|item):(\d+\s*-\s*\d+|\d+(?:[\s,]+\d+)*)\b") #(i|item):n|m,n,o...|m-p #7
kw_pat1 = re.compile(r"\b('.+?'|\".+?\")\b") #'...'|".." #1
kw_pat2 = re.compile(r"([^\s\n\t]+)") #..... #10
range_pat = re.compile(r"\bcons(?:ider)?:(\d+\s*-\s*\d+|\d+(?:[\s,]+\d+)*)\b") #cons:(m-p|m, n, o, p) #3
takeonly_pat = re.compile(r"\b(?:tp|type):(photo|image|audio|video|\.[\d\w_]|file|folder|dir)(?:ectory)?\b") #type:photo|image|audio|video|file|folder|dir|{extention} #6
count_pat = re.compile(r"\b(?:t|take):(f|l|\d+)?-(\d+)\b") #t:f-n|-n|l-n|m-n #6
ignore_pat = re.compile(r"\b(?:ign|ignore):(.+)$") #ignore:.....$ #2
size_pat = re.compile(r"\b(?:s|size):(\d+(?:\.\d+)?(?:b|kb|mb|gb|B|KB|MB|GB)?)(?:\s*-\s*(\d+(?:\.\d+)?(?:b|kb|mb|gb|B|KB|MB|GB)?))?") #s:{n}b|kb|mb|gb|-{n}b|kb|mb|gb| #9

image_ext = ("jpg", "jpeg", "png", "gif", "bmp", "tiff", "raw", "webp", "tif")
video_ext = ("mp4", "3gp", "ogg", "wmv", "webm", "flv")
audio_ext = ("m4a", "mp3", "flac", "wav", "wma", "aac")

@cache
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

@cache
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

@cache
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

@cache
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

@cache
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

@cache
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

@cache
def total_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    size = 0
    for f in list(traverse_dir(path)):
        if os.path.isfile(f):
            size += os.path.getsize(f)
    return size

@cache
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

@cache
def real_size(size):
    pat = r"(\d+(?:\.\d+)?)\s*(b|kb|mb|gb|B|KB|MB|GB)"
    match = re.search(pat, size)
    if match:
        n, unit = match.groups()
        n = float(n)
        unit = unit.lower()
        to_multiply = {'b': 1, "kb": 1024, "mb": (1024 * 1024), "gb": 1024 * 1024 * 1024}
        return n * to_multiply.get(unit, 1)

@cache
def pretify_path(path):
    if path.startswith("/storage"):
        if "/storage/emulated/0" in path:
            path = path.replace("/storage/emulated/0", "Internal Storage", 1)
        else:
            path = os.path.join("SD Card", *split_path(path)[3:])
    return path

@cache
def real_path(f):
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
                return path
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
                        return path
            except Exception as exc:
                logger.error(exc)
    return f

@cache
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

@cache
def traverse_dir(path: str, depth=-1):
    def gen(path, depth):
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
    return list(gen(path, depth))

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
    command = ''
    args = []
    for pattern in all_patterns:
        match = pattern.fullmatch(cmd_str)
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

@cache
def flexible_select(f, items=None, return_exact=False):
    if return_exact:
        items = os.listdir() if items is None else items.copy()
    else:
        items = [os.path.abspath(item) for item in os.listdir()] if items is None else items.copy()
    not_to_take = set()
    match = kw_pat1.search(f)
    f = kw_pat1.sub("", f)
    if match is not None:
        kw = match.group(1)[1:-1]
        logger.warning(("quoted keyword", kw, f))
        pat = re.compile(kw)
        for item in items:
            if pat.search(os.path.basename) is None:
                not_to_take.add(item)
    ignore = ignore_pat.search(f)
    f = ignore_pat.sub("", f)
    if ignore is not None:
        logger.warning(("ignore", ignore.group(1), f))
        for item in flexible_select(ignore.group(1), items):
            if item in items:
                items.remove(item)
    match = range_pat.search(f)
    f = range_pat.sub("", f)
    if match is not None:
        f_str = match.group(1)
        logger.warning(("consider", f_str, f))
        targets = list(map(int, re.findall(r"(\d+)", f_str)))
        logger.warning(targets)
        if re.fullmatch(r"\d+\s*-\s*\d+", f_str):
            targets = list(range(targets[0], targets[1] + 1))
        items = [items[i] for i in targets]
    takeonly = takeonly_pat.search(f)
    f = takeonly_pat.sub("", f)
    takeonly = takeonly.group(1) if takeonly is not None else None
    for item in items:
        if takeonly is None:
            continue
        if takeonly == "file":
            if not os.path.isfile(item):
                not_to_take.add(item)
        elif takeonly in ("folder", "dir") and not os.path.isdir(item):
            not_to_take.add(item)
        else:
            ext = os.path.splitext(item)[1][1:].strip()
            logger.warning(ext)
            if takeonly.startswith("."):
                if not (ext == takeonly[1:].strip()):
                    logger.warning(item)
                    not_to_take.add(item)
            elif takeonly in ("image", "photo") and ext not in image_ext:
                not_to_take.add(item)
                logger.warning(("photo", item))
            elif takeonly == "audio" and ext not in audio_ext:
                not_to_take.add(item)
                logger.warning(("audio", item))
            elif takeonly == "video" and ext not in video_ext:
                not_to_take.add(item)
                logger.warning(("video", item))
    for item in not_to_take:
        if item in items:
            items.remove(item)
    match = time_pat.search(f)
    f = time_pat.sub("", f)
    if match:
        times = match.groupdict()
        logger.warning(("time", match.group(), f))
        start, end = times['time1'], times['time2']
        if start == "now":
            start = now.timestamp()
            if end is None:
                limit = 1
        elif start == "today":
            start = today.timestamp()
            if end is None:
                limit = 86400
        elif start == "yesterday":
            start = today.timestamp() - 86400
            if end is None:
                limit = 86400
        else:
            pat = r"(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{1,4})(?:\s+(\d{1,2})(?:\s*:\s*(\d{1,2})(?:\s*:\s*(\d{1,2}))?)?)?"
            date = re.search(pat, match.group(0))
            if date is None:
                start = 0
            else:
                timetuple = list(date.groups())
                limit = 60 if timetuple[5] is None else None
                limit = 3600 if timetuple[4] is None else limit
                limit = 86400 if timetuple[3] is None else limit
                limit = 1 if limit is None else limit
                for i in range(len(timetuple)):
                    if timetuple[i] is None:
                        timetuple[i] = "00"
                prettydate = "{}-{}-{} {}:{}:{}".format(*timetuple)
                fmt = "%d-%m-%Y %H:%M:%S" if len(timetuple[2]) > 2 else "%d-%m-%y %H:%M:%S"
                start = datetime.datetime.strptime(prettydate, fmt).timestamp()
                logger.warning("start " + prettydate)
        if end is None:
            end = start + limit
        elif end == "now":
            end = now.timestamp()
        elif end == "today":
            end = today.timestamp()
        elif end == "yesterday":
            end = today.timestamp() - 86400
        elif type(end) is not float:
            pat = r"(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{1,4})(?:\s+(\d{1,2})(?:\s*:\s*(\d{1,2})(?:\s*:\s*(\d{1,2}))?)?)?"
            date = re.search(pat, match.group(0))
            if date is None:
                end = datetime.datetime.now().timestamp()
            else:
                timetuple = list(date.groups())
                for i in range(len(timetuple)):
                    if timetuple[i] is None:
                        timetuple[i] = "00"
                prettydate = "{}-{}-{} {}:{}:{}".format(*timetuple)
                fmt = "%d-%m-%Y %H:%M:%S" if len(timetuple[2]) > 2 else "%d-%m-%y %H:%M:%S"
                end = datetime.datetime.strptime(prettydate, fmt).timestamp()
                logger.warning("end " + prettydate)
        if start is not None and end is not None:
            logger.warning((start, end))
            for item in items:
                stat = os.stat(item)
                ctime, mtime = stat.st_ctime, stat.st_mtime
                remove = True
                if start <= ctime and ctime <= end:
                    remove = False
                if start <= mtime and mtime <= end:
                    remove = False
                if remove:
                    not_to_take.add(item)
    take = count_pat.search(f)
    f = count_pat.sub(" ", f)
    take = take.groups() if take is not None else None
    logger.warning(("take", take, f))
    match = item_pat.search(f)
    f = item_pat.sub("", f)
    if match is not None:
        f_str = match.group(1)
        logger.warning(("items", f_str, f))
        targets = list(map(int, re.findall(r"(\d+)", f_str)))
        logger.warning(targets)
        if re.fullmatch(r"\d+\s*-\s*\d+", f_str):
            targets = list(range(targets[0], targets[1] + 1))
        for i in range(len(items)):
            if (i + 1) not in targets:
                not_to_take.add(items[i])
    match = timelimit_pat.search(f)
    f = timelimit_pat.sub("", f)
    if match:
        logger.warning(("timelimit", match.group(), f))
        time_intervals = {'y': (86400 * 365), 'm': (86400 * 30), 'w': 86400 * 7, 'd': 86400, 'h': 3600, 'min': 60, 's': 1}
        param = match.group(2).lower()
        coefficient = int(match.group(1))
        max_interval = coefficient * time_intervals[param]
        logger.warning(("max_interval", max_interval))
        for item in items:
            stat = os.stat(item)
            if abs(stat.st_ctime - now.timestamp()) > max_interval and abs(stat.st_mtime - now.timestamp()) > max_interval:
                not_to_take.add(item)
    match = size_pat.search(f)
    f = size_pat.sub("", f)
    if match:
        logger.warning(match.group())
        min_, max_ = match.groups()
        p_min = "." in min_
        min_ = real_size(min_)
        logger.warning(min_)
        if max_ is not None:
            max_ = real_size(max_)
            logger.warning(max_)
        else:
            p = int(math.log(min_, 1024))
            p = 3 if p > 3 else p
            if p_min:
                max_ = min_ + math.pow(10, p)
            else:
                max_ = min_ + math.pow(1024, p)
        logger.warning((min_, max_))
        for item in items:
            size = total_size(item)
            if min_ <= size and size <= max_:
                continue
            not_to_take.add(item)
    match = kw_pat2.search(f)
    f = kw_pat2.sub("", f)
    if match is not None and match.group(1) != "all":
        pat = re.compile(match.group(1))
        logger.warning(("keyword", match.group(1), f))
        for item in items:
            if pat.search(os.path.basename(item)) is None:
                not_to_take.add(item)
    for item in not_to_take:
        if item in items:
            items.remove(item)
    if take is not None:
        from_ = take[0]
        if from_ == "l":
            from_ = len(items) - int(take[1])
            to = len(items)
        elif from_ == "f" or from_ is None:
            from_ = 0
            to = int(take[1])
        else:
            n = int(take[1])
            if n == 0:
                return []
            from_ = (n * (int(take[0]) - 1))
            to = int(take[0]) * n
        logger.warning(("taking", from_, to, len(items)))
        items = items[from_ : to]
    return items
    
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
#updated: 1610948727
