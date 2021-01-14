import math
import datetime
import time
import os
import json
import threading
import queue
import socket

from src.python import configs
from src.python import parsers
from src.python.configs import logger


zone_info = {} 
requests = queue.Queue() 
chats = queue.Queue() 
lock = threading.Lock()
deliveries = [] 
expecteds = [] 
received_chats = [] 
news = [] 
zone_closed = False
share_replies = [] 
share_reqs = [] 
senders = [] 
receivers = [] 
public_shares = queue.Queue() 
visit_replies = [] 
visit_reqs = [] 
maps = {} 
visitors_data = {} 
visitors_command = queue.Queue() 
service_running = False 
cancelled = [] 
zone_host = '' 
targeted_receiver = -1 
clients = [] 

def get_ip():
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def is_active(addr):
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
    except ConnectionRefusedError:
        logger.info("Inactive addr: " + str(addr))
        return False
    else:
        return True

def create_server(addr=None, type_="TCP", not_at=configs.NOT_AT):
    
    if not addr:
        if not configs.server_id:
            ip = get_ip()
            if ip == configs.NOT_AT and configs.min_ip:
                ip = configs.min_ip
        else:
            logger.info("A server is already active.")
            ip = parsers.get_addr(configs.server_id)[0]
        if not configs.active_ports:
            port = configs.PORT
        else:
            port = configs.active_ports[-1] + 1
        addr = (ip, port)
        if not not_at:
            if type(not_at) is str and addr[0] == not_at:
                return None
            elif type(not_at) is int and addr[1] == not_at:
                return None
            elif type(not_at) is tuple and addr == not_at:
                return None
    addr = list(addr)
    while is_active(tuple(addr)):
        addr[1] += 1
        logger.info("Active server at " + str(addr))
    addr = tuple(addr)
    if type_ != "TCP":
        type_ = socket.SOCK_DGRAM
    else:
        type_ = socket.SOCK_STREAM
    sock = socket.socket(socket.AF_INET, type_)
    try:
        sock.bind(addr)
    except Exception as exc:
        logger.error(exc)
        return False
    else:
        configs.servers.append(sock)
        configs.active_ports.append(addr[1])
        return (sock, addr)

def connect(addr):
    if type(addr) is str:
        logger.info(addr)
        addr = parsers.get_addr(addr)
        logger.info(addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((addr))
    except (OSError, ConnectionRefusedError) as exc:
        logger.info("Not found.")
        return 404
    except:
        return None
    else:
        configs.clients.append(sock)
        return sock

def send_news(msg, not_to=None, send_self=True):
    if type(msg) is str:
        msg = parsers.Message(msg, {"type": "news", "sender": "server"})
    for client in clients:
        if configs.client and not send_self and client == configs.client:
            logger.info(msg.content)
            continue
        if not_to and not (client == not_to):
            client.messages.put(msg)

def remove_client(client, msg_format="{} has left the Zone."):
    logger.info("Removing " + str(client.intro) + " format: " + msg_format)
    for i, c in enumerate(clients):
        if c == client:
            send_news(msg_format.format(c.intro['name']), c, msg_format != "{} has been kicked out of the Zone")
            if msg_format == "{} has been kicked out of the Zone":
                client.send(parsers.Message("You have been kicked out from Zone", {"type": "news"}), True)
            with lock:
                try:
                    client.is_active = False
                    clients.pop(i)
                    maps.pop(client.intro['name'])
                    logger.info(client.intro['name'])
                    if i < len(zone_info['members']) and client.intro['name'] == zone_info['members'][i]:
                        zone_info['members'].pop(i)
                except:
                    pass
            return

def handle_requests():
    while configs.running:
        client, req = requests.get()
        topic = req.get_headers("topic")[0]
        logger.info(topic)
        logger.info(req.content)
        if topic == "members":
            reply = {
                "created": zone_info['created'],
                "zone_host": zone_info['zone_host']
            }
            for member in maps:
                reply[maps[member].intro['name']] = maps[member].intro['joined']
            reply = parsers.Message.info(reply, {'type': "response", "topic": "members", "status": "200"})
            client.messages.put(reply)
        elif topic == "share" and req.get_headers("target")[0] == "all":
            send_news(req, client)
            i = len(share_replies)
            ex = len(zone_info["members"])
            time.sleep(0.5)
            s = time.time()
            while len(share_replies) + 1 < (i + ex) and configs.running:
                if time.time() - s > 180:
                    break
                time.sleep(0.25)
            copy = share_replies.copy()
            accepted = []
            rejected = []
            for j in range(len(copy)):
                range_, status = copy[j].get_headers("range", "status")
                if range_ == "public":
                    msg = share_replies.pop(j - abs(i - len(share_replies)))
                    if status == "200":
                        accepted.append(msg.get_headers("sender")[0])
                    elif status == "403":
                        rejected.append(msg.get_headers("sender")[0])
            reply = parsers.Message.info({"accepted": len(accepted), "rejected": len(rejected)}, {"type": "response", "topic": "share"})
            client.messages.put(reply)
        elif topic == "zone info":
            res = zone_info.copy()
            res['zone_host'] = zone_info['zone_host']
            res["total_members"] = len(zone_info["members"])
            res["members"] = ", ".join(zone_info['members'])
            headers = {
                "sender": "server",
                "type": "response",
                "topic": topic,
                "status": 200,
            }
            msg = parsers.Message.info(res, headers)
            client.messages.put(msg)
        elif topic == "share":
            target = req.get_headers("target")[0]
            if target == client.intro["name"] or target not in zone_info["members"]:
                headers = {
                    "sender": "server",
                    "type": "response",
                    "topic": "share",
                    "status": "404"
                }
                res = parsers.Message("", headers)
                client.messages.put(res)
            else:
                i = zone_info["members"].index(target)
                receiver = clients[i]
                i = len(share_replies)
                receiver.messages.put(req)
                time.sleep(0.1)
                while len(share_replies) <= i:
                    time.sleep(0.1)
                res = share_replies[i]
                client.messages.put(res)
        elif topic == "visit":
            target = req.get_headers("target")[0]
            if target == client.intro["name"] or target not in zone_info["members"]:
                headers = {
                    "type": "response",
                    "topic": "visit",
                    "status": "404"
                }
                res = parsers.Message("", headers)
                client.messages.put(res)
            else:
                i = zone_info["members"].index(target)
                receiver = clients[i]
                i = len(visit_replies)
                receiver.messages.put(req)
                time.sleep(0.1)
                while len(visit_replies) <= i:
                    time.sleep(0.1)
                res = visit_replies[i]
                client.messages.put(res)

def forward_chat():
    while configs.running:
        sender, msg = chats.get()
        logger.info(msg.content)
        for client in clients:
            if sender == client:
                continue
            client.messages.put(msg)

def send_message(client):
    while configs.running and client.is_active:
        msg = client.messages.get()
        client.send(msg)

def receive_message(client):
    with lock:
        logger.info(configs.BODY_SIZE)
        configs.BODY_SIZE = configs.BODY_SIZE - configs.DECREASE
        logger.info(configs.BODY_SIZE)
    while configs.running and client.is_active:
        msg = client.receive()
        if msg:
            client.received_msg.put(msg)
            client.last_contact = time.time()
            configs.min_ip = parsers.min_ip(configs.min_ip, msg.get_headers("min_ip")[0])
        else:
            continue
    with lock:
        logger.info(configs.BODY_SIZE)
        configs.BODY_SIZE = configs.BODY_SIZE + configs.DECREASE
        logger.info(configs.BODY_SIZE)

def give_attendance(client):
    while configs.running and client.is_active:
        logger.info("Giving attendence")
        msg = parsers.Message("", {"type": "attendance"})
        client.messages.put(msg)
        time.sleep(configs.WAITING_TIME)

def check_attendance():
    while configs.running:
        now = time.time()
        for client in clients:
            if client.last_contact is None:
                time.sleep(30)
                continue
            logger.info(client.intro['name'] + " " + str(client.last_contact))
            interval = abs(now - client.last_contact)
            if interval > configs.WAITING_TIME * 1.25:
                logger.info(client.intro['name'])
                remove_client(client, "{} is offline.")
        time.sleep(configs.WAITING_TIME * 1.25)

def manage_client(client, ip):
    try:
        
        intro_msg = client.receive()
        client.intro = intro_msg.content
    except:
        try:
            
            intro_msg = client.receive()
            client.intro = intro_msg.content
        except:
            return
    if len(clients) >= configs.MAX_MEMBERS or configs.BODY_SIZE <= 512:
        msg = "full"
        headers = {"type": "str"}
        msg = parsers.Message(msg, headers)
        client.send(msg)
        return 
    elif intro_msg.get_headers("type")[0] == "check":
        msg = configs.data["name"]
        headers = {"type": "str"}
        msg = parsers.Message(msg, headers)
        client.send(msg)
        return 
    elif client.intro['name'] in zone_info['members']:
        
        msg = "Username is already taken"
        headers = {"type": "str"}
        msg = parsers.Message(msg, headers)
        client.send(msg)
        return
    if client.intro["name"] == configs.data["name"]:
        accept = True
    if client.intro["name"] == configs.data["name"]:
        accept = True
    else:
        
        accept = input(client.intro["name"] + " wants to join this Zone. Accept him/her? (y/n):").strip().lower() == "y"
    if not accept:
        msg = "Rejected"
        headers = {"type": "str"}
        msg = parsers.Message(msg, headers)
        client.send(msg)
        logger.info(msg)
        return 
    clients.append(client)
    msg = parsers.Message(zone_info['zone_host'], {"type": "str"})
    client.send(msg)
    logger.info(configs.min_ip)
    configs.min_ip = parsers.min_ip(configs.min_ip, ip)
    logger.info(configs.min_ip)
    with lock:
        zone_info["members"].append(client.intro["name"])
    maps[client.intro["name"]] = client
    t = threading.Thread(target=send_message, args=(client,))
    t.daemon = True
    t.start()
    t = threading.Thread(target=receive_message, args=(client,))
    t.daemon = True
    t.start()
    send_news(f"{client.intro['name']} has joined the zone", not_to=client, send_self=False)
    while configs.running and client.is_active:
        msg = client.received_msg.get()
        if not msg:
            continue
        type_, topic = msg.get_headers("type", "topic")
        if type_ == "leave":
            remove_client(client)
            return
        if type_ == "attendance":
            res = parsers.Message("", {'type': "attendance"})
            client.messages.put(res)
            continue
        elif type_ == "request":
            with lock:
                requests.put((client, msg))
        elif type_ == "chat":
            with lock:
                chats.put((client, msg))
        elif type_ == "response" and topic == "share":
            with lock:
                share_replies.append(msg)
        elif type_ == "response" and topic == "visit":
            with lock:
                visit_replies.append(msg)
        elif msg.get_headers("to")[0]:
            to = msg.get_headers("to")[0]
            if to == "all":
                for name in maps:
                    if name == client.intro["name"]:
                        continue
                    maps[name].messages.put(msg)
            else:
                try:
                    to = maps[to]
                except:
                    pass
                with lock:
                    to.messages.put(msg)
    logger.info(str(client.intro) + " " + str(client.is_active))

def accept_clients():
    control.listen(5)
    control.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    while configs.running:
        try:
            sock, addr = control.accept()
        except Exception as exc:
            logger.info(exc)
        client = Client(sock, addr)
        logger.info(addr)
        t = threading.Thread(target=manage_client, args=(client, addr[0]))
        t.daemon = True
        t.start()

def run_server():
    global control, clients
    clients = []
    try:
        control, addr = create_server(not_at=configs.NOT_AT)
    except:
        return False
    configs.running = True
    configs.server_id = parsers.get_id(addr)
    t = threading.Thread(target=handle_requests)
    t.daemon = True
    t.start()
    t = threading.Thread(target=forward_chat)
    t.daemon = True
    t.start()
    t = threading.Thread(target=check_attendance)
    t.daemon = True
    t.start()
    t = threading.Thread(target=accept_clients)
    t.daemon = True
    t.start()
    return True

def close_server():
    global requests, chats, lock, zone_closed
    farewell_msg = parsers.Message("", {"type": "close"})
    for client in clients:
        client.messages.put(farewell_msg)
    time.sleep(0.25)
    zone_info.clear()
    zone_info['members'] = []
    requests = queue.Queue()
    chats = queue.Queue()
    lock = threading.Lock()
    received_chats.clear()
    news.clear()
    share_replies.clear()
    visit_replies.clear()
    maps.clear()
    configs.min_ip = ""
    configs.running = False
    configs.server_id = ""
    configs.active_ports = []
    configs.selected = []
    configs.running = False
    configs.client = None
    clients.clear()
    zone_closed = True
    for sock in configs.servers:
        try:
            sock.close()
            logger.info("closed")
        except:
            pass
    configs.servers.clear()

def accept_sender(sock):
    sock.listen(1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client, addr = sock.accept()
    logger.info(addr)
    return client, addr

def start_receive(sock, sender_name):
    c, addr = accept_sender(sock)
    client = Client(c, addr)
    t = threading.Thread(target=receive_message, args=(client, ))
    t.daemon = True
    t.start()
    t = threading.Thread(target=send_message, args=(client,))
    t.daemon = True
    t.start()
    receiver = Receiver(client, sender_name)
    receivers.append(receiver)
    receiver.receive_info()
    receiver.start_receive()
    time.sleep(0.125)

def start_send(addr, sender):
    addr = parsers.get_addr(addr)
    sock = connect(addr)
    if type(sock) is socket.socket:
        client = Client(sock, addr)
        sender.sender = client
        sender.sender.is_active = True
        senders.append(sender)
        t = threading.Thread(target=send_message, args=(client,))
        t.daemon = True
        t.start()
        t = threading.Thread(target=receive_message, args=(client, ))
        t.daemon = True
        t.start()
        sender.inform()
        sender.sendall()
        sender.finish_up()
    else:
        print("Invalid response from receiver.")

def public_send(sender):
    logger.info("starting send")
    t = threading.Thread(target=send_message, args=(sender.sender,))
    t.daemon = True
    t.start()
    t = threading.Thread(target=receive_message, args=(sender.sender,))
    t.daemon = True
    t.start()
    sender.inform()
    sender.sendall()
    sender.finish_up()

def begin_public_send(sock, items):
    global targeted_receiver
    sock.listen(5)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    added = 0
    logger.info(targeted_receiver)
    while configs.running and (added < targeted_receiver or targeted_receiver == -1):
        try:
            client, addr = sock.accept()
            logger.info(addr)
        except:
            continue
        client = Client(client, addr)
        sender = Sender(client, items, "")
        if added == 0:
            sender.receiver = "all"
            added += 1
        senders.append(sender)
        t = threading.Thread(target=public_send, args=(sender, ))
        t.daemon = True
        t.start()
        logger.info((added, targeted_receiver))
        time.sleep(1)
    logger.info(targeted_receiver)
    targeted_receiver = -1
    sock.close()

def public_receive(addr,sender_name):
    sock = connect(addr)
    time.sleep(0.5)
    if type(sock) is not socket.socket:
        print("Unable to start receive.")
        return
    client = Client(sock, None)
    receiver = Receiver(client, sender_name)
    t = threading.Thread(target=receive_message, args=(client, ))
    t.daemon = True
    t.start()
    t = threading.Thread(target=send_message, args=(client,))
    t.daemon = True
    t.start()
    receivers.append(receiver)
    receiver.receive_info()
    receiver.start_receive()
    

def manage_communication(client):
    global zone_closed
    while configs.running or not zone_closed:
        msg = client.received_msg.get()
        if not msg:
            continue
        type_, topic, sender = msg.get_headers("type", "topic", "sender")
        if type_ == "attendance":
            logger.info(sender)
            continue
        if type_ == "info" and topic == "cancel":
            cancelled.append(msg.get_headers("filename")[0])
            logger.info(cancelled)
            continue
        elif type_ == "news":
            if msg.content == zone_host + " has left the Zone.":
                zone_closed = True
                continue
            if msg.content == configs.visiting + " has left the Zone.":
                configs.visiting = ''
            for visitor in configs.visitors.copy():
                if msg.content == visitor + " has left the Zone.":
                    try:
                        configs.visitors.remove(visitor)
                        visitors_data.pop(visitor)
                    except:
                        pass
            news.append(msg)
        elif type_ == "chat":
            received_chats.append(msg)
        elif type_ == "close":
            zone_closed = True
        elif type_ == "request" and topic == "share":
            share_reqs.append(msg)
        elif type_ == "request" and topic == "visit":
            visit_reqs.append(msg)
        elif type_ == "command" and sender in configs.visitors:
            visitors_command.put(msg)
        elif (type_ == "info" and topic == "inform") or type_ == "bytes":
            public_shares.put(msg)
        else:
            
            for i, ex in enumerate(expecteds):
                if ex == (type_, topic):
                    logger.info(ex)
                    deliveries[i] = msg
                    break


class Client:
    
    def __init__(self, sock, addr):
        
        self.socket = sock
        self.addr = parsers.get_id(addr) if addr else None
        self.intro = {}
        self.messages = queue.Queue()
        self.received_msg = queue.Queue()
        self.is_active = True
        self.last_contact = None
    
    def _receive_single(self, size=configs.BODY_SIZE, first=False, urgent=False):
        
        if urgent:
            lock.acquire()
        msg = b''
        if not first and (not configs.running or not self.is_active):
            if urgent:
                lock.release()
            return None
        try:
            msg = self.socket.recv(size)
        except Exception as exc:
            self.is_active = False
            if configs.server_id:
                remove_client(self)
            if urgent:
                lock.release()
            return None
        else:
            if urgent:
                lock.release()
            return msg
    
    def receive(self, first=False):
        
        
        headers_bytes = self._receive_single(configs.HEADER_SIZE, first)
        if not headers_bytes:
            return None
        try:
            headers = parsers.Message.from_bytes(headers_bytes).get_headers()
        except:
            s = headers_bytes.find(b"type")
            if s >= 0:
                headers_bytes = headers_bytes[s:]
                try:
                    headers = parsers.Message.from_bytes(headers_bytes).get_headers()
                except:
                    return
            else:
                return
        msg_len = int(headers.get("length", 0))
        message = b''
        remaining = msg_len
        
        while remaining > 0 and ((configs.running and self.is_active) or first):
            size = min((configs.BODY_SIZE, remaining))
            chunk = self._receive_single(size, first)
            if not chunk:
                continue
            message += chunk
            remaining = msg_len - len(message)
        full_msg = headers_bytes + message
        if not full_msg:
            return None
        try:
            return parsers.Message.from_bytes(full_msg)
        except:
            return None
    
    def send(self, msg, first=False, urgent=False):
        
        if urgent:
            lock.acquire()
        if not first and (not configs.running or not self.is_active):
            if urgent:
                lock.release()
            return False
        try:
            if self.addr and configs.server_id:
                try:
                    msg.headers["receiver"] = self.intro['name']
                    receiver_ip = parsers.get_addr(self.addr)[0]
                    msg.headers['receiver_ip'] = receiver_ip
                except:
                    pass
            msg = bytes(msg)
            self.socket.sendall(msg)
        except Exception as exc:
            self.is_active = False
            if configs.server_id:
                remove_client(self)
            if urgent:
                lock.release()
            return False
        else:
            if urgent:
                lock.release()
            return True
    
    def __eq__(self, client):
        res = self.intro.get("name", "") == client.intro.get("name", "")
        return res


class Sender:
    
    def __init__(self, sender, items=[], receiver="", public=False):
        
        self.sender = sender
        if items:
            if type(items) is str:
                if os.path.exists(items):
                    self.items = [os.path.abspath(items)]
                else:
                    self.items = []
            elif type(items) in (list, tuple, set):
                self.items = [os.path.abspath(item) for item in items]
            else:
                self.items = []
        
        self.dirmaps = [parsers.dirmap(item) for item in self.items]
        self.files = [item for item in self.items if os.path.isfile(item)]
        for item in self.items:
            if os.path.isdir(item):
                for f in parsers.traverse_dir(item):
                    self.files.append(f)
        self.status = {}
        self.receiver = receiver
        self.public = public
        self.started = int(datetime.datetime.now().timestamp())
    
    def inform(self):
        self.files = list(set(self.files))
        headers = {
            "type": "info",
            "topic": "inform",
            "to": self.receiver
        }
        info = {"dirmap" + str(i): dirmap for i, dirmap in enumerate(self.dirmaps)}
        info["total_size"] = self.total_size()
        msg = parsers.Message.info(info, headers)
        self.sender.messages.put(msg)
        configs.data['sending_sessions'] += 1
    
    def total_size(self):
        
        size = 0
        for file in self.files:
            size += os.path.getsize(file)
        return size
    
    def sendall(self):
        
        file_titles = [f for dirmap in self.dirmaps for f in parsers.parse_dirmap(dirmap) if f[-1] not in "/\\"]
        
        self.status = {
            "total size": self.total_size(),
            "sent size": 0,
            "files": len(self.files),
            "completed": 0,
            "sending": None,
            "size": 0,
            "sent": 0,
            "chunks": 0,
            "sent chunks": 0,
            "records": {},
        }
        for file in self.files:
            title = ""
            for t in file_titles:
                if t in file:
                    title = t
                    break
            sent = 0
            size = os.path.getsize(file)
            chunks = math.ceil(size / configs.BODY_SIZE)
            self.status["sending"] = title
            self.status["size"] = size
            self.status["chunks"] = chunks
            stats = os.stat(file)
            headers = {
                "type": "bytes",
                "files": self.status["files"],
                "total size": self.status["total size"],
                "filename": title,
                "filesize": size,
                "chunks": chunks,
                "sent": 0,
                "completed": 0,
                "atime": stats.st_atime,
                "mtime": stats.st_mtime,
                "to": self.receiver
            }
            configs.data['total_sent'] += size
            with open(file, "rb") as f:
                for i in range(chunks):
                    chunk = i + 1
                    data_chunk = f.read(configs.BODY_SIZE)
                    sent += len(data_chunk)
                    self.status["records"][title] = [sent, size, False]
                    self.status["sent size"] += len(data_chunk)
                    self.status["chunk"] = chunk
                    self.status["sent"] = sent
                    headers["chunk"] = chunk
                    headers['sent'] = sent
                    headers["sent size"] = self.status["sent size"]
                    headers["completed"] = self.status["completed"]
                    if "all" in cancelled:
                        for fl in self.status['records']:
                            self.status['records'][fl][2] = True
                        return
                    if any(f in title for f in cancelled):
                        self.status['records'][title][2] = True
                        
                        break
                    if any(f in title for f in cancelled):
                        self.status['records'][title][2] = True
                        continue
                    msg = parsers.Message(data_chunk, headers)
                    self.sender.messages.put(msg)
            self.status["completed"] += 1
    
    def finish_up(self):
        last_msg = self.sender.received_msg.get()
        cancelled.clear()
        time.sleep(0.5)
        self.sender.is_active = False
        try:
            self.sender.socket.close()
        except:
            pass
        logger.info("finishing up")


class Receiver:
    
    def __init__(self, receiver, sender="", public=False):
        
        self.receiver = receiver
        self.files = []
        self.dirmaps = []
        self.received_size = 0
        self.completed = 0
        self.total_size = 0
        self.sender = sender
        self.abspaths = {}
        self.public = public
        self.status = {
            "total size": 1,
            "received size": 0,
            "files": 1,
            "completed": 0,
            "receiving": None,
            "size": 1,
            "received": 0,
            "chunks": 0,
            "received chunks": 0,
            "records": {}
        }
        self.started = int(datetime.datetime.now().timestamp())
    
    def receive_info(self):
        
        if self.public:
            msg = public_shares.get()
        else:
            msg = self.receiver.received_msg.get()
        lock.acquire()
        if msg.get_headers("type", "topic") != ("info", "inform"):
            if self.public:
                public_shares.put(msg)
            else:
                self.receiver.received_msg.put(msg)
            time.sleep(0.5)
            self.receive_info
            lock.release()
            return False
        lock.release()
        info = msg.content
        self.dirmaps = [info[key] for key in info if key.startswith("dirmap")]
        for dirmap in self.dirmaps:
            for f in parsers.parse_dirmap(dirmap):
                if os.sep != "\\" and "\\" in f:
                    f = f.replace("\\", "/")
                if os.sep != "/" and "/" in f:
                    f = f.replace("/", "\\")
                lock.acquire()
                dirname = os.path.dirname(f)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
                if f[-1] not in "/\\":
                    self.status['records'][f] = [0, 1, False]
                    self.abspaths[f] = os.path.join(configs.data['home_dir'], f)
                    self.files.append(f)
                    with open(f, "wb") as fl:
                        pass
                lock.release()
        try:
            self.total_size = int(info["total_size"])
        except:
            try:
                self.total_size = int(info["total_size"][:-1])
            except:
                return False
        self.status['total size'] = self.total_size
        self.status['files'] = len(self.files)
        configs.data['receiving_sessions'] += 1
        return True
    
    def start_receive(self):
        
        not_to_take = set()
        while configs.running and self.received_size < self.total_size:
            if self.public:
                
                msg = public_shares.get()
            else:
                msg = self.receiver.received_msg.get()
            if msg.get_headers("type", "topic") == ("info", "done"):
                self.finish_up()
                
                return
            infos = msg.get_headers("filename", "filesize", "chunks", "chunk", "sent size", "sent", "completed")
            if any(info is None for info in infos):
                logger.error(msg)
            file, self.received_size, self.completed = infos[0], int(infos[4]), int(infos[-1])
            if os.sep != "\\" and "\\" in file:
                file = file.replace("\\", "/")
            if os.sep != "/" and "/" in file:
                file = file.replace("/", "\\")
            self.status["received size"] = int(infos[4])
            self.status["receiving"] = infos[0]
            self.status["size"] = int(infos[1])
            self.status["received"] = int(infos[-2])
            self.status["chunks"] = int(infos[2])
            self.status["received chunks"] = int(infos[3])
            self.status["records"][file] = [self.status["received"], self.status["size"], False]
            if "all" in cancelled:
                for file in self.status['records']:
                    self.status['records'][file][2] = True
                for file in self.abspaths.values():
                    if os.path.exists(file):
                        os.unlink(file)
                self.finish_up()
                return
            if any(f in file for f in cancelled):
                
                if file not in not_to_take:
                    self.received_size -= int(infos[-2])
                    self.received_size += int(infos[1])
                not_to_take.add(file)
                if os.path.exists(file):
                    os.unlink(file)
                self.status["records"][file][2] = True
                continue
            if file in not_to_take:
                continue
            with open(self.abspaths[file], "ab") as f:
                f.write(msg.content)
            if infos[2] == infos[3]:
                configs.data['total_received'] += int(infos[1])
                self.status["completed"] += 1
                a_time, m_time = msg.get_headers("atime", "mtime")
                if a_time is not None and m_time is not None:
                    a_time = float(a_time)
                    m_time = float(m_time)
                    os.utime(self.abspaths[file], (a_time, m_time))
        self.finish_up()
        return True
    
    def finish_up(self):
        last_msg = parsers.Message("", {"type": "finish"})
        self.receiver.messages.put(last_msg)
        time.sleep(0.5)
        try:
            self.sender.socket.close()
        except:
            pass
        self.receiver.is_active = False
        logger.info("Finishing up")
        cancelled.clear()


#name: assets.py
#updated: 1610600175
