
import datetime
import json
import logging
import os


log_level = logging.CRITICAL + 1
log_format = "%(levelname)s On %(asctime)s in %(funcName)s, %(filename)s at %(lineno)s, %(threadName)s: %(message)s"
date_format = "%d-%m-%y %H:%M:%S"
formatter = logging.Formatter(log_format, date_format)
logger = logging.getLogger("main")
logger.setLevel(log_level)
debug_handler = logging.StreamHandler()
debug_handler.setFormatter(formatter)
debug_handler.setLevel(logging.DEBUG)
logger.addHandler(debug_handler)

PROMPT = "# >> "
FILLCHAR = '-' 
INFO_DELIMITER = "=" 
INFO_LINE_SEP = "$" 
HEADER_SEP = "\n" 
HEADER_DELIMITER = ":" 
PORT = 7118 
NOT_AT = "127.0.0.1"
MAX_MEMBERS = 5
WAITING_TIME = 180 
HEADER_SIZE = 512 
BODY_SIZE = 2048 
DECREASE = BODY_SIZE // 16 
BUFFER_SIZE = BODY_SIZE + HEADER_SIZE
ABOUT = """Project: Congregate Devices.
Last Updated Wednesday, 20 January 2021, 10:40 PM
About Author:
    Name: Rajin Alim.
    Age: 17 (at the time of doing this project)
    Occupation: Student (at the time of doing this project)
    Homeland: Chattrogram, Bangladesh.
    Facebook: www.facebook.com/rajinalim.ra7118
    Gmail: rajin7118@gmail.com
Words from author: \"The purpose of this project is same as it's name, to Congregate multiple devices, to share files and folders among them.This project was done by a learner, so it is not usual to face errors.In case you face any error, please contact me.And also, consider leaving a review through my gmail.I would love to hear from you.Enjoy yourself, live your life, chase your dreams, take care of your dear ones, keep me in your prayers.\""""
ESSSENTIAL_KEYS = ['name', 'joined', 'protected', 'history', 'total_time', 'joined_n', 'hosted_n', 'total_sent', 'total_received', 'data_path', 'total_commands', 'invalid_commands', 'home_dir', 'project_dir', 'sending_sessions', 'receiving_sessions', "command_records", "times_launched"]
ALL_COMMANDS = ['pwd', 'ls', 'cd', 'dirmap', 'select', 'unselect', 'search', 'protect', 'unprotect', 'username', 'start', 'join', 'chat', 'visit', 'return', 'share', 'share with', 'collect', 'cancel', 'view', 'share status', 'kick', 'throw', 'clear', 'leave', 'close', 'help', 'share this', 'how to', 'about', 'exit', 'details']

joined = False 
active_ports = [] 
selected = [] 
running = False 
server_id = "" 
data = {} 
client = None 
informed = False 
servers = [] 
clients = [] 
visiting = "" 
visitors = [] 
min_ip = ""
saver_active = False

if os.path.exists("CongregateDevices_data.json"):
    with open("CongregateDevices_data.json") as f:
        try:
            data = json.load(f)
            if any(key in data and not os.path.exists(data[key]) for key in ("data_path", "home_dir", "project_dir")):
                try:
                    data.pop("data_path")
                except:
                    pass
                try:
                    data.pop("home_dir")
                except:
                    pass
                try:
                    data.pop("project_dir")
                except:
                    pass
        except Exception as exc:
            logger.error(exc)
if any(key not in data for key in ESSSENTIAL_KEYS):
    if "name" not in data:
        name = input("Enter your username: ").strip()
        data["name"] = name
        print("Welcome, ", name, "! Hope you enjoy this project. Run 'help' command if you are unfamiliar with this project.", sep='')
    if "joined" not in data:
        data["joined"] = int(datetime.datetime.now().timestamp()) 
    data['protected'] = [] if 'protected' not in data else data['protected']
    data['history'] = [] if 'history' not in data else data['history']
    data['total_time'] = 0 if 'total_time' not in data else data['total_time']
    data['joined_n'] = 0 if 'joined_n' not in data else data['joined_n']
    data['hosted_n'] = 0 if 'hosted_n' not in data else data['hosted_n']
    data['total_sent'] = 0 if 'total_sent' not in data else data['total_sent']
    data['times_launched'] = 0 if 'times_launched' not in data else data['times_launched']
    data['total_received'] = 0 if 'total_received' not in data else data['total_received']
    data['total_commands'] = 0 if 'total_commands' not in data else data['total_commands']
    data['invalid_commands'] = 0 if 'invalid_commands' not in data else data['invalid_commands']
    if "command_records" not in data:
        data["command_records"] = {command: 0 for command in ALL_COMMANDS}
        data['total_commands'] = 0
        data['invalid_commands'] = 0
    if any(cmd not in data['command_records'] for cmd in ALL_COMMANDS):
        data["command_records"] = {command: 0 for command in ALL_COMMANDS}
        data['total_commands'] = 0
        data['invalid_commands'] = 0
    if any(len(history) < 4 for history in data['history']):
        data['history'].clear()
    data['sending_sessions'] = 0 if 'sending_sessions' not in data else data['sending_sessions']
    data['receiving_sessions'] = 0 if 'receiving_sessions' not in data else data['receiving_sessions']
    data['project_dir'] = os.getcwd() if "project_dir" not in data else data['project_dir']
    cwd = os.getcwd()
    if "CongregateDevices" in cwd:
        try:
            os.listdir("..")
            tempname = ".testfolderbyCongregateDevices"
            os.makedirs(os.path.join("..", tempname))
            os.rmdir(os.path.join("..", tempname))
            os.chdir("..")
        except Exception as exc:
            os.chdir(cwd)
    data['home_dir'] = os.getcwd() if 'home_dir' not in data else data['home_dir']
    os.chdir(data['project_dir'])
    data['data_path'] = os.path.abspath("CongregateDevices_data.json") if 'data_path' not in data else data['data_path']
    with open("CongregateDevices_data.json", "w") as f:
        json.dump(data, f, indent=4)
os.chdir(data['home_dir'])



#name: configs.py
#updated: 1611160504
