from src.python import configs
from src.python.parsers import pretify_path

summery = f"Congregate your and your friends' devices!\nConnect to a wifi, start a Zone by running 'start' command, and make your friends who are connected to same wifi join your Zone using the Zone ID.Once you have started a Zone, anyone in same wifi (or LAN) can join your Zone with Zone ID after your approval.You and others who will join the Zone must be in same Local Network (wifi).\nOr you can also turn on hotspot, make your friends connect to your hotspot. Then one of your friends (NOT YOU!) can start a Zone, then you and others (must be connected to your hotspot) can join the Zone using Zone ID.\nOnce you have joined a Zone you chat with other members in the Zone, share files with any member in the Zone.Maximum number of members in a single Zone is {configs.MAX_MEMBERS}.\nAll activities have to be done by running specifc commands.\nCommands checked very strictly, any mistake in spelling or format will make the command considered as invalid.\nRun 'view commands' command to see all runnable commands and their valid formats.\nOr consider running 'help all' command to know everything about all runnable commands."
example = """This project is not GUI based. So it is unusual if anybody knows how to use this programme properly at starting. Sharing is the main purpose of this project. There is an example below how to share files between two device.
Suppose you have to share some photos (or anything) with your friend (or anyone), then the following actions has to be performed:
1.Turn on hotspot in your device and make your friend connect to your hotspot.
2.Tell your friend to start a Zone with 'start' command. (You can't do this because hotspot is running on your mobile)
3.After a Zone has been created, your friend will be given a Zone ID which is the key for you to join the Zone.You have to join your friend's Zone with 'join' command which is followed by an space and the Zone ID.Suppose the Zone ID is '3H1 RVGF S41A'. You have to run 'join 3H1 RVGF S41A' command to join your friend's Zone. Then tell your friend to press just enter (run empty command), then your friend will be asked if he wants to allow to you join his Zone or not. If he answers with 'y' you will successfully join the Zone.
4.Then the next task is to select.Navigate to the folder where the photos you want to share is stored by changing working directory (run 'help cd' command to know how to change working directory).Then select the photos you want to share. Selecting is probably the most flexible feature of this programme, run 'help select' command to know how to select.It is always a good practise to change directory to this programme's home directory when work is done. To do this you have to run 'cd home' command.
5.After selecting, you have to run 'share' or 'share with' command to share the files. you can run 'share selected' command to share the files, but this will send the files to all members in the Zone (if there is anyone else in the Zone). To share the photos with only one specific person you have to run 'share with' command.Here how you can do it: Suppose your friend's username is 'Jamp', then you have to run 'share selected with Jamp' command to share the photos only with Jamp. (run 'help share' to know more in details)
6.To know how much of sharing has been completed, run 'share status' command.This is quite meaningless if done on sender's device, this command will give accurate status in receiver's device. So wait until 'share status' command in receiver's device shows 100% complete.
7.After sending is complete Zone can be closed by running 'close' command or you can continue sharing and chatting.Just don't forget to close the Zone after you are done."""
helps = {
    "start": "Run 'start' to create a new Zone.This will give you a Zone ID, which essential for others to join the Zone.",
    "join": "Run 'join {Zone Id}' command to join a Zone.Zone ID must be valid, it should one that is provided when creating the Zone you wish to join.Zone ID will include 11 characters, they will be digits or alphabet.",
    "cd": "Run 'cd {directory}' to change your working directory.\nRun 'cd home' to change your working directory to this programme's home directory.\nBy default your working directory will this programme's home directory, unless you manully change working directoy (run 'help home' to know about home directory). Every file you receive will be stored according to your working directory. ",
    "pwd": "Run 'pwd' command to know your working directory.Every file you receive will be stored according to your working directory.",
    "ls": "Run 'ls' command to get the list of items in current working directory.",
    "dirmap": "Run 'dirmap' to get a visual representation of your working directory.\nRun 'dirmap {directory}' to get visual representation of any directory.",
    "select": "Run 'select {item}' command to select any item, here {item} can be any file or folder.\nRun 'select {part_of_name}' to select any items whose name match the letters in the curly braces.\nRun 'select {n}' command to select the nth item of your current working directory.For example, to select 3rd item of your current working directory run 'select 3' command.\nRun 'select {m} {n} {p}' command to select the mth, nth and pth item of your current working directory.For example to select 1st, 2nd and 3rd item of your current working directory run 'select 1 2 3'.In this way, you can select as much items you want.\nRun 'select {m}-{n}' to select from mth to nth item of your current working directory.For example, to select 3rd to 10th items in your current working directory run 'select 3-10' command.\nRun 'select all' command to select everything in your current working directory.\nSelecting will help you to share multiple items at once.",
    "unselect": "Run 'unselect {item}' to unselect any of the items you selected, here {items} will be the file or folder to unselect.You can also run 'unselect all' command to unselect all the items you selected.\nRun 'unselect {part_of_name}' to unselect any items whose name match the letters in the curly braces.\nRun 'unselect {n}' command to unselect the nth item from the selected items.For example, to unselect 3rd item from selected items run 'unselect 3' command.\nRun 'unselect {m} {n} {p}' command to unselect the mth, nth and pth item from selected items.For example to unselect 1st, 2nd and 3rd item from selected items run 'unselect 1 2 3'.In this way, you can unselect as much items you want.\nRun 'unselect {m}-{n}' to unselect from mth to nth item from selected items.For example, to unselect 3rd to 10th items from selected items run 'unselect 3-10' command.",
    "search": "Run 'search {item}' command to search for a specific keyword in the whole device, here {item} should be a word, any file or directory matching the word will be selected.Note that, this feature is only available in Android phones.",
    "protect": "Run 'protect {item}' command to hide any file or folder from visitors, here {item} can be name or path of a file or folder.\nRun 'protect {part_of_name}' to protect any items whose name match the letters in the curly braces.\nRun 'protect {n}' command to protect the nth item of your current working directory.For example, to protect 3rd item of your current working directory run 'protect 3' command.\nRun 'protect {m} {n} {p}' command to protect the mth, nth and pth item of your current working directory.For example to protect 1st, 2nd and 3rd item of your current working directory run 'protect 1 2 3'.In this way, you can protect as much item you want.\nRun 'protect {m}-{n}' to protect from mth to nth item of your current working directory.For example, to protect 3rd to 10th items in your current working directory run 'protect 3-10' command.\nRun 'protect selected' command to hide the selected from visitors.\nRun 'protect all' command to protect everything in your current working directory.\nProtected items are hidden from visitors, this feature is for protecting users' privacy.",
    "unprotect": "Run 'unprotect {item}' command remove a file or folder from the list of protected items, which will make the file or folder visible to visitors.\nRun 'unprotect {part_of_name}' to unprotect any items whose name match the letters in the curly braces.\nRun 'unprotect {n}' command to unprotect the nth item from the protected items.For example, to unprotect 3rd item from protected items run 'unprotect 3' command.\nRun 'unprotect {m} {n} {p}' command to unprotect the mth, nth and pth item from protected items.For example to unprotect 1st, 2nd and 3rd item from protected items run 'unprotect 1 2 3'.In this way, you can unprotect as much items you want.\nRun 'unprotect {m}-{n}' to unprotect from mth to nth item from protected items.For example, to unprotect 3rd to 10th items from protected items run 'unprotect 3-10' command.",
    "view": "This command helps you to view several informations about the Zone you are in right now, visitors, your current state and some records.\nRun 'view status' command to see current status, this will give you informations about your first use of this programme, Zone info if you are in any Zone, name of the visitors visiting your device and also some interesting records.\nRun 'view members' to see informations about the members of the Zone.\nRun 'view selected' command to see the list of items you selected.\nRun 'view protected' command to see which items are hidden from visitors.\nRun 'view visitors' to get informations about visitors who are visiting your device right now.\nRun 'view history' command to see Zone ID, name of host and time of last join of all Zones you have joined.\nRun 'view commands' command to the list of runnable commands and their valid formats.",
    "chat": "Run 'chat {message}' to send messages accross the Zone, {message} will be sent to all members in the Zone.",
    "zone info": "Run 'zone info' command to get informations the Zone you are in right now.",
    "share": "Run 'share {item}' command to share the item with all members in your Zone, here {item} can be a file or a directory.\nRun 'share selected' to share the selected items with all members in your Zone.Every member of your Zone will get the items if they accepts them.\nRun 'share {item} with {receiver}' command to share items with a specific member in your Zone, here {item} can be a file or a directory and {receiver} should be the username of the receiver.\nRun 'share selected with {receiver}' command to share the selected with specific member in your Zone.Note that receiver has to accept the items, otherwise items won't be shared",
    "share with": "Run 'share {item} with {receiver}' command to share items with a specific member in your Zone, here {item} can be a file or a directory and {receiver} should be the username of the receiver.\nRun 'share selected with {receiver}' command to share the selected with specific member in your Zone.Note that receiver has to accept the items, otherwise items won't be shared",
    "share status": "Run 'share status' command to see status all sharing activities of this session.",
    "visit": "Run 'visit {user}' to visit a user's device, here {user} be the username of the member in your Zone you wish to visit. While visiting, you can run 'pwd', 'ls', 'cd', 'dirmap', 'select', 'unselect' command in the device you are visiting, you can also collect files from the device you are visiting with 'collect' command.Note that, the user you are willing to visit has to accept you as his guest.Otherwise you can't visit him/her.",
    "collect": "Run 'collect {item}' command to collect any item from the device you are visiting.Run 'collect selected' to collect the items you selected in the device your visiting.",
    "cancel": "Run 'cancel {item}' to cancel sending, receiving or collecting a specific item, here {item} should be the name of the item to cancel sharing, any file or directory matching the {item} won't be sent or received.Note that this cannot be undone.",
    "return": "Run 'return' command to return from someone's device, that means run this command when you are done visiting.",
    "throw": "Run 'throw' command to throw all visitors out of your device.\nRun 'throw {user}' command to throw a visitor out of your device, here {user} should be the username of the visitor to throw out.",
    "kick": "Run 'kick {user}' command to kick a user out from the Zone, here {user} should be username of the user of to kick out.Note that only Zone host can do this.",
    "leave": "Run 'leave' command to leave a Zone.",
    "close": "Run 'close' command to close the entire Zone.Note that this will cancel all sharing activities.",
    "exit": "Run 'exit' command to exit this programme.Note that this will cancel all sharing activities and will also close entire Zone if you are the Zone host.",
    "username": "Run 'username {name}' command to change your username, here {name} should be the new username.Note that username can't be changed if you are in a Zone.\nRun 'username' command to see your username.",
    "clear": "Run 'clear' command to clear all records saved by this programme.",
    "about": "Run 'about' command to know about this project and it's author.",
    "help": "Run 'help' command to know how the programme works.\nRun 'help {command}' command to get help any specific command, here {command} should be the command you want to know about.\nRun 'help all' to get help about all commands",
    "share this": "Run 'share this' command to see how to share this programme.",
    "how to": "Run 'how to share' to see an example how to share files between two devices."
}
formats = {
    "pwd": "pwd",
    "ls": "ls",
    "cd": "cd {directory}",
    "dirmap": "dirmap, dirmap {directory}",
    "select": "select {item}, select all, select {n}, select {m}-{n} select {m} {n}.., select {part_of_name}",
    "unselect": "unselect {item}, unselect all, unselect {n}, unselect {m}-{n}, unselect {m} {n}.., unselect {part_of_name}",
    "search": "search {keyword}",
    "protect": "protect {item}, protect all, protect selected, protect {n}, protect {m}-{n}, protect {m} {n}.., protect {part_of_name}",
    "unprotect": "unprotect {item}, unprotect all, unprotect {n}, unprotect {m}-{n}, unprotect {m} {n}.., unprotect {part_of_name}",
    "username": "username, username {new name}",
    "start": "start",
    "join": "join {Zone ID}",
    "chat": "chat {message}",
    "visit": "visit {user}",
    "return": "return",
    "share": "share {item}, share selected",
    "share with": "share {item} with {receiver}, share selected with {receiver}",
    "collect": "collect {item}, collect selected",
    "cancel": "cancel {item}, cancel all",
    "view": "view selected, view protected, view status, view members, view visitors, view history",
    "share status": "share status",
    "kick": "kick {user}",
    "throw": "throw, throw {user}",
    "clear": "clear",
    "leave": "leave",
    "close": "close",
    "help": "help, help {command}",
    "share this": "share this",
    "how to": "how to share",
    "about": "about",
    'exit': "exit",
}

def share_this(path):
    drive_link = "https://drive.google.com/folderview?id=1-XeM32MuvnqhXOmda4uIU004iJsqXMII"
    github_link = "https://github.com/RajinAlim/CongregateDevices"
    print("To use this programme all requirements are the files of this project and any way to run python script.\nFirst let's talk about the second requirement, way to run python script.\nTo run python script in Android phones, QpythonL is probably smallest app. Open Play Store and search 'QpythonL' and download the first one of search results. On other devices, do search for 'how to run python in {os}' ({os} should be whatever operating system you are using) on Youtube.")
    print(f"Let's talk about the second requirement, the files.\nThe files of this programme can be downloaded from Google Drive or Github. Link for both is below:\nGoogle drive link: {drive_link}\nGithub repostory link: {github_link}.\n\nIf you want to do this without Internet, it's okay.Here's how this can be done:")
    print(f"All the files of the project is copied at '{pretify_path(path)}' folder. Share those file (all files in '{path}' folder) with the person you want to share the programme with. You can use Bluetooth or any other way to share those files. Note that QpythonL (or any app to run python) must be installed either from Play Store or anywhere else.")
    print("Once the files of the programme is shared or downloaded in a device, the next task is to run the 'main.py' file in any way you like, in Android phones, using QPythonL or Pydroid3 or any other app that can run python. (if you are using QpythonL, then you can watch this video on youtube: https://youtu.be/XD0N-ZMNfFQ).Then Done!")

def help(topic=None):
    if topic is None:
        return summery
    topic = topic.strip()
    if topic == "all":
        help_str = summery + "\nList of commands:\n\n"
        commands = []
        for command in formats:
            words = "Command: " + command + "\n"
            words += "Formats: " + formats[command] + "\n"
            if command in helps:
                words += "Description: " + helps[command]
            commands.append(words)
        return help_str + "\n\n".join(commands)
    if topic not in helps:
        return "Couldn't recognize topic.Run 'help' to get help."
    help_str = helps[topic]
    if topic in ("share", "share with") and configs.data['total_received'] + configs.data['total_sent'] == 0:
        help_str += "\n\nRun 'how to share' command to see a example how to share files between two devices."
    return help_str


#name: helps.py
#updated: 1610003754
