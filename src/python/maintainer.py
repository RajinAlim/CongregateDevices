import re
import json
import datetime
import html
import os
import shutil
import sys

from urllib.request import urlretrieve

wd = os.getcwd()
ESSENTIALS = {
    os.path.join("src", "python"): ['assets.py', 'configs.py', 'executor.py', 'helps.py', 'parsers.py', 'maintainer.py'],
    "": ['main.py', 'README.txt'],
}
project_dir = None
github_maintainer_link = "https://github.com/RajinAlim/CongregateDevices/blob/main/src/python/maintainer.py"
github_link = lambda path: f"https://github.com/RajinAlim/CongregateDevices/blob/main/{path}"

update_history = {
    "src/python/assets.py": 1609940002,
    "src/python/configs.py": 1609940002,
    "src/python/executor.py": 1609940002,
    "src/python/helps.py": 1609940002,
    "src/python/parsers.py": 1609940002,
    "src/python/maintainer.py": 1609940002,
    "main.py": 1609940002,
    "README.txt": 1609940116
}

class WebSource:
    
    def __init__(self, url):
        self.tempname = f".tempwebpagefilebeingusedbyCongregateDevices.html"
        self.abspath = os.path.abspath(self.tempname)
        self.f = None
        try:
            urlretrieve(url, self.abspath)
        except Exception as exc:
            self.tempname = None
            self.abspath = None
    
    def __enter__(self):
        try:
            self.f = open(self.abspath)
        except Exception as exc:
            return None
        return self.f
    
    def __exit__(self, exc_type, exc_track, exc):
        try:
            self.f.close()
            os.unlink(self.abspath)
        except:
            pass
        return False


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
            yield os.path.abspath(f) + os.sep
            yield from traverse_dir(f, depth - 1)
    os.chdir(prev_wd)

def retrieve_history(text):
    pat = r"\nupdate_history\s*?=\s*?({.+?})\n"
    match = re.search(pat, text, re.DOTALL)
    if match:
        history = json.loads(match.group(1))
        return history
    return {}

def retrieve_code(text):
    line_pat = r"<td id=\"LC\d+?\" class=\"blob-code blob-code-inner js-file-line\">(.+?)</td>"
    tag_pat = re.compile(r"<.+?>")
    try:
        code = ""
        lines = re.findall(line_pat, text, re.DOTALL)
        for line in lines:
            line = tag_pat.sub("", line)
            line = html.unescape(line)
            if not line.endswith("\n"):
                line += "\n"
            code += line
        return code
    except Exception as exc:
        return ""

def update_timestamp(filename):
    old_ts_pat = r"\n\n\n#name: .+?\n#updated: \d+"
    with open(filename) as f:
        text = f.read()
    new_timestamp = int(os.stat(filename).st_mtime)
    basename = os.path.basename(filename)
    text = re.sub(old_ts_pat, f"\n\n\n#name: {basename}\n#updated: {new_timestamp}", text, re.DOTALL)
    with open(filename, 'w') as f:
        f.write(text)
    return new_timestamp

def update_comment_time(filename):
    pat = r"(\"{3}.+?)Last Updated .+?((\n.+?)?\"{3})"
    with open(filename) as f:
        text = f.read()
    current_time = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
    text = re.sub(pat, r"\1Last Updated " + current_time + r"\2", text, flags=re.DOTALL)
    with open(filename, 'w') as f:
        f.write(text)
    return True

def fetch_data(text):
    pat = r"\n\n\n#name: (.+?)\n#updated: (\d+)"
    match = re.search(pat, text)
    if not match:
        return None
    return match.group(1), int(match.group(2))

def congregate_files(target_path, move=False):
    is_organized()
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    for path in ESSENTIALS:
        for f in ESSENTIALS[path]:
            full_path = os.path.join(project_dir, path, f)
            if not os.path.exists(full_path):
                continue
            new_path = os.path.join(os.path.abspath(target_path), f)
            shutil.copy(full_path, new_path)
            if move:
                try:
                    os.unlink(full_path)
                except:
                    pass
        if move:
            try:
                shutil.rmtree(path)
            except:
                pass
    return os.path.abspath(target_path)

def available_update():
    with WebSource(github_maintainer_link) as f:
        if f is None:
            return []
        maintainer_source = retrieve_code(f.read())
        u_history = retrieve_history(maintainer_source)
        if not u_history:
            return []
        available = []
        for file, timestamp in u_history.items():
            add = False
            if file in update_history:
                full_path = os.path.join(wd, file)
                if not os.path.exists(full_path):
                    continue
                with open(full_path) as f:
                    updated = fetch_data(f.read())[1]
                if updated is not None and updated < u_history[file]:
                    add = True
            elif file not in update_history:
                add = True
            if add:
                try:
                    update_time = datetime.datetime.fromtimestamp(u_history[file]).strftime("%d %B %Y, %I:%M %p")
                    available.append((file, update_time))
                except Exception as exc:
                    pass
        return available

def download_file(filepath, path=None):
    if type(path) is str and os.path.exists(path):
        file_abspath = os.path.join(os.path.abspath(path), os.path.basename(filepath))
    else:
        file_abspath = os.path.join(wd, filepath)
    dirname = os.path.dirname(file_abspath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    github_url = github_link(filepath)
    with WebSource(github_url) as webpage:
        if webpage is None:
            return None
        with open(file_abspath, "w") as f:
            code = retrieve_code(webpage.read())
            f.write(code)
            return file_abspath

def is_organized():
    global project_dir
    paths = split_path(wd)
    if "CongregateDevices" in paths:
        project_dir = os.path.join(*paths[:paths.index("CongregateDevices") + 1])
    elif os.path.exists("CongregateDevices"):
        project_dir = os.path.abspath("CongregateDevices")
    else:
        return False
    for path in ESSENTIALS:
        folder_path = os.path.join(project_dir, path)
        if not os.path.exists(folder_path):
            return False
        for f in ESSENTIALS[path]:
            file_path = os.path.join(folder_path, f)
            if not os.path.exists(file_path) and f != "README.txt":
                return False
    return True

def organize():
    global project_dir
    prev_wd = os.getcwd()
    os.chdir(wd)
    if project_dir and os.path.exists(project_dir):
        os.chdir(project_dir)
    else:
        os.makedirs("CongregateDevices", exist_ok=True)
        project_dir = os.path.abspath("CongregateDevices")
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    missing = []
    file_in_cd = [f for f in os.listdir() if f.endswith(".py")]
    for path in ESSENTIALS:
        if path == "":
            continue
        full_path = os.path.join(project_dir, path)
        if not os.path.exists(full_path) and full_path:
            os.makedirs(full_path)
        for f in ESSENTIALS[path]:
            is_missing = True
            if os.path.exists(f):
                with open(f) as fl:
                    data = fetch_data(fl.read())
                if data is not None and data[0] == f:
                    file_path = os.path.join(full_path, f)
                    fl = open(file_path, "w")
                    fl.close()
                    shutil.move(f, file_path)
                    is_missing = False
            if is_missing:
                for filename in file_in_cd:
                    if not os.path.exists(filename):
                        continue
                    with open(filename) as fl:
                        data = fetch_data(fl.read())
                    if data is not None and data[0] == f:
                        file_path = os.path.join(full_path, f)
                        fl = open(file_path, "w")
                        fl.close()
                        shutil.move(filename, file_path)
                        is_missing = False
            if is_missing and f.endswith(".py"):
                file_title = "/".join(split_path(path) + [f])
                missing.append(file_title)
    if not missing:
        os.chdir(project_dir)
    return missing

def finish_up():
    if not is_organized():
        missing = organize()
        if missing:
            print("Missing files:", ", ".join(missing))
            return False
    prev_wd = os.getcwd()
    os.chdir(project_dir)
    
    update_history = {}
    for path in ESSENTIALS:
        full_path = os.path.abspath(path)
        for f in ESSENTIALS[path]:
            file_path = os.path.join(path, f)
            file_abspath = os.path.abspath(file_path)
            if not os.path.exists(file_abspath):
                continue
            file_path = "/".join(split_path(file_path)[1:])
            update_history[file_path] = update_timestamp(file_abspath)
    update_history = json.dumps(update_history, indent=4)
    
    with open(os.path.join(project_dir, "src", "python", "maintainer.py")) as f:
        maintainer_source = f.read()
    pat = r"\nupdate_history\s*?=\s*?(\{[\n\s\"\w\d_/\\.:,]+?}\n)"
    maintainer_source = re.sub(pat, "\nupdate_history = " + update_history + "\n", maintainer_source, re.DOTALL)
    with open(os.path.join(project_dir, "src", "python", "maintainer.py"), "w") as f:
        f.write(maintainer_source)
    
    update_comment_time(os.path.join(project_dir, "src", "python", "configs.py"))
    update_comment_time("main.py")
    
    with open(os.path.join(project_dir, "src", "python", "configs.py")) as f:
        configs_source = f.read()
    pat = r"log_level = logging\.[A-Z]+?\s*?\n"
    configs_source = re.sub(pat, "log_level = logging.CRITICAL + 1\n", configs_source)
    pat = r"NOT_AT.*?\n"
    configs_source = re.sub(pat, "NOT_AT = \"127.0.0.1\"\n", configs_source, flags=re.DOTALL)
    with open(os.path.join(project_dir, "src", "python", "configs.py"), "w") as f:
        f.write(configs_source)
    try:
        os.chdir(prev_wd)
    except:
        pass
    return True

if __name__ =="__main__":
    finish_up()


#name: maintainer.py
#updated: 1609940002
