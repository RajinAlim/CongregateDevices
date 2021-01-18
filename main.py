import os
import shutil
import sys
import time
import json
import subprocess
try:
    from src.python import maintainer
except ImportError as exc:
    try:
        import maintainer
        missing = maintainer.organize()
        if not missing:
            print(f"All files have been organized accordingly.You are ready to use this programme! You just have to reopen (or rerun) 'main.py'.\nFrom now, when you want to use this programme, you have to run 'main.py' file which is located at '{maintainer.project_dir.replace('/storage/emulated/0', 'Internal Storage')}' folder.")
            print("Exiting programme. Please reopen (or rerun) 'main.py'.")
            sys.exit()
        maintainer.congregate_files(".")
        try:
            shutil.rmtree(maintainer.project_dir)
        except:
            pass
        print("Some essential files are missing: \n    ", "\n    ".join(map(os.path.basename, missing)), sep="")
        download = input("Download them?(y/n): ").strip().lower() == "y"
        if download:
            downloaded = 0
            failed = 0
            for file in missing:
                for p, files in maintainer.ESSENTIALS.items():
                    if file in files:
                        title = "/".join((p, file)) if p else file
                path = maintainer.download_file(title, ".")
                if path is None:
                    failed += 1
                    print("Failed to download", file)
                else:
                    downloaded += 1
                    print("Downloaded", file)
            if failed > 0:
                print(f"Failed to download {failed} file{'s' if failed > 1 else ''}. Download {'them' if failed > 1 else 'it'} manually from 'https://drive.google.com/folderview?id=1-XeM32MuvnqhXOmda4uIU004iJsqXMII' or try again later.")
            if failed == 0:
                maintainer.organize()
                print(f"All missing files were successfully downloaded! You have to reopen 'main.py'.\nFrom now, when you want to use this programme, you have to run 'main.py' file which is located at '{maintainer.project_dir.replace('/storage/emulated/0', 'Internal Storage')}' folder.")
                print("Exiting programme. Please reopen (or rerun) 'main.py'.")
            sys.exit()
        else:
            print("Unable to continue without these files.")
            sys.exit()
    except ImportError as exc:
        print("Unable to find a very important file. Please manually download all the files from", "https://drive.google.com/folderview?id=1-XeM32MuvnqhXOmda4uIU004iJsqXMII")
        sys.exit()
try:
    from src.python import configs
    from src.python import executor
    from src.python import parsers
    from src.python import assets
    from src.python import helps
except ImportError as exc:
    os.chdir(maintainer.wd)
    maintainer.congregate_files("src")
    missing = maintainer.organize("..")
    if not missing:
        print(f"There were some leak in files' organizing.No need to worry, all files have been organized accordingly. You just have to reopen (or rerun) 'main.py'.\nFrom now, when you want to use this programme, you have to run 'main.py' file which is located at '{maintainer.project_dir.replace('/storage/emulated/0', 'Internal Storage')}' folder.")
        print("Exiting programme. Please reopen (or rerun) 'main.py'.")
        sys.exit()
    print("Some essential files are missing: \n    ", "\n    ".join(map(os.path.basename, missing)), sep="")
    download = input("Download them?(y/n): ").strip().lower() == "y"
    if download:
        downloaded = 0
        failed = 0
        for file in missing:
            for p, files in maintainer.ESSENTIALS.items():
                if file in files:
                    title = "/".join((p, file)) if p else file
            path = maintainer.download_file(title, ".")
            if path is None:
                failed += 1
                print("Failed to download", file)
            else:
                downloaded += 1
                print("Downloaded", file)
                real_path = os.path.join(maintainer.project_dir ,*title.split("/"))
                shutil.move(path, real_path)
        if failed > 0:
            print(f"Failed to download {failed} file{'s' if failed > 1 else ''}. Download {'them' if failed > 1 else 'it'} manually from 'https://drive.google.com/drive/folders/10TGK4auocqd7sYTlOhwRDmd_c2t8cRxf' or try again later.")
            sys.exit()
        else:
            print("All missing files were successfully downloaded! You have to reopen 'main.py'.\nFrom now, when you want to use this programme, you have to run 'main.py' file which is located at '{maintainer.project_dir.replace('/storage/emulated/0', 'Internal Storage')}' folder.")
            print("Exiting programme. Please reopen (or rerun) 'main.py'.")
            sys.exit()
    else:
        print("Can't continue without these files.")
        sys.exit()
    sys.exit()


available_updates = maintainer.available_update()
if available_updates:
    print("Following files have updated by developer:")
    for data in available_updates:
        file, date = data
        file = file.split("/")[-1]
        print(file, ", Updated on ", date, sep="")
    update = input("Download updates?(y/n) :").strip().lower() == "y"
    if update:
        for i, data in enumerate(available_updates):
            count = i + 1
            file, date = data
            parts = file.split("/")
            path = os.getcwd() if len(parts) == 1 else os.path.join(maintainer.project_dir, *parts[:-1])
            path = maintainer.download_file(file, path)
            if path is None:
                print("Failed to download", os.path.basename(file))
                if i == 0:
                    break
                continue
            print("Downloaded", os.path.basename(file))
            print("Remaining", len(available_updates) - 1)
        else:
            with open(os.path.join(maintainer.project_dir, "src", "python", "maintainer.py")) as f:
                data_to_clear = maintainer.retrieve_history(f.read())
            if data_to_clear is not None and "clear_data" in data_to_clear:
                for key in data_to_clear:
                    if key in configs.data['history']:
                        configs.data['history'].pop(key)
            print(len(available_updates), "file(s) successfully updated. Exiting programme. Kindly reopen (rerun 'main.py').")
            sys.exit()
    print()

time_track = time.time()
warned = False
configs.data["times_launched"] += 1
while True:
    if configs.visiting:
        prompt = "(in " + configs.visiting  + "'s device) "  + configs.PROMPT
    else:
        prompt = configs.PROMPT
    cmd = input(prompt).strip()
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
Last Updated Monday, 18 January 2021, 11:47 AM"""


#name: main.py
#updated: 1610819697
