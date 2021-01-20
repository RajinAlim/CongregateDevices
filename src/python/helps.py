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
    "details": "Run 'details {item}' command to get some basic details about any file or folder.",
    "select": """Run 'select {item}' command to select any item, here {item} can be any file or folder.\nRun 'select all' command to select everything in your current working directory.
Selecting the most flexible feature of this programme. You can specify some conditions and items meeting all conditions will be selected. Here are the conditions and rules of specifying them:
time:
prefix: 'tm:' / 'time:'
format: 'tm:{time(now/today/yesterday/'DD-MM-YYYY HH:MM:SS')}'
description: this take the items who were modified or created at a specific time.
examples:
=>'tm:now' will take all the items who were created or modified at this second.
=>'tm:today' will take all the items who were created or modified today.
=>'tm:yesterday' will take all the items who were created or modified yesterday.
=>'tm:07-04-2018' will take all the items who were created or modified on 7 April 2018.
=>'tm:27-06-2018 16:30' will take all the items who were created or modified on 27 June 2018 4:30 pm.

time limit:
prefix: 'in:'
format: 'in:{amount of time}{unit('y' for year, 'm' for month, 'w' for week, 'd' for day, 'h' for hour, 'min' for minute, 's' for second)}'
description: this condition checks if a file was modified or created before a certain amout of time. 
examples:
=>'in:1w' will match the items which were modifed of creation in last 1 week.
=>'in:2m' will match any item(file or folder) which was created or modified in last 2 months.
=>'in:15min' will match any item(file or folder) which was created or modified in last 15 minutes.

time limit (items between 2 specific times):
prefix: 'tm:' / 'time:'
format: 'tm:{time1(now/today/yesterday/'DD-MM-YYYY HH:MM:SS')}-{time2(now/today/yesterday/'DD-MM-YYYY HH:MM:SS')}'
description: this condition will match any items(files or folders) which were modified between {time1} and {time2}.note that in hour minute and seconds are optional if any or both of the times are specified in 'DD-MM-YYYY HH:MM:SS' format.
examples:
=>'tm:yesterday-now' will match all items which were created or modified between yesterday 12:00 am and now.
=>'tm:today-now' will match all items which were created or modified between today 12:00 am and now.
=>'tm:10-12-2020-now' will match all items which were created or modified between 10 December 2020 12:00 am and now.
=>'tm:10-12-2020-now' will match all items which were created or modified between 10 December 2020 12:00 am and now.
=>'tm:03-07-2020-29-06-2020' will match all items which were created or modified between 3 July 2020 12:00 am and 29 June 2020 12:00 am.
=>'tm:10-01-2020 17:15-29-01-2020' will match all items which were created or modified between 10 January 2020 5:15 pm and 29 January 2020 12:00 am.
=>'tm:03-02-2020 10:00-28-02-2020 14:00' will match all items which were created or modified between 3 February 2020 10:00 am and 28 February 2020 2:00 pm.

item:
prefix: 'i:' / 'item:'
formats: 'i:{n}', 'i:{m} {n} {o}...', 'i:{m}-{n}'
description: '{n}' will match the nth item of current working directory. '{m} {n} {o}...' will match mth, nth, oth, ... items of current working directory. '{m}-{n}' will match from mth to nth items in current working directory.
examples:
=>'i:5' will match the 5th item of current working directory.
=>'i:2 6 12 16' will match 2nd, 6th, 12th and 16th items of current working directory.
=>'i:13-20' will match 13th, 14th, 15th, 16th, 17th, 19th and 20th items in current working directory.

size:
prefix: 's:' / 'size:'
format: 's:{size}'
description: this condition matches the files of specific size.
examples:
=>'s:45kb' will match all items (files or folderss) of 45kb size.
=>'s:562mb' will match all items which's size are 562mb.
=>'s:2.5gb' will match all items which's size are 2.5gb.

size limit:
prefix: 's:" / 'size:'
format: 's:{minimum size}-{maximum size}'
description: this condition will match all files which sizes are between {minimum size} and {maximum size}
examples:
=>'s:5mb-10mb' will match any files which's size is more than or equal to 5mb and less than or equal to 10mbl

type:
prefix: 'tp:' / 'type:'
format: 'tp:{extension}/image/photo/audio/video/file/folder/directory'
description: this condition matches items of specific type.
examples:
=>'tp:image' or 'tp:photo' will match all the images in current working directory.
=>'tp:audio' will match all the audios in current working directory.
=>'tp:video' will match all the videos in current working directory.
=>'tp:.pdf' will match all files with .pdf extensions in current working directory.
=>'tp:file' will match any kind of file (except folders) in current working directory.
=>'tp:folder' or 'tp:dir' or 'tp:directory' will match all folders (except files) in current working directory.

keyword:
prefix: (No prefix, any condition without prefix is recognised as keyword)
formats: {keyword(no space)}, "{anything}", '{anything}'
description: any condition without prefix is recognised as keyword. any text inside single or double quote is also recognised as keyword. all items who contain the keyword in their name will be takes. keyword can be also regular expressions, any items whose name contains match of the regular expressions will be taken (ignore this line if you don’t know about regular expression).

amout of items to take:
prefix: 't:' / 'take:'
formats: 't:f-{n}', 't:l-{n}', 't:{k}-{n}'
description: this condition specifies how many items to take and from where to take.
examples:
=>'t:f-15' will take only the first 15 items.
=>'t:l-10' will take only the last items.
=>'t:5-10' this will separate the items in some groups, each group will have 10 members and the 5th group will be taken.

consideration limit:
prefix: 'cons' / 'consider'
format: 'cons:{n}', 'cons:{m} {n} {o}...', 'cons:{m}-{n}'
description: this condition will specify which items will be considered for selection
examples:
=>'cons:5' will make only the 5th item of current working directory considered for selection.
=>'cons:2 6 12 16' will make only 2nd, 6th, 12th and 16th items of current working directory considered for selection.
=>'cons:13-20' will make only 13th, 14th, 15th, 16th, 17th, 19th and 20th items in current working directory considered for selection.

ingore (with 'ign:' prefix):
prefix: 'ign:' / 'ignore:'
format: 'ign: {condition}'
description: this will remove the items which meet {conditions} from consideration list. Here {condition} can be one or more conditions from above.
examples:
=>'ignore: tm:today tp:.py' will remove the items who meet 'tm:today' and 'tp:.py' from consideration list.
You can mix up one or multiple conditions to get your desired items selected. If more than one condition is provided then only those items will be selected who meet all the conditions.
Selecting will help you to share multiple items at once.""",
    "unselect": "Run 'unselect {item}' to unselect any of the items you selected, here {items} will be the file or folder to unselect.You can also run 'unselect all' command to unselect all the items you selected.\nRun 'unselect {n}' command to unselect the nth item from the selected items.For example, to unselect 3rd item from selected items run 'unselect 3' command.\nRun 'unselect {m} {n} {p}' command to unselect the mth, nth and pth item from selected items.For example to unselect 1st, 2nd and 3rd item from selected items run 'unselect 1 2 3'.In this way, you can unselect as much items you want.\nRun 'unselect {m}-{n}' to unselect from mth to nth item from selected items.For example, to unselect 3rd to 10th items from selected items run 'unselect 3-10' command.",
    "search": """Run 'search {condition}' start search from current working directory (in Android phone this will search the whole phone!) with {conditions}.\nRun 'search {condition} in {folder}' start search from {folder} with {conditions}.{conditions} is described below:
time:
prefix: 'tm:' / 'time:'
format: 'tm:{time(now/today/yesterday/'DD-MM-YYYY HH:MM:SS')}'
description: this take the items who were modified or created at a specific time.
examples:
=>'tm:now' will take all the items who were created or modified at this second.
=>'tm:today' will take all the items who were created or modified today.
=>'tm:yesterday' will take all the items who were created or modified yesterday.
=>'tm:07-04-2018' will take all the items who were created or modified on 7 April 2018.
=>'tm:27-06-2018 16:30' will take all the items who were created or modified on 27 June 2018 4:30 pm.

time limit:
prefix: 'in:'
format: 'in:{amount of time}{unit('y' for year, 'm' for month, 'w' for week, 'd' for day, 'h' for hour, 'min' for minute, 's' for second)}'
description: this condition checks if a file was modified or created before a certain amout of time. 
examples:
=>'in:1w' will match the items which were modifed of creation in last 1 week.
=>'in:2m' will match any item(file or folder) which was created or modified in last 2 months.
=>'in:15min' will match any item(file or folder) which was created or modified in last 15 minutes.

time limit (items between 2 specific times):
prefix: 'tm:' / 'time:'
format: 'tm:{time1(now/today/yesterday/'DD-MM-YYYY HH:MM:SS')}-{time2(now/today/yesterday/'DD-MM-YYYY HH:MM:SS')}'
description: this condition will match any items(files or folders) which were modified between {time1} and {time2}.note that in hour minute and seconds are optional if any or both of the times are specified in 'DD-MM-YYYY HH:MM:SS' format.
examples:
=>'tm:yesterday-now' will match all items which were created or modified between yesterday 12:00 am and now.
=>'tm:today-now' will match all items which were created or modified between today 12:00 am and now.
=>'tm:10-12-2020-now' will match all items which were created or modified between 10 December 2020 12:00 am and now.
=>'tm:10-12-2020-now' will match all items which were created or modified between 10 December 2020 12:00 am and now.
=>'tm:03-07-2020-29-06-2020' will match all items which were created or modified between 3 July 2020 12:00 am and 29 June 2020 12:00 am.
=>'tm:10-01-2020 17:15-29-01-2020' will match all items which were created or modified between 10 January 2020 5:15 pm and 29 January 2020 12:00 am.
=>'tm:03-02-2020 10:00-28-02-2020 14:00' will match all items which were created or modified between 3 February 2020 10:00 am and 28 February 2020 2:00 pm.

item:
prefix: 'i:' / 'item:'
formats: 'i:{n}', 'i:{m} {n} {o}...', 'i:{m}-{n}'
description: '{n}' will match the nth item of current working directory. '{m} {n} {o}...' will match mth, nth, oth, ... items of current working directory. '{m}-{n}' will match from mth to nth items in current working directory.
examples:
=>'i:5' will match the 5th item of current working directory.
=>'i:2 6 12 16' will match 2nd, 6th, 12th and 16th items of current working directory.
=>'i:13-20' will match 13th, 14th, 15th, 16th, 17th, 19th and 20th items in current working directory.

size:
prefix: 's:' / 'size:'
format: 's:{size}'
description: this condition matches the files of specific size.
examples:
=>'s:45kb' will match all items (files or folderss) of 45kb size.
=>'s:562mb' will match all items which's size are 562mb.
=>'s:2.5gb' will match all items which's size are 2.5gb.

size limit:
prefix: 's:" / 'size:'
format: 's:{minimum size}-{maximum size}'
description: this condition will match all files which sizes are between {minimum size} and {maximum size}
examples:
=>'s:5mb-10mb' will match any files which's size is more than or equal to 5mb and less than or equal to 10mbl

type:
prefix: 'tp:' / 'type:'
format: 'tp:{extension}/image/photo/audio/video/file/folder/directory'
description: this condition matches items of specific type.
examples:
=>'tp:image' or 'tp:photo' will match all the images in current working directory.
=>'tp:audio' will match all the audios in current working directory.
=>'tp:video' will match all the videos in current working directory.
=>'tp:.pdf' will match all files with .pdf extensions in current working directory.
=>'tp:file' will match any kind of file (except folders) in current working directory.
=>'tp:folder' or 'tp:dir' or 'tp:directory' will match all folders (except files) in current working directory.

keyword:
prefix: (No prefix, any condition without prefix is recognised as keyword)
formats: {keyword(no space)}, "{anything}", '{anything}'
description: any condition without prefix is recognised as keyword. any text inside single or double quote is also recognised as keyword. all items who contain the keyword in their name will be takes. keyword can be also regular expressions, any items whose name contains match of the regular expressions will be taken (ignore this line if you don’t know about regular expression).

amout of items to take:
prefix: 't:' / 'take:'
formats: 't:f-{n}', 't:l-{n}', 't:{k}-{n}'
description: this condition specifies how many items to take and from where to take.
examples:
=>'t:f-15' will take only the first 15 items.
=>'t:l-10' will take only the last items.
=>'t:5-10' this will separate the items in some groups, each group will have 10 members and the 5th group will be taken.

consideration limit:
prefix: 'cons' / 'consider'
format: 'cons:{n}', 'cons:{m} {n} {o}...', 'cons:{m}-{n}'
description: this condition will specify which items will be considered for selection
examples:
=>'cons:5' will make only the 5th item of current working directory considered for selection.
=>'cons:2 6 12 16' will make only 2nd, 6th, 12th and 16th items of current working directory considered for selection.
=>'cons:13-20' will make only 13th, 14th, 15th, 16th, 17th, 19th and 20th items in current working directory considered for selection.

ingore (with 'ign:' prefix):
prefix: 'ign:' / 'ignore:'
format: 'ign: {condition}'
description: this will remove the items which meet {conditions} from consideration list. Here {condition} can be one or more conditions from above.
examples:
=>'ignore: tm:today tp:.py' will remove the items who meet 'tm:today' and 'tp:.py' from consideration list.\
You can mix up one or multiple conditions to get your desired items selected. If more than one condition is provided then only those items will be selected who meet all the conditions.
search traverse a directory and will get all the files meeting contidions selected.
""",
    "protect": "Run 'protect {item}' command to hide any file or folder from visitors, here {item} can be name or path of a file or folder.\nRun 'protect {n}' command to protect the nth item of your current working directory.For example, to protect 3rd item of your current working directory run 'protect 3' command.\nRun 'protect {m} {n} {p}' command to protect the mth, nth and pth item of your current working directory.For example to protect 1st, 2nd and 3rd item of your current working directory run 'protect 1 2 3'.In this way, you can protect as much item you want.\nRun 'protect {m}-{n}' to protect from mth to nth item of your current working directory.For example, to protect 3rd to 10th items in your current working directory run 'protect 3-10' command.\nRun 'protect selected' command to hide the selected from visitors.\nRun 'protect all' command to protect everything in your current working directory.\nProtected items are hidden from visitors, this feature is for protecting users' privacy.",
    "unprotect": "Run 'unprotect {item}' command remove a file or folder from the list of protected items, which will make the file or folder visible to visitors.\nRun 'unprotect {n}' command to unprotect the nth item from the protected items.For example, to unprotect 3rd item from protected items run 'unprotect 3' command.\nRun 'unprotect {m} {n} {p}' command to unprotect the mth, nth and pth item from protected items.For example to unprotect 1st, 2nd and 3rd item from protected items run 'unprotect 1 2 3'.In this way, you can unprotect as much items you want.\nRun 'unprotect {m}-{n}' to unprotect from mth to nth item from protected items.For example, to unprotect 3rd to 10th items from protected items run 'unprotect 3-10' command.",
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
    "how to": "Run 'how to share' to see an example how to share files between two devices.",
    "p": "This is a shortcut to run the previous command. Run 'p' command to run the previous command you ran."
}
formats = {
    "pwd": "pwd",
    "ls": "ls",
    "cd": "cd {directory}",
    "dirmap": "dirmap, dirmap {directory}",
    "details": "details {item}",
    "select": "select {item}, select all, select {conditions}",
    "unselect": "unselect {item}, unselect all, unselect {n}, unselect {m}-{n}, unselect {m} {n} {o} {p}...",
    "search": "search {conditions}, search {conditions}",
    "protect": "protect {item}, protect all, protect selected, protect {n}, protect {m}-{n}, protect {m} {n} {o} {p}...",
    "unprotect": "unprotect {item}, unprotect all, unprotect selected, unprotect {n}, unprotect {m}-{n}, unprotect {m} {n} {o} {p}...",
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
    drive_link = "https://drive.google.com/drive/folders/10TGK4auocqd7sYTlOhwRDmd_c2t8cRxf"
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
#updated: 1611150762
