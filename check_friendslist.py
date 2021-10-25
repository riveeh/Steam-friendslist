import sys
import requests_html
import datetime
import steamapi

# link to your friendslist (remember to set your friendslist to public before running the script!)
steam_user = "id/<your_profile_id>" # either set your id or use steamid64
steam_url = "https://steamcommunity.com/" + steam_user + "/friends/"
# API key from https://steamcommunity.com/dev
APIkey = "<your_steam_API_key>" # steam API key

# list-files
old_list_file = "old_list.txt"
current_list_file = "current_list.txt"
# lists in memory
old_list = []
current_list = []
# new data from steamcommunity.com
steamid64_list = []
# logfile to which the changes are written to
logfile = "friendlist_history.txt"
# flags
missing_flag = False
new_flag = False
# list of old and new friends
missing_list = []
new_list = []


def steamapi_init():
    global APIkey
    steamapi.core.APIConnection(api_key=APIkey, validate_key=True)

def get_friendlist():
    print("[*] Retrieving friendlist from", steam_url)
    session = requests_html.HTMLSession()
    r = session.get(steam_url)
    friends = r.html.find('#search_results', first=True)
    friends_data = friends.find()
    friendslist = []
    for x in range(len(friends_data)):
        if 'data-steamid' in str(friends_data[x]):
            friendslist.append(str(friends_data[x]))

    for element in friendslist:
        startindex = element.find('data-steamid')
        # endindex = element.find('>') # fails when a steamuser has a ">" in his name
        # needed offset since format is [..]data-steamid='76561198006382745'[..]
        offset = 'data-steamid='
        # -2 to remove '>" symbols from the end, steam64 should always be last
        # 08/01/2021
        # steam updated website, data-steamid='<steamid64>' still valid
        # now followed by data-miniprofile
        data_miniprofile_index = element.find('data-miniprofile')
        steamid64_list.append(element[startindex+len(offset)+1:data_miniprofile_index-2])

    steamid64_list.sort()

    print("[*] Updating", current_list_file)
    with open(current_list_file, 'w') as f:
        for x in steamid64_list:
            if x == '': continue # no entry for empty name
            f.write(x + "\n")
    return None

def compare_friends():
    global missing_flag, new_flag, current_list, old_list
    try:
        current_list = [line.strip() for line in open(current_list_file, 'r')]
    except FileNotFoundError:
        print("[-] File", current_list_file,
              "could not be found.", file=sys.stderr)
    try:
        old_list = [line.strip() for line in open(old_list_file, 'r')]
    except FileNotFoundError:
        print("[-] File", old_list_file,
              "could not be found.", file=sys.stderr)

    print("Current friends:", len(current_list))
    print("Before:", len(old_list))

    for x in old_list:
        if x not in current_list:
            missing_list.append(x)
            missing_flag = True

    for x in current_list:
        if x not in old_list:
            new_list.append(x)
            new_flag = True

    if not missing_flag and not new_flag:
        print("Nothing has changed.")
        return None

    if missing_flag:
        print("[-] Missing:")
        for x in missing_list:
            try:
                print(x + " [" + str(steamapi.user.SteamUser(x)) + "]")
            except Exception as e:
                print("[-] error when fetching data from steampi:", e)
                print(x + "\n")
    if new_flag:
        print("[+] New:")
        for x in new_list:
            try:
                print(x + " [" + str(steamapi.user.SteamUser(x)) + "]")
            except Exception as e:
                print("[-] error when fetching data from steampi:", e)
                print(x + "\n")

    return None

def log_check():
    now = datetime.datetime.now()
    with open(logfile, 'r') as f:
        text = f.read()
    with open(logfile, 'w') as f:
        # write timestamp and current/old friendcount to logfile
        f.write(now.strftime("%d/%m/%Y %H:%M:%S") + "\n")
        f.write("[*] Current friends: " + str(len(current_list)) + " (" + str(len(old_list)) + ")" + "\n")
        
        if missing_flag:
            f.write("[-] Missing friend(s):\n")
            for x in missing_list:
                try:
                    f.write(
                        x + " [" + str(steamapi.user.SteamUser(x)) + "]" + "\n")
                except Exception as e:
                    print("[-] error when fetching data from steampi:", e)
                    f.write(x + "\n")
        if new_flag:
            f.write("[+] New friend(s):\n")
            for x in new_list:
                try:
                    f.write(
                        x + " [" + str(steamapi.user.SteamUser(x)) + "]" + "\n")
                except Exception as e:
                    print("[-] error when fetching data from steampi:", e)
                    f.write(x + "\n")

        if not missing_flag and not new_flag:
            f.write("[*] Nothing has changed.\n")

        f.write("\n")
        # append previous text to new log-entry (so newest entry is on top)
        f.write(text)

    return None

def write_old():
    if not new_flag and not missing_flag:
        print("[*] Nothing has changed.")
        return None
    else:
        print("[*] Updating", old_list_file)
        with open(old_list_file, 'w') as f:
            for x in current_list:
                f.write(x + "\n")
    return None

if __name__ == "__main__":
    # connect to steam api using the api key
    steamapi_init()
    # get friendlist from steamcommunity.com and write to [current_list_file]
    get_friendlist()
    # compare list from [current_list_file] with list from [old_list_file]
    compare_friends()
    # update [old_list_file] with new data
    write_old()
    # write changes to [logfile]
    log_check()
    exit(0)
