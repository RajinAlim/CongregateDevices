import os
import shutil
import sys
import time
import json
import subprocess
try:
    from src.python import maintainer
    from src.python import configs
    from src.python import executor
except Exception as exc:
    try:
        import maintainer
        missing = maintainer.organize()
        if missing:
            print("Some essential files are missing: \n\t", "\n\t".join(map(os.path.basename, missing)), sep="")
            download = input("Download them?(y/n): ").strip().lower() == "y"
            if download:
                maintainer.congregate_files(".", True)
                try:
                    shutil.rmtree("CongregateDevices")
                except:
                    pass
                for i, file in enumerate(missing):
                    path = maintainer.download_file(file, ".")
                    if path is None:
                        print("Failed to download", os.path.basename(file))
                        continue
                    print("Downloaded", os.path.basename(file))
                    count = i + 1
                    print("Remaining", len(missing) - count)
                missing = maintainer.organize()
                if not missing:
                    print("All missing files were successfully downloaded! You have to reopen 'main.py'.\nExiting programme. Please reopen (or rerun) 'main.py'.")
                    try:
                        maintainer.congregate_files("..", True)
                        shutil.rmtree("CongregateDevices")
                    except:
                       pass
                    sys.exit()
                else:
                    print("Failed to collect all essential files.Please manually download all the files from", "https://drive.google.com/folderview?id=1-XeM32MuvnqhXOmda4uIU004iJsqXMII")
                    maintainer.congregate_files(".", True)
                    try:
                        shutil.rmtree("CongregateDevices")
                    except:
                        pass
                    sys.exit()
            else:
                print("Cannot continue without these files.")
                maintainer.congregate_files(".", True)
                try:
                    shutil.rmtree("CongregateDevices")
                except:
                    pass
                sys.exit()
        else:
            print(f"All files have been organized accordingly.You are ready to use this programme! You just have to reopen (or rerun) 'main.py'.\nFrom now, when you want to use this programme, you have to run 'main.py' file which is located at '{maintainer.project_dir.replace('/storage/emulated/0', 'Internal Storage')}' folder.")
            print("Exiting programme. Please reopen (or rerun) 'main.py'.")
            sys.exit()
    except Exception as exc:
        print("Unable to find a very important file. Please manually download all the files from", "https://drive.google.com/folderview?id=1-XeM32MuvnqhXOmda4uIU004iJsqXMII")
        sys.exit()


available_updates = maintainer.available_update()
if available_updates:
    print("Following files have updated by developer:")
    for data in available_updates:
        file, date = data
        file = os.path.basename(file)
        print(file, "Updated on", date)
    update = input("Download updates?(y/n) :").strip().lower() == "y"
    if update:
        for i, data in enumerate(available_updates):
            count = i + 1
            file, date = data
            path = maintainer.download_file(file)
            if path is None:
                print("Failed to download", os.path.basename(file))
                if i == 0:
                    break
                continue
            print("Downloaded", os.path.basename(file))
            print("Remaining", len(available_updates) - 1)
        else:
            print(len(available_updates), "file(s) successfully updated. Exiting programme. Kindly reopen (rerun 'main.py').")
            sys.exit()
    print()

time_track = time.time()
warned = False
while True:
    if configs.visiting:
        prompt = "(in " + configs.visiting  + "'s device) "  + configs.PROMPT
    else:
        prompt = configs.PROMPT
    cmd = input(prompt).strip()
    if cmd:
        configs.data['total_commands'] += 1
    current_time = time.time()
    interval = current_time - time_track
    interval = int(interval)
    configs.data['total_time'] += interval
    time_track = current_time
    output, news, chats = executor.execute(cmd)
    if cmd:
        if output:
            print(output)
    if news:
        print("Updates:", "\n".join(news), sep="\n")
    if chats:
        print("Messages:", "\n".join(chats), sep='\n')
    if not configs.joined:
        available = executor.check()
        if type(available) is tuple:
            host, zone_id = available
            print(host + "'s Zone with", zone_id, "Zone ID is available.")
            join = input("Join " + host + "'s Zone? (y/n): ").strip().lower() == "y"
            if join:
                print(executor.execute("join " + zone_id)[0])
    if configs.running and configs.client and not configs.server_id and configs.client.last_contact:
        now = time.time()
        interval = abs(now - configs.client.last_contact)
        if interval >= 375:
            print("Left Zone because there is no response from Zone in last 6 minutes.")
            executor.leave(True)
        elif interval >= 180 and not warned:
            warned = True
            print("No response from Zone in last 3 minutes")
    time.sleep(0.1)

"""Project: Congregate Devices.
Author: Rajin Alim.
Last Updated Wednesday, 06 January 2021, 07:36 PM"""


#name: main.py
#updated: 1609940002
