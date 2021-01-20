import collections
import time
import datetime
import json
import sys
import os
import shutil
import queue
import threading
import socket

from src.python import assets
from src.python import parsers
from src.python import configs
from src.python import helps
from src.python import maintainer
from src.python.configs import logger
from src.python.parsers import cache


n_cmd = 0
session_cmds = []

class DataSaver():
    
    def __init__(self):
        self.saving_now = False
    
    def _save(self):
        with assets.lock:
            self.saving_now = True
        with open(configs.data['data_path'], "w") as f:
            json.dump(configs.data, f, indent=4)
        with assets.lock:
            self.saving_now = False
    
    def save(self):
        if self.saving_now:
            return
        t = threading.Thread(target=self._save)
        t.deamon = True
        t.start()


saver = DataSaver()

def start():
    if configs.server_id and configs.running:
        return "A Zone is already running."
    if configs.running:
        return "Cannot start another Zone while you are member of a Zone."
    ip = assets.get_ip()
    if ip == configs.NOT_AT:
        return "You must be connected to a Wifi to start a Zone. Run 'help' command to know more."
    if not assets.run_server():
        return "Unable to start a Zone. Try to do it in another device or try again later."
    time.sleep(0.25)
    while not configs.server_id:
        pass
    assets.zone_info["zone_id"] = configs.server_id
    assets.zone_info["created"] = int(datetime.datetime.now().timestamp())
    assets.zone_info['members'] = []
    assets.zone_info['zone_host'] = configs.data['name']
    assets.zone_closed = False
    join(configs.server_id, True)
    configs.data['hosted_n'] += 1
    return "Created new Zone. Zone ID: " + configs.server_id

def close(confirm=False):
    if not configs.server_id:
        return "No running Zone to close."
    if not confirm and len(assets.zone_info['members']) > 1:
        confirm = input("Confirm about closing Zone? (y/n): ").strip().lower() == "y"
    assets.close_server()
    if configs.client:
        leave(True)
    configs.informed = True
    return "Zone Closed."

def join(server_id, controlled=False):
    if configs.server_id and not controlled:
        return "A Zone is already running on this device."
    if configs.running and not controlled:
        return "Already in a Zone."
    res = assets.connect(server_id)
    if res == 404:
        return "No Zone found with this id. Make sure that you are in same network as the Zone."
    if res is None:
        return "Invalid Zone Id."
    if not configs.server_id:
        print("Requested for join. Waiting for Zone host's approval..")
    client = assets.Client(res, None)
    intro = {
        "name": configs.data["name"],
        "joined": int(datetime.datetime.now().timestamp()),
    }
    intro_msg = parsers.Message.info(intro, {"type": "intro"})
    client.send(intro_msg, True)
    client.intro = intro
    first_msg = client.receive(True)
    if first_msg is None:
        return 'The Zone is not responding.'
    msg = first_msg.content
    if msg == "Username is already taken":
        return "There is already a member with username " + configs.data['name'] + " in that Zone.You have to change username and rejoin the Zone."
    if msg == "full":
        return "The Zone has reached maximum number of members."
    if msg == "Rejected":
        return "Zone host has rejected you."
    configs.running = configs.running or (not controlled)
    configs.client = client
    t = threading.Thread(target=assets.send_message, args=(configs.client, ))
    t.daemon = True
    t.start()
    t = threading.Thread(target=assets.receive_message, args=(configs.client, ))
    t.daemon = True
    t.start()
    t = threading.Thread(target=assets.give_attendance, args=(configs.client, ))
    t.daemon = True
    t.start()
    t = threading.Thread(target=assets.manage_communication, args=(configs.client, ))
    t.daemon = True
    t.start()
    configs.informed = False
    assets.zone_host = msg
    assets.members = int(first_msg.get_headers("members")[0])
    configs.joined = True
    if msg == configs.data["name"]:
        msg = "You"
    data = [server_id.upper(), msg, intro['joined']]
    for i, record in enumerate(configs.data['history']):
        if data[0] == record[0] and data[1] == record[1]:
            n = record[3] + 1
            data.append(n)
            configs.data['history'][i] = data
            break
    else:
        data.append(1)
        configs.data['history'].append(data)
        configs.data['history'].reverse()
    if not configs.server_id:
        configs.data['joined_n'] += 1
    return f"Joined {msg}'s Zone."

def check():
    for data in configs.data["history"]:
        zone_id = data[0]
        res = assets.connect(zone_id)
        if res in (404, None):
            continue
        client = assets.Client(res, None)
        msg = parsers.Message("", {"type": "check"})
        client.send(msg, True)
        first_msg = client.receive(True)
        if first_msg.content == "full":
            continue
        return (first_msg.content, zone_id)
    return None

def leave(confirm=False):
    if not configs.running:
        return "You are not in any Zone."
    if not confirm:
        confirm = input("Confirm about leaving zone? (y/n): ").strip().lower() == "y"
        if confirm:
            farewell_msg = parsers.Message("", {"type": "leave"})
            configs.client.send(farewell_msg, urgent=True)
            time.sleep(0.25)
        else:
            return False
    for client in configs.clients:
        try:
            client.close()
        except:
            pass
    configs.clients.clear()
    configs.running = False
    configs.client = None
    configs.active_ports.clear()
    configs.visiting = ""
    configs.visitors.clear()
    configs.min_ip = ""
    assets.deliveries.clear()
    assets.expecteds.clear()
    assets.received_chats.clear()
    assets.news.clear()
    assets.share_reqs.clear()
    assets.visit_reqs.clear()
    assets.senders.clear()
    assets.receivers.clear()
    assets.service_running = False
    assets.public_shares = queue.Queue()
    assets.visitors_data.clear()
    assets.visitors_command = queue.Queue()
    assets.cancelled.clear()
    assets.zone_host = ''
    assets.targeted_receiver = None
    assets.members = 0
    if configs.server_id:
        close(True)
    return "Left from Zone."

def zone_info(return_dict=False):
    
    if not configs.running:
        return "You are not in any Zone."
    req = {
        "type": "request",
        "topic": "zone info"
    }
    req = parsers.Message("", req)
    configs.client.messages.put(req)
    ex = ("response", "zone info")
    assets.deliveries.append(None)
    assets.expecteds.append(ex)
    i = len(assets.deliveries) - 1
    time.sleep(0.1)
    s = time.time()
    while not assets.deliveries[i]:
        if time.time() - s > configs.WAITING_TIME * 1.25:
            return "No response from Zone."
        if assets.zone_closed:
            configs.datarmed = True
            return "Zone has been closed."
        time.sleep(0.1)
    res = assets.deliveries[i]
    assets.deliveries.pop(i)
    assets.expecteds.pop(i)
    status = res.get_headers("status")[0]
    if status == "200":
        info = res.content
        if return_dict:
            return info
        res = f"Zone ID: {info['zone_id']}\nZone Host: {info['zone_host']}\nZone Created on {datetime.datetime.fromtimestamp(int(info['created'])).strftime('%I:%M:%S %p')}\nTotal Members: {info['total_members']}\nMembers: {info['members']}"
        if not configs.server_id:
            assets.zone_info = info.copy()
        return res
    return "Failed to get Zone info."

def chat(msg=None):
    if not configs.running:
        return "You are not in any Zone."
    if msg:
        msg = parsers.Message(msg, {"type": "chat"})
        configs.client.messages.put(msg)
        assets.received_chats.append(msg)

def share_with(stuffs, receiver):
    stuffs = stuffs.strip()
    receiver = receiver.strip()
    if not configs.running:
        return "You must be in a Zone to share."
    if configs.server_id and len(assets.zone_info.get("members", [])) == 1:
        return "There is no member in the Zone to share with."
    elif stuffs == "selected":
        stuffs = configs.selected.copy()
    elif os.path.exists(stuffs):
        stuffs = [stuffs]
    else:
        return "Invalid Item!"
    info = {}
    sender = assets.Sender(None, stuffs, receiver)
    info["total_size"] = sender.total_size()
    info["total_files"] = len(sender.files)
    req = parsers.Message.info(info, {"type": "request", "topic": "share", "target": receiver})
    configs.client.messages.put(req)
    print("Informed about share. Waiting for response..")
    ex = ("response", "share")
    with assets.lock:
        assets.deliveries.append(None)
        assets.expecteds.append(ex)
        i = len(assets.deliveries) - 1
    time.sleep(0.5)
    s = time.time()
    while not assets.deliveries[i]:
        if time.time() - s > configs.WAITING_TIME * 1.25:
            return "No response from receiver."
        if assets.zone_closed:
            configs.datarmed = True
            return "Zone has been closed."
        time.sleep(0.5)
    res = assets.deliveries[i]
    assets.deliveries.pop(i)
    assets.expecteds.pop(i)
    status = res.get_headers("status")[0]
    if status == "200":
        addr = res.get_headers("addr")[0]
        t = threading.Thread(target=assets.start_send, args=(addr, sender))
        t.daemon = True
        t.start()
        return f"Sharing {len(sender.files)} items with " + receiver + "."
    elif status == "404":
        return "No such member found in Zone."
    elif status == "500":
        return "Receiver has failed to receive the items."
    elif status == "403":
        return "Sharing has been denied by " + receiver.strip() + "."
    return "Failed to share."

def share(stuffs):
    stuffs = stuffs.strip()
    if not configs.running:
        return "You must be in a Zone to share."
    if assets.members == 2:
        return share_with(stuffs, "")
    if any(sender.sender.is_active for sender in assets.senders) or any(receiver.receiver.is_active for receiver in assets.receivers):
        return "Cannot start another session of public share while one is running.Please wait for that session to finish."
    if configs.server_id and len(assets.zone_info.get(  "members", [])) == 1:
        return "There is no member in the Zone to share with."
    if stuffs == "selected":
        stuffs = configs.selected.copy()
    elif os.path.exists(stuffs):
        stuffs = [stuffs]
    else:
        return "Invalid Item!"
    try:
        sock, addr = assets.create_server()
        addr = parsers.get_id(addr)
    except:
        return "Unable to start public share."
    t = threading.Thread(target=assets.begin_public_send, args=(sock, stuffs))
    t.deamon = True
    t.start()
    info = {}
    sender = assets.Sender(None, stuffs, "all")
    info["total_size"] = sender.total_size()
    info["total_files"] = len(sender.files)
    req = parsers.Message.info(info, {"type": "request", "topic": "share", "target": "all", "addr": addr})
    configs.client.messages.put(req)
    print("Informed about share. Waiting for response..")
    ex = ("response", "share")
    with assets.lock:
        assets.deliveries.append(None)
        assets.expecteds.append(ex)
        i = len(assets.deliveries) - 1
    s = time.time()
    time.sleep(0.5)
    while not assets.deliveries[i]:
        if time.time() - s > configs.WAITING_TIME * 1.25:
            return "No response from anybody in the Zone."
        if assets.zone_closed:
            configs.datarmed = True
            return "Zone has been closed."
        time.sleep(0.5)
    res = assets.deliveries[i]
    assets.deliveries.pop(i)
    assets.expecteds.pop(i)
    accepted = int(res.content["accepted"])
    assets.targeted_receiver = accepted
    rejected = int(res.content["rejected"])
    if accepted == 0:
        try:
            s = assets.connect(addr)
        except:
            pass
        else:
            try:
                s.close()
            except:
                pass
        return "Nobody accepted the items."
    output = ""
    if rejected:
        output += str(rejected) + f" member{'s' if rejected > 1 else ''} rejected the items."
    output += f"Sharing the items with {accepted} member{'s' if accepted > 1 else ''}."
    return output

def share_zone():
    if not configs.running:
        return "You are not in any Zone."
    output_str = ''
    if assets.senders:
        output_str += "Sending Status:\n"
        strs = []
        for sender in assets.senders:
            if not sender.receiver:
                continue
            output = f"\tSending {sender.status.get('files', '')} files, {parsers.pretify(sender.status.get('total size', 0))} to {sender.receiver}\n"
            output += "\tSession started on " + datetime.datetime.fromtimestamp(sender.started).strftime("%I:%M:%S %p") + ".\n"
            output += "\t" + f"Completed: {sender.status.get('completed', 0)}\n"
            overall_progress = sender.status.get('sent size', 0) / sender.status.get('total size', 1)
            overall_progress = round(overall_progress, 2) * 100
            output += "\t" + f"Progress: {overall_progress}%\n"
            records = []
            for file, s in sender.status.get("records", {}).items():
                sent, size, cancelled = s[0], s[1], s[2]
                size = 1 if size == 0 else size
                progress = sent / size
                progress = round(progress, 2) * 100
                if int(overall_progress) == 100 and int(progress) != 100:
                    continue
                r = f"\t{file} ({progress}%)"
                if cancelled:
                    r += " (cancelled)"
                records.append(r)
            if records:
                output += "\n\tAll Files:\n" + "\n".join(records)
            strs.append(output)
        assets.senders = [sender for sender in assets.senders if sender.sender.is_active]
        output_str += "\n\n".join(strs)
    if assets.receivers:
        if output_str:
            output_str += "\n"
        output_str += "Receiving Status:\n"
        strs = []
        for receiver in assets.receivers:
            if not receiver.sender:
                continue
            output = f"\tReceiving {receiver.status.get('files', 0)} files, {parsers.pretify(receiver.status.get('total size', 0))} from {receiver.sender}\n"
            output += "\tSession started on " + datetime.datetime.fromtimestamp(receiver.started).strftime("%I:%M:%S %p") + ".\n"
            output += "\t" + f"Completed: {receiver.status.get('completed', 0)}\n"
            overall_progress = receiver.status.get('received size', 0) / receiver.status.get('total size', 1)
            overall_progress = round(overall_progress, 2) * 100
            output += "\t" + f"Progress: {overall_progress}%\n"
            records = []
            for file, s in receiver.status.get("records", {}).items():
                received, size, cancelled = s[0], s[1], s[2]
                size = 1 if size == 0 else size
                progress = received / size
                progress = round(progress, 2) * 100
                if int(overall_progress) == 100 and int(progress) != 100:
                    continue
                r = f"\t{file} ({progress}%)"
                if cancelled:
                    r += " (cancelled)"
                records.append(r)
            if records:
                output += "\n\tAll Files:\n" + "\n".join(records)
            strs.append(output)
        assets.receivers = [receiver for receiver in assets.receivers if receiver.receiver.is_active]
        output_str += "\n\n".join(strs)
    if not output_str:
        return "No sharing activities going on."
    return output_str

def share_this():
    path = maintainer.congregate_files(os.path.join(configs.data['home_dir'], 'All_files_for_CongregateDevices'))
    if not path:
        return "Fail to perform operations."
    helps.share_this(path)

def visit(dest):
    dest = dest.strip()
    if not configs.running:
        return "You must be in a Zone to visit."
    if configs.server_id and len(assets.zone_info["members"]) == 1:
        return "There is no member in the Zone to visit."
    msg = parsers.Message.info({}, {"type": "request", "topic": "visit", "target": dest})
    configs.client.messages.put(msg)
    print("Requested for visit. Waiting for response.")
    ex = ("response", "visit")
    with assets.lock:
        i = len(assets.expecteds)
        assets.expecteds.append(ex)
        assets.deliveries.append(None)
    time.sleep(0.5)
    s = time.time()
    while not assets.deliveries[i]:
        if time.time() - s > configs.WAITING_TIME * 1.25:
            return "No response from " + dest + "."
        if assets.zone_closed:
            configs.datarmed = True
            return "Zone has been closed."
        time.sleep(0.5)
    res = assets.deliveries.pop(i)
    assets.expecteds.pop(i)
    status = res.get_headers("status")[0]
    if status == "200":
        configs.visiting = dest
        return dest + " accepted you as his guest."
    elif status == "404":
        return "No such member found in Zone."
    elif status == "403":
        return "Visit has been denied by " + dest + "."

def pwd(visitor=''):
    if visitor:
        return parsers.pretify_path(assets.visitors_data[visitor]['wd'])
    return parsers.pretify_path(os.getcwd())

def ls(visitor='', for_programme=False):
    if visitor:
        cwd = os.getcwd()
        assets.lock.acquire()
        os.chdir(assets.visitors_data[visitor]['wd'])
    items = []
    i = 0
    for f in os.listdir():
        if os.path.abspath(f) in configs.data['protected'] and visitor:
            continue
        i ++ 1
        if os.path.isfile(f):
            items.append(f"{i + 1}.(file) {f}")
        elif os.path.isdir(f):
            items.append(f"{i + 1}.(folder) {f}")
        items.append(f"size: {parsers.pretify(parsers.total_size(os.path.abspath(f)))}, last modified on {datetime.datetime.fromtimestamp(os.stat(f).st_mtime).strftime('%d %B %Y %I:%M:%S %p')}")
    if visitor:
        os.chdir(cwd)
        assets.lock.release()
    return '\n'.join(items)

def cd(dr, visitor=''):
    dr = parsers.real_path(dr.strip())
    logger.warning(parsers.is_accessable(os.path.abspath(dr)))
    if visitor:
        cwd = os.getcwd()
        assets.lock.acquire()
        if assets.visitors_data[visitor]['wd']:
            os.chdir(assets.visitors_data[visitor]['wd'])
        if not os.path.exists(dr):
            items = parsers.flexible_select("i:" + dr)
            while items and (not os.path.isdir(items[0]) or parsers.is_accessable(items[0])):
                items.pop(0)
            if items:
                assets.visitors_data[visitor]['wd'] = items[0]
                os.chdir(cwd)
                assets.lock.release()
                return "Current working directory: " + parsers.pretify_path(items[0])
        if os.path.exists(dr):
            if os.path.abspath(dr) not in configs.data['protected'] and parsers.is_accessable(dr):
                assets.visitors_data[visitor]['wd'] = os.path.abspath(dr)
                os.chdir(cwd)
                assets.lock.release()
                return "Current working directory: " + parsers.pretify_path(os.path.abspath(dr))
            else:
                while "../" in dr:
                    dr = dr.replace("../", "")
                while "..\\" in dr:
                    dr = dr.replace("..\\", "")
                if dr and assets.visitors_data[visitor]['wd']:
                    os.chdir(cwd)
                    assets.lock.release()
                    return "No such directory."
                try:
                    wd = dr
                    while wd in configs.data["protected"] or not parsers.is_accessable(wd):
                        os.chdir("..")
                        wd = os.getcwd()
                        os.listdir()
                    assets.visitors_data[visitor]['wd'] = wd
                    os.chdir(cwd)
                    assets.lock.release()
                    return "Current working directory: " + parsers.pretify_path(wd)
                except Exception as exc:
                    pass
                dirs = []
                while not dirs:
                    try:
                        for f in os.listdir():
                            if os.path.abspath(f) not in configs.data['protected'] and os.path.isdir(f):
                                dirs.append(os.path.abspath(f))
                                break
                        if not dirs:
                            os.chdir("../")
                    except:
                        os.chdir(cwd)
                        assets.lock.release()
                        return "Unable to change directory."
                    assets.visitors_data[visitor]['wd'] = dirs[0]
                    os.chdir(cwd)
                    assets.lock.release()
                    return 'Current working directory: ' + parsers.pretify_path(assets.visitors_data[visitor]['wd'])
    if os.path.exists(dr):
        abspath = os.path.abspath(dr)
        os.chdir(dr)
        return "Current Working directory: " + parsers.pretify_path(abspath)
    if dr == "home":
        os.chdir(configs.data['home_dir'])
        return "Current Working directory: " + parsers.pretify_path(os.getcwd())
    items = parsers.flexible_select("i:" + dr)
    while items and not os.path.isdir(items[0]):
        items.pop(0)
    if items:
        os.chdir(items[0])
        return "Current Working directory: " + parsers.pretify_path(os.getcwd())
    return "No such directory"

def dirmap(dr=None, visitor=''):
    if visitor:
        if dr and not parsers.is_accessable(dr):
            return "No such directory."
        cwd = os.getcwd()
        assets.lock.acquire()
        os.chdir(assets.visitors_data[visitor]['wd'])
        dr = assets.visitors_data[visitor]['wd'] if dr is None else dr
        dr = dr.strip()
        dirmap = parsers.dirmap(dr, ignore=configs.data['protected'], fillchar="    ")
        os.chdir(cwd)
        assets.lock.release()
        return dirmap
    else:
        if dr is None:
            dr = os.getcwd()
        else:
            dr = dr.strip()
    dr = parsers.real_path(dr)
    drmap = parsers.dirmap(dr, fillchar="    ")
    return drmap

@cache
def details(f, visitor=""):
    f = os.path.abspath(parsers.real_path(f.strip()))
    details_str = ""
    if f == "selected":
        if visitor:
            l = assets.visitors_data[visitor]["selected"]
        else:
            l = configs.selected
        for f in l:
            details_str += details(f) + "\n"
        return details_str
    if visitor:
        with lock:
            cwd = os.getcwd()
            os.chdir(assets.visitors_data[visitor]['wd'])
            f = os.path.abspath(f)
            if not parsers.is_accessable(f):
                os.chdir(cwd)
                return "No such file or directory."
            os.chdir(cwd)
        return details(f, visitor)
    if not os.path.exists(f):
        return "No such file or directory."
    name = os.path.basename(f)
    abspath = os.path.abspath(f)
    size = parsers.total_size(f)
    stat = os.stat(f)
    if not os.path.basename(f) or os.path.basename(f).isspace():
        details_str += f"Name: {parsers.pretify_path(f).replace('/', '')}\nAbosute path: {abspath}\n"
    else:
        details_str += f"Name: {os.path.basename(f)}\nAbosute path: {abspath}\n"
    if os.path.isdir(f):
        files = parsers.traverse_dir(f)
        details_str += "Type: Folder\n"
        details_str += "Total number of containing files: " + str(len(files)) + "\n"
        if "/storage" in f:
            details_str += f"Total Size (of accessable parts): {parsers.pretify(size)}\n"
        else:
            details_str += f"Total Size: {parsers.pretify(size)}\n"
        details_str += f"Last Modification date: {parsers.pretify_timestamp(stat.st_mtime)}\nLast Access date: {parsers.pretify_timestamp(stat.st_atime)}\n"
        individual_type_details = {"image": [0, 0], "audio": [0, 0], "video": [0, 0], "document": [0, 0], "others": [0, 0]}
        headings = ("Document", "Quantity", "Total Size", "Percentage of size")
        max_lens = [len(heading) for heading in headings]
        for file in files:
            ext = os.path.splitext(file)[1].replace(".", "").strip()
            if ext in parsers.image_ext:
                type_ = "image"
            elif ext in parsers.audio_ext:
                type_ = "audio"
            elif ext in parsers.video_ext:
                type_ = "video"
            elif ext in parsers.doc_ext:
                type_ = "document"
            else:
                type_ = "others"
            individual_type_details[type_][0] += 1
            individual_type_details[type_][1] += os.path.getsize(file)
        if files:
            strs = []
            for type_ in individual_type_details:
                p = round((individual_type_details[type_][1] / size) * 100, 2)
                i = 3
                while p == 0.0 and individual_type_details[type_][1]:
                    p = round((individual_type_details[type_][1] / size) * 100, i)
                    i += 1
                q = str(individual_type_details[type_][0]).center(max_lens[1])
                s = str(parsers.pretify(individual_type_details[type_][1])).center(max_lens[2])
                p = (str(p) + '%').center(max_lens[3])
                max_lens[0] = max(len(type_), max_lens[0])
                max_lens[1] = max(len(q), max_lens[1])
                max_lens[2] = max(len(s), max_lens[2])
                max_lens[3] = max(len(p), max_lens[3])
                type_ = type_.center(max_lens[0])
                strs.append(f"{type_.title()} - {q} - {s} - {p}")
            headings = ("Type".center(max_lens[0]), "Quantity".center(max_lens[1]), "Total Size".center(max_lens[2]), "Percentage of size".center(max_lens[3]))
            details_str += "\nStatistics of Individual Types:\n"
            details_str += " - ".join(headings) + "\n"
            details_str += "   ".join(["-" * i for i in max_lens]) + "\n"
            details_str += "\n".join(strs) + "\n"
        individual_ext_details = collections.defaultdict(lambda : [0, 0])
        headings = ("Extension", "Quantity", "Total Size", "Percentage of size")
        max_lens = [len(heading) for heading in headings]
        no_ext = [0, 0]
        for file in files:
            ext = os.path.splitext(file)[1].replace(".", "").strip()
            if not ext:
                no_ext[0] += 1
                no_ext[1] += os.path.getsize(file)
                continue
            data = individual_ext_details[ext]
            data[0] += 1
            data[1] += os.path.getsize(file)
        if individual_ext_details:
            strs = []
            individual_ext_details = {key: individual_ext_details[key] for key in sorted(individual_ext_details, key=lambda key: individual_ext_details[key][1], reverse=True)}
            if no_ext[0]:
                individual_ext_details["without extension"] = no_ext
                max_lens[0] = len("without extension")
            for ext in individual_ext_details:
                p = round((individual_ext_details[ext][1] / size) * 100, 2)
                i = 3
                while p == 0.0 and individual_ext_details[ext][1]:
                    p = round((individual_ext_details[ext][1] / size) * 100, i)
                    i += 1
                extn = ('.' + ext).center(max_lens[0]) if " " not in ext else ext.center(max_lens[0])
                q = str(individual_ext_details[ext][0]).center(max_lens[1])
                s = str(parsers.pretify(individual_ext_details[ext][1])).center(max_lens[2])
                p = (str(p) + '%').center(max_lens[3])
                max_lens[0] = max(len(extn), max_lens[0])
                max_lens[1] = max(len(q), max_lens[1])
                max_lens[2] = max(len(s), max_lens[2])
                max_lens[3] = max(len(p), max_lens[3])
                strs.append(f"{extn} - {q} - {s} - {p}")
            headings = ("Extension".center(max_lens[0]), "Quantity".center(max_lens[1]), "Total Size".center(max_lens[2]), "Percentage of size".center(max_lens[3]))
            details_str += "\nStatistics of Individual Extensions:\n"
            details_str += " - ".join(headings) + "\n"
            details_str += "   ".join(["-" * i for i in max_lens]) + "\n"
            details_str += "\n".join(strs) + "\n"
    else:
        ext = os.path.splitext(f)[1].replace(".", "").strip()
        type_ = parsers.types.get(ext, "Unknown")
        details_str += "Extension: ." + ext + "\n"
        details_str += f"Type: {type_}\n"
        details_str += f"Total Size: {parsers.pretify(size)}\n"
        details_str += f"Creation date: {parsers.pretify_timestamp(stat.st_ctime)}\nLast Modification date: {parsers.pretify_timestamp(stat.st_mtime)}\nLast Access date: {parsers.pretify_timestamp(stat.st_atime)}\n"
    return details_str

def select(f, visitor=''):
    parsers.real_path(f = f.strip())
    if visitor:
        cwd = os.getcwd()
        os.chdir(assets.visitors_data[visitor]['wd'])
        assets.lock.acquire()
        if os.path.exists(f):
            abs_path = os.path.abspath(f)
            if abs_path not in configs.data['protected'] and abs_path not in assets.visitors_data[visitor]['selected'] and parsers.is_accessable(abs_path):
                assets.visitors_data[visitor]['selected'].append(abs_path)
                logger.debug(assets.visitors_data[visitor]['selected'])
                os.chdir(cwd)
                assets.lock.release()
                return f + " has been selected."
        elif f == "all":
            for item in os.listdir():
                abs_path = os.path.abspath(item)
                if item not in assets.visitors_data[visitor]['selected'] and abs_path not in configs.data['protected'] and parsers.is_accessable(abs_path):
                    assets.visitors_data[visitor]['selected'].append(abs_path)
            os.chdir(cwd)
            assets.lock.release()
            return f"{len(os.listdir())} items selected."
        else:
            try:
                items = parsers.flexible_select(f)
            except Exception as exc:
                items = []
                logger.error(exc)
            for item in items:
                if item in assets.visitors_data[visitor]['selected'] and item in configs.data['protected'] and not parsers.is_accessable(item):
                    continue
                assets.visitors_data[visitor]['selected'].append(item)
            if len(items) < 4 and items:
                os.chdir(cwd)
                assets.lock.release()
                return ", ".join(map(os.path.basename, items)) + " has been selected."
            if len(items) >= 4:
                os.chdir(cwd)
                assets.lock.release()
                return str(len(items)) + " item(s) has been selected."
        os.chdir(cwd)
        assets.lock.release()
        return "No such file or directory."
    if os.path.exists(f):
        abs_path = os.path.abspath(f)
        if abs_path not in configs.selected:
            configs.selected.append(abs_path)
        return parsers.pretify_path(abs_path) + " has been selected"
    elif f == "all":
        items = os.listdir()
        for file in items:
            abs_path = os.path.abspath(file)
            if abs_path in configs.selected:
                continue
            configs.selected.append(abs_path)
        return f"{len(items)} items has been selected."
    else:
        try:
            items = parsers.flexible_select(f)
        except Exception as exc:
            items = []
            logger.error(exc)
        if items:
            for item in items:
                if item in configs.selected:
                    continue
                configs.selected.append(item)
            if len(items) < 4:
                return ", ".join(map(os.path.basename, items)) + " has been selected."
            elif len(items) >= 4:
                return str(len(items)) + " items has been selected."
        return "No such file or directory."

def unselect(f, visitor=''):
    f = parsers.real_path(f.strip())
    if visitor:
        if f == "all":
            assets.visitors_data[visitor]['selected'].clear()
            return ""
        cwd = os.getcwd()
        os.chdir(assets.visitors_data[visitor]['wd'])
        abs_path = os.path.abspath(f)
        assets.lock.acquire()
        if abs_path in assets.visitors_data[visitor]['selected']:
            assets.visitors_data[visitor]['selected'].remove(abs_path)
            os.chdir(cwd)
            assets.lock.release()
            return ""
        else:
            try:
                items = parsers.flexible_select("i:" + f, assets.visitors_data[visitor]['selected'], True)
            except Exception as exc:
                items = []
                logger.error(exc)
            for item in items:
                if item in assets.visitors_data[visitor]['selected']:
                    assets.visitors_data[visitor]['selected'].remove(item)
            if len(items) <= 4 and items:
                os.chdir(cwd)
                assets.lock.release()
                return str(len(items)) + " items has been unselected."
            if len(items) > 4:
                os.chdir(cwd)
                assets.lock.release()
                return ", ".join(items) + " items has been unselected."
            os.chdir(cwd)
            assets.lock.release()
            return ''
    if f == "all":
        configs.selected.clear()
        return "Selected items' list cleared."
    abspath = os.path.abspath(f)
    if abspath in configs.selected:
        configs.selected.remove(abspath)
    else:
        try:
            items = parsers.flexible_select("i:" + f, configs.selected, True)
        except Exception as exc:
            items = []
            logger.error(exc)
        for item in items:
            configs.selected.remove(item)
        if len(items) < 4:
            return ", ".join(map(os.path.basename, items)) + " has been unselected."
        elif len(items) >= 4:
            return str(len(items)) + " items has been unselected."
    return ""

def search(f, location=None, visitor=""):
    if location is None:
        if os.path.exists("/storage"):
            if not visitor:
                print("Searching the whole phone...might take a while....")
            try:
                items = parsers.flexible_select(f, parsers.traverse_dir("/storage"), True)
            except Exception as exc:
                items = []
                logger.error(exc)
        elif parsers.available_drives():
            items = []
            if not visitor:
                print("Searching the whole device...might take a while...")
            for drive in parsers.available_drives():
                if not visitor:
                    print("Sreaching in", drive[0], "drive")
                try:
                    items.extend(parsers.flexible_select(f, parsers.traverse_dir(drive), True))
                except Exception as exc:
                    logger.error(exc)
        else:
            location = parsers.minimum_path(os.getcwd())
            try:
                items = parsers.flexible_select(f, parsers.traverse_dir(location), True)
            except Exception as exc:
                items = []
                logger.error(exc)
        if not visitor:
            for item in items:
                if item not in configs.selected:
                    configs.selected.append(item)
        else:
            for item in items:
                if item not in assets.visitors_data[visitor]['selected'] and item not in configs.data['protected'] and parsers.is_accessable(item):
                    assets.visitors_data[visitor]['selected'].append(item)
        if items and len(items) <= 4:
            return ", ".join(map(os.path.basename, items)) + " has been selected. (unselect unwanted items manually)"
        elif items:
            return str(len(items)) + " items have been selected. View them by running 'view selected' command and unselect unwanted items manually."
        return "No such item found."
    if visitor:
        with lock:
            cwd = os.getcwd()
            os.chdir(assets.visitors_data[visitor]['wd'])
            location = os.path.abspath(location) if location is not None else None
            os.chdir(cwd)
        return search(f, location, visitor)
    if not os.path.isdir(location):
        return "No such directory."
    try:
        items = parsers.flexible_select(f, parsers.traverse_dir(location), True)
    except Exception as exc:
        items = []
        logger.error(exc)
    configs.selected.extend(items)
    if items and len(items) <= 4:
        return ", ".join(map(os.path.basename, items)) + " has been selected. (unselect unwanted items manually)"
    elif items:
        return str(len(items)) + " items have been selected. View them by running 'view selected' command and unselect unwanted items manually."
    return "No such item found."

def protect(item):
    item = parsers.real_path(item.strip())
    if not os.path.exists(item):
        if item == "selected":
            for file in configs.selected:
                if file not in configs.data['protected']:
                    configs.data['protected'].append(file)
            return ", ".join(map(os.path.basename, configs.data['protected'])) + " has been added to protected items' list."
        if item == "all":
            for file in os.listdir():
                abs_path = os.path.abspath(file)
                if abs_path not in configs.data['protected']:
                    configs.data['protected'].append(abs_path)
            return f"{len(os.listdir())} items has been added to protected items' list."
        try:
            items = parsers.flexible_select("i:" + item)
        except Exception as exc:
            items = []
            logger.error(exc)
        for item in items:
            if item not in configs.data['protected']:
                configs.data['protected'].append(item)
        logger.warning(items)
        if len(items) <= 4 and items:
            return ", ".join(map(os.path.basename, items)) + " has been added to protected items' list."
        elif len(items) > 4:
            return str(len(items)) + " items has been added to protected items' list"
        if not items:
            return "No such file or directory."
    abspath = os.path.abspath(item)
    if abspath not in configs.data['protected']:
        configs.data['protected'].append(abspath)
    return item + " has been added to protected items' list."

def unprotect(item):
    item = parsers.real_path(item.strip())
    if item == "all":
        configs.data['protected'].clear()
        return "Cleared protected items' list."
    if item == "selected":
        for file in configs.selected:
            if file in configs.data['protected']:
                configs.data['protected'].remove(file)
        return str(len(configs.selected)) + " item(s) has been removed from protected items' list"
    try:
        items = parsers.flexible_select("i:" + item, configs.data['protected'], True)
    except Exception as exc:
        items = []
        logger.error(exc)
    for item in items:
        if item in configs.data['protected']:
            configs.data['protected'].remove(item)
    if len(items) <= 4 and items:
        return ", ".join(map(os.path.basename, items)) + " has been removed from protected items' list."
    elif len(items) > 4:
        return str(len(items)) + " items has been removed from protected items' list"
    abspath = os.path.abspath(item)
    if abspath in configs.data['protected']:
        configs.data['protected'].remove(abspath)
    return item + " has been removed from protected items."

def view(topic, visitor=''):
    topic = topic.strip()
    def members():
        if not configs.running:
            return "You are not in any Zone."
        if configs.server_id:
            output_str = "Zone created on " + datetime.datetime.fromtimestamp(assets.zone_info["created"]).strftime("%I:%M:%S %p")
            output_str += "\nZone Host: " + configs.data['name']
            output = []
            for name in assets.maps:
                joined = int(assets.maps[name].intro['joined'])
                joined = datetime.datetime.fromtimestamp(joined).strftime("%I:%M:%S %p")
                output.append(f"\t{name}, joined on {joined}.")
            if output:
                output_str += "\nMembers:\n" + "\n".join(output)
            return output_str
        req = parsers.Message("", {"type": "request", "topic": "members"})
        configs.client.messages.put(req)
        ex = ("response", "members")
        with assets.lock:
            i = len(assets.expecteds)
            assets.expecteds.append(ex)
            assets.deliveries.append(None)
        time.sleep(0.25)
        s = time.time()
        while assets.deliveries[i] is None:
            if time.time() - s > 180:
                return "No response from Zone."
            if assets.zone_closed:
                return "Zone has been closed."
            time.sleep(0.125)
        res = assets.deliveries.pop(i)
        assets.expecteds.pop(i)
        status = res.get_headers("status")[0]
        if status == "200":
            info = res.content
            output_str = "Zone created on " + datetime.datetime.fromtimestamp(int(info["created"])).strftime("%I:%M:%S %p")
            output_str += "\nZone Host: " + info['zone_host']
            output = []
            for name in list(info.keys())[2:]:
                joined = int(info[name])
                joined = datetime.datetime.fromtimestamp(joined).strftime("%I:%M:%S %p")
                output.append(f"\t{name}, joined on {joined}.")
            if output:
                output_str += "\nMembers:\n" + "\n".join(output)
            return output_str
        return "Failed collect members info."
    def selected(*args):
        if visitor:
            selected_list = assets.visitors_data[visitor]['selected'].copy()
        else:
            selected_list = configs.selected.copy()
        n_dirs = 0
        n_total = len(selected_list)
        n_files = 0
        for i in range(len(selected_list)):
            if os.path.isdir(selected_list[i]):
                n_dirs += 1
            else:
                n_files += 1
            selected_list[i] = str(i + 1) + ". " + parsers.pretify_path(selected_list[i])
        l = "\n".join(selected_list)
        s = lambda n: "s" if n > 1 else ""
        s = (s(n_total), s(n_dirs), s(n_files))
        if n_total == 0:
            return "Nothing is selected."
        info = f"{n_dirs} folder{s[1]} and {n_files} file{s[2]} selected ({n_total} in total)."
        return info + "\n" + l
    def status():
        info = zone_info(True)
        output = {
            "Username": configs.data['name'],
            "First Used": datetime.datetime.fromtimestamp(configs.data['joined']).strftime("%A, %d %B %Y %I:%M %p"),
        }
        output_str = []
        for key, value in output.items():
            output_str.append(f"{key}: {value}.")
        output_str.append("\nCurrent Status: " +  f"{'Not ' if not configs.running else ''}In Zone")
        if configs.running and info:
            output_str.append("Zone Info:")
            info = f"Joined On: {datetime.datetime.fromtimestamp(configs.client.intro['joined']).strftime('%I:%M:%S %p')}\nZone ID: {info['zone_id']}\nZone Host: {info['zone_host']}\nZone Created on {datetime.datetime.fromtimestamp(int(info['created'])).strftime('%I:%M:%S %p')}\nTotal Members: {info['total_members']}"
            output_str.append(info)
        if configs.visiting:
            output_str.append("Visiting " + configs.visiting)
        if configs.visitors:
            output_str.append("Visitors: " + ", ".join(configs.visitors))
        if configs.running:
            if assets.senders:
                output_str.append(f"Number of running sending sessions(including the completed ones): {len(assets.senders)}")
            if assets.receivers:
                output_str.append(f"Number of running receiving sessions(including the completed ones): {len(assets.receivers)}")
        output_str.append("\nRecords:")
        output_str.append(f"Total time spent in using this programme: {parsers.pretify_time(configs.data['total_time'])}.")
        output_str.append(f"Number of times this programme was launched/run: {configs.data['times_launched']}")
        joined, hosted = configs.data['joined_n'], configs.data['hosted_n']
        output_str.append(f"Number of joined Zones: {joined}.")
        output_str.append(f"Number of hosted Zones: {hosted}")
        sent, received = configs.data['total_sent'], configs.data['total_received']
        output_str.append(f"Number of total sending sessions: {configs.data['sending_sessions']}")
        output_str.append(f"Number of total receiving sessions: {configs.data['receiving_sessions']}")
        output_str.append(f"Total Sent: {parsers.pretify(sent)}.")
        output_str.append(f"Total Received: {parsers.pretify(received)}.")
        output_str.append(f"Total number of executed valid commands: {configs.data['total_commands']}")
        output_str.append(f"Total number of invalid commands: {configs.data['invalid_commands']}")
        if any(n > 0 for n in configs.data["command_records"].values()):
            output_str.append("Individual command records:")
            max_len = max([len(cmd) for cmd in configs.data["command_records"]] + [len("Command")])
            output_str.append("Command".ljust(max_len) + " - " + "Times Executed")
            output_str.append("-" * max_len + "   " + "-" * len("Times Executed"))
        configs.data["command_records"] = dict(sorted([(key, value ) for key, value in configs.data["command_records"].items()], key=lambda item: item[1], reverse=True))
        for cmd, n in configs.data["command_records"].items():
            if n > 0:
                output_str.append(f"{cmd.ljust(max_len)} - {str(n).center(len('Times Executed'))}")
        output_str = '\n'.join(output_str) + "\n"
        return output_str
    def visitors():
        if not configs.running:
            return "You are not in any Zone."
        if not configs.visitors:
            return "Nobody is currently visiting your device."
        n = len(configs.visitors)
        output_str = f"{n} visitor{'s' if n > 1 else ''} is currently visiting your device\n"
        output_str += "Individual Visitor Informations:"
        for name, data in assets.visitors_data.items():
            data_str = f"\nName: {name}\n"
            entered = int(data["entered"])
            entered = datetime.datetime.fromtimestamp(entered)
            entered = entered.strftime("%I:%M:%S %p")
            data_str += "Entered At " + entered
            data_str += "\nWorking Directory: " + data['wd']
            if data["selected"]:
                slt = view("selected", name)
                slt = "\n".join(map(parsers.pretify_path, slt.splitlines()[1:]))
                data_str += "\nSelected Items:\n" + slt
            output_str += data_str
        return output_str
    def protected(*args):
        files = 0
        folders = 0
        protected_items = []
        for i, f in enumerate(configs.data['protected']):
            if os.path.isfile(f):
                files += 1
            else:
                folders += 1
            protected_items.append(f"{i + 1}. {parsers.pretify_path(f)}")
        if not protected_items:
            return "Nothing is protected from visitors."
        s = ['s' if f > 1 else '' for f in (files, folders)]
        output_str = f"{folders} folder{s[1]} and {files} file{s[0]} {'are' if len(protected_items) > 1 else 'is'} protected from visitors:"
        output_str += "\n" + "\n".join(protected_items)
        return output_str
    def commands(*args):
        cmd_max_len = len(sorted(helps.formats.keys(), key=len, reverse=True)[0])
        output_str = ["commands".ljust(cmd_max_len) + "   " + "formats", ("-" * cmd_max_len) + "   " + ("-"  * cmd_max_len)]
        for cmd, fmt in helps.formats.items():
            output_str.append(cmd.ljust(cmd_max_len) + " : " + fmt)
        output_str.append("\nRun 'help {command}' to get help about any specific command")
        return "\n".join(output_str) 
    def history(*args):
        datas = configs.data['history'].copy()
        if not datas:
            return "No Zone record exists."
        max_lens = [len("Zone ID"), len("Zone Host"), len("Last Joined"), len("Times Joined")]
        for i, data in enumerate(datas):
            zone_id, zone_host, last_joined, joined_n = data
            last_joined = datetime.datetime.fromtimestamp(last_joined).strftime("%A, %d %B %Y, %I:%M %p")
            if max_lens[0] < len(zone_id):
                max_lens[0] = len(zone_id)
            if max_lens[1] < len(zone_host):
                max_lens[1] = len(zone_host)
            if max_lens[2] < len(last_joined):
                max_lens[2] = len(last_joined)
            if max_lens[3] < len(str(joined_n)):
                max_lens[3] = len(str(joined_n))
            datas[i] = (zone_id, zone_host, last_joined, joined_n)
        strs = ["Zone ID".ljust(max_lens[0]) + " - " + "Zone Host".center(max_lens[1]) + " - " + "Last Joined".center(max_lens[2]) + " - " + "Times Joined", "-" * max_lens[0] + "   " + "-" * max_lens[1] + "   " + "-" * max_lens[2] + "   " + '-' * max_lens[3]]
        for data in datas:
            as_str = data[0].ljust(max_lens[0]) + " - " + data[1].center(max_lens[1]) + " - " + data[2].center(max_lens[2]) + " - " + str(data[3]).center(max_lens[3])
            strs.append(as_str)
        return f"Total Joined: {configs.data['joined_n']} times\nTotal Hosted: {configs.data['hosted_n']} times.\n\nDistinct Zone Records:\n" + '\n'.join(strs)
    outputs = {
        "selected": selected,
        "status": status,
        "stats": status,
        "visitors": visitors,
        "protected": protected,
        "commands": commands,
        "members": members,
        "history": history,
    }
    outputs = collections.defaultdict(lambda : lambda *args: "Couldn't recognize topic", outputs)
    return outputs[topic]()

def kick(target):
    if not configs.running:
        return "You are not in any Zone."
    if not configs.server_id:
        return "Only Zone host can kick out members."
    target = target.strip()
    if target == configs.data['name']:
        return "Can't kick yourself."
    if target not in assets.maps:
        return "No such member in zone."
    confirm = input("Confirm about kicking out " + target + "? (y/n): ").strip().lower() == "y"
    if not confirm:
        return
    client = assets.maps[target]
    assets.remove_client(client, "{} has been kicked out of the Zone")
    return target + " has been kicked out from Zone."

def cancel(filename):
    if not configs.running:
        return "You are not in any Zone."
    if not assets.senders and not assets.receivers:
        return "No sharing activities going on."
    filename = filename.strip()
    headers = {"type": "info", "topic": "cancel", "filename": filename, "to": ""}
    for sender in assets.senders:
        if not sender.sender.is_active:
            continue
        headers["to"] = sender.receiver
        msg = parsers.Message("", headers)
        configs.client.messages.put(msg)
    for receiver in assets.receivers:
        if not receiver.receiver.is_active:
            continue
        headers["to"] = receiver.sender
        msg = parsers.Message("", headers)
        configs.client.messages.put(msg)
    assets.cancelled.append(filename)
    return ''

def username(name=None):
    if name is None:
        return "Your username is " + configs.data['name'] + "."
    if configs.running:
        return "Cannot change username while in a Zone."
    confirm = input("Confirm about chaning username?(y/n): ").strip().lower() == "y"
    if not confirm:
        return "Username changing cancelled."
    name = name.strip()
    prev_name = configs.data['name']
    configs.data['name'] = name
    return "Username changed from " + prev_name + " to " + name + "."

def clear():
    confirm = input("Clearing all records will clear all the saved data including your username, Zone records, protected items' list and will exit this programme, you have to reopen again.\nConfirm about clearing all records?(y/n): ")
    if not confirm:
        return ""
    leave(True)
    try:
        with open(configs.data['data_path'], "w") as f:
            pass
        os.unlink(configs.data['data_path'])
    except:
        pass
    return "Cleared all saved records."

def throw(user=None):
    if not configs.running:
        return "You are not in any Zone."
    if not configs.visitors:
        return "No visitors to throw out."
    throw_all = False
    if user is None:
        confirm = input("Throw all visitors out of your device?(y/n): ").strip().lower() == "y"
        throw_all = True
        if confirm:
            if len(configs.visitors) == 1:
                user = [configs.visitors[0]]
            else:
                users = configs.visitors.copy()
    else:
        if user not in assets.visitors_data:
            return "No such visitor."
        users = [user]
    for user in users:
        user = user.strip()
        assets.visitors_data.pop(user)
        configs.visitors.remove(user)
        headers = {"type": "news", "to": user}
        reply = parsers.Message("You have been thrown out.", headers)
        configs.client.messages.put(reply)
    if throw_all:
        return "All the " + str(len(configs.visitors)) + " visitors have been thrown out of your device"
    return user + " has been thrown out of your device."

def home(new_dir=None):
    if new_dir is None:
        return parsers.pretify_path(configs.data['home_dir']) + " is currently being used as home/default directory."
    if os.path.exists(new_dir):
        confirm = input("Confirm about changing home/default directory?(y/n): ").strip().lower() == "y"
        if not confirm:
            return ''
        configs.data['home_dir'] = os.path.abspath(new_dir)
        return "Default directory has been changed to " + parsers.pretify_path(os.path.abspath(new_dir))
    return "No such directory."

def none(*args):
    return "Invalid Command or format! Run 'view commands' to be all the runnable commands and their valid formats."

tasks = {
    "pwd": pwd,
    "ls": ls,
    "cd": cd,
    "dirmap": dirmap,
    "view": view,
    "select": select,
    "unselect": unselect,
    "start": start,
    "close": close,
    "join": join,
    "zone info": zone_info,
    "chat": chat,
    "leave": leave,
    "share with": share_with,
    "share status": share_zone,
    "share": share,
    "visit": visit,
    "kick": kick,
    "cancel": cancel,
    "return": none,
    "collect": none,
    "throw": throw,
    "protect": protect,
    "unprotect": unprotect,
    "username": username,
    "help": helps.help,
    "about": lambda : configs.ABOUT,
    "exit": lambda :"",
    "leave": leave,
    "close": close,
    "clear": clear,
    "home": home,
    "search": search,
    "details": details,
    "how to": lambda topic: helps.example if topic == "share" else none(),
    "share this": share_this,
}
tasks = collections.defaultdict(lambda : none, tasks)

def serve_visitors():
    while len(configs.visitors) > 0:
        assets.service_running = True
        msg = assets.visitors_command.get()
        sender_name = msg.get_headers("sender")[0].strip()
        v_cmd = msg.content
        v_cmd, args = parsers.parse_command(v_cmd)
        headers = {"type": "output", "to": sender_name}
        if v_cmd == "return":
            configs.visitors.remove(sender_name)
            assets.visitors_data.pop(sender_name)
            assets.news.append(parsers.Message("Visitor " + sender_name + " has left from this device."))
            continue
        elif v_cmd == "collect":
            headers['type'] = "info"
            if args[0] == "selected":
                stuff = assets.visitors_data[sender_name]['selected'].copy()
                invalid = False
            else:
                cwd = os.getcwd()
                os.chdir(assets.visitors_data[sender_name]['wd'])
                item = args[0]
                abspath = os.path.abspath(item)
                if os.path.exists(item) and abspath not in configs.data["protected"] and parsers.is_accessable(item):
                    stuff = [abspath]
                    invalid = False
                else:
                    output = "Invalid Item"
                    invalid = True
                    headers['status'] = '404'
                    reply = parsers.Message.info({}, headers)
                    stuff = []
                os.chdir(cwd)
            if not invalid:
                sender = assets.Sender(None, stuff, sender_name)
                addr = msg.get_headers("addr")[0]
                t = threading.Thread(target=assets.start_send, args=(addr, sender))
                t.daemon = True
                t.start()
                headers['status'] = '200'
                info = {"total_files": len(sender.files), "total_size": sender.total_size()}
                reply = parsers.Message.info(info, headers)
        else:
            output = tasks[v_cmd](*args, visitor=sender_name)
            reply = parsers.Message(output, headers)
        if sender_name in configs.visitors:
            configs.client.messages.put(reply)
        output = ''
    assets.service_running = False

def execute(cmd):
    global n_cmd
    n_cmd += 1
    shortcut = False
    saver.save()
    if cmd and not cmd.replace("p", "") and session_cmds:
        n = cmd.count("p")
        cmd = session_cmds[-n]
        shortcut = True
    if cmd == "status":
        cmd = "view status"
    cm, args = parsers.parse_command(cmd)
    if cm in configs.data["command_records"]:
        configs.data["command_records"][cm] += 1
        configs.data['total_commands'] += 1
        if not shortcut:
            session_cmds.append(cmd)
    elif cmd:
        configs.data["invalid_commands"] += 1
    if cm == "exit":
        if (configs.running and not configs.server_id) or (bool(configs.server_id) and len(assets.zone_info.get("members", [])) > 1):
            if leave():
                sys.exit()
        else:
            sys.exit()
    if configs.visiting and (cm in ("return", "ls", "pwd", "cd", "collect", "return", "visit", "share", "share with", "select", "unselect", "dirmap") or (cm == "view" and args == ["selected"])):
        logger.debug((cm, args))
        if cm == "visit":
            output = "Already Visiting " + configs.visiting
        elif cm in ("share with", "share", "protect", "unprotect", "clear", "kick", "search") or (cm == "username" and args) or (cm == "view" and args != ["selected"]):
            output = "This command is not runnable while visiting"
        elif cm not in tasks:
            output = "Invalid Command!!"
        else:
            headers = {"type": "command", "to": configs.visiting}
            if cm == "collect":
                try:
                    sock, addr = assets.create_server()
                except:
                    return "Unable to start collecting.", [], []
                headers['addr'] = parsers.get_id(addr)
                t = threading.Thread(target=assets.start_receive, args=(sock, configs.visiting))
                t.daemon = True
                t.start()
            msg = parsers.Message(cmd, headers)
            configs.client.messages.put(msg)
            if cm == "collect":
                ex = ("info", None)
            else:
                ex = ("output", None)
            assets.deliveries.append(None)
            assets.expecteds.append(ex)
            i = len(assets.expecteds) - 1
            time.sleep(0.25)
            s = time.time()
            while not assets.deliveries[i] and cm != "return":
                if time.time() - s > configs.WAITING_TIME * 1.25:
                    output = "No response from " + configs.visiting + "."
                    return output, [], []
                if assets.zone_closed:
                    break
                time.sleep(0.1)
            res = assets.deliveries.pop(i)
            assets.expecteds.pop(i)
            if cm == "return":
                output = "Returned from " + configs.visiting + "'s device."
                configs.visiting = ''
            elif cm == "collect" and res is not None:
                status = res.get_headers("status")[0]
                if status == "200":
                    total_files = res.content['total_files']
                    total_size = int(res.content['total_size'])
                    output = f"Collecting {total_files} files, {parsers.pretify(total_size)} in size"
                elif status == "404":
                    output = "Invalid Item!!"
                else:
                    output = "Failed to collect"
            elif res is not None:
                output = res.content
            else:
                output = "Zone has been closed"
                configs.datarmed = True
    else:
        cmd, args = parsers.parse_command(cmd)
        output = tasks[cmd](*args)
        if output == "Cleared all saved records.":
            sys.exit()
    news = set()
    kicked = False
    news_msgs = assets.news.copy()
    assets.news.clear()
    news_msgs.reverse()
    for msg in news_msgs:
        if not msg.content:
            continue
        if msg.content == "You have been thrown out.":
            news.add("You have been thown out of " + configs.visiting + "'s device.")
            configs.visiting = ''
            continue
        sent = msg.get_headers("sent_time")[0]
        sent = int(sent)
        sent = datetime.datetime.fromtimestamp(sent).strftime("%I:%M:%S %p")
        news.add(msg.content + "\n(" + sent + ")")
        if msg.content == "You have been kicked out from Zone":
            kicked = True
    chats = []
    for chat_msg in assets.received_chats.copy():
        from_, sent = chat_msg.get_headers("sender", "sent_time")
        if from_ == configs.data['name']:
            from_ = "You"
        sent = datetime.datetime.fromtimestamp(int(sent)).strftime("%I:%M:%S %p")
        chat_msg = f"{from_.strip()}: {chat_msg.content}\n({sent})"
        chats.append(chat_msg)
        assets.received_chats.pop(0)
    if assets.zone_closed:
        if not configs.informed:
            news.add("Zone has been closed.")
            configs.informed = True
        leave(True)
        assets.zone_closed = False
    if assets.visit_reqs:
        msg = assets.visit_reqs.pop()
        visitor = msg.get_headers("sender")[0].strip()
        accept = input(visitor + " wants to visit your device. Accept him/her as guest? (y/n) :").strip().lower() == "y"
        if accept:
            assets.visitors_data[visitor] = {"entered": msg.get_headers("sent_time")[0], "selected": [], "wd": None}
            if cd(os.getcwd(), visitor) in ("Unable to change directory.", "No such directory."):
                accept = False
                assets.visitors_data.pop(visitor)
            else:
                headers = {"type": "response", "topic": "visit", "status": "200"}
                msg = parsers.Message("", headers)
                configs.client.messages.put(msg)
                configs.visitors.append(visitor)
        if accept and not assets.service_running:
            t = threading.Thread(target=serve_visitors)
            t.daemon = True
            t.start()
        if not accept:
            headers = {"type": "response", "topic": "visit", "status": "403"}
            msg = parsers.Message("", headers)
            configs.client.messages.put(msg)
    if assets.share_reqs:
        msg = assets.share_reqs.pop()
        total_size = int(msg.content['total_size'])
        total_files = int(msg.content["total_files"])
        to, sender = msg.get_headers("target", "sender")
        sender = sender.strip()
        if to == "all":
            accept = input(f"{sender} wants to share {total_files} file{'s' if total_files > 1 else ''}, Total Size: {parsers.pretify(total_size)} with all members in Zone. Accept these? (y/n): ").strip().lower() == "y"
            if accept:
                addr = msg.get_headers("addr")[0]
                headers = {"type": "response", "topic": "share", "status": "200", "range": "public"}
                msg = parsers.Message.info({}, headers)
                configs.client.messages.put(msg)
                t = threading.Thread(target=assets.public_receive, args=(addr, sender))
                t.daemon = True
                t.start()
            else:
                headers = {"type": "response", "topic": "share", "status": "403", "range": "public"}
                msg = parsers.Message.info({}, headers)
                configs.client.messages.put(msg)
            return output, news, chats
        accept = input(f"{sender} wants to share {total_files} file{'s' if total_files > 1 else ''}, Total Size: {parsers.pretify(total_size)} with you. Accept these? (y/n): ").strip().lower() == "y"
        if accept:
            headers = {"type": "response", "topic": "share", "status": "200"}
            try:
                sock, addr = assets.create_server()
            except:
                print("Unable to start receive.")
                headers = {"type": "response", "topic": "share", "status": "500"}
                msg = parsers.Message.info({}, headers)
                configs.client.messages.put(msg)
                return output, news, chats
            headers['addr'] = parsers.get_id(addr)
            msg = parsers.Message.info({}, headers)
            configs.client.messages.put(msg)
            t = threading.Thread(target=assets.start_receive, args=(sock, sender))
            t.daemon = True
            t.start()
        else:
            headers = {"type": "response", "topic": "share", "status": "403"}
            msg = parsers.Message.info({}, headers)
            configs.client.messages.put(msg)
    if not configs.joined and (n_cmd == 1 or n_cmd % 5 == 0):
        available = check()
        if type(available) is tuple:
            host, zone_id = available
            print(host + "'s Zone with", zone_id, "Zone ID is available.")
            join = input("Join " + host + "'s Zone? (y/n): ").strip().lower() == "y"
            if join:
                print(tasks['join'](zone_id))
                return '', [], []
    if kicked:
        leave(True)
    logger.info(threading.active_count())
    return output, news, chats


#name: executor.py
#updated: 1611064510
