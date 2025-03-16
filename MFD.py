from tqdm import tqdm
import requests
import json
import time
import sys
import csv

def Write_CSV(csv_data):
    with open('User_Data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)
    csvfile.close()

def Write_txt(data):
    textfile = open("uniqueIDs.txt", "w")
    for x in data:
        print(x, file=textfile)

def V1_User(uniqueIDs):
    number = 0
    for i in tqdm (range(len(uniqueIDs)), desc="User Data", unit=" Ids"):
        userId = uniqueIDs[i]
        URL = f"https://users.roblox.com/v1/users/{userId}"
        response = requests.get(URL)
        if response.status_code == 200:
            data = response.json()
            ban_stat = data["isBanned"]
            if ban_stat == False:
                discp_str = str(data["description"])
                if discp_str == "":
                    discp_str = "null"
                discp_str = discp_str.replace("\n"," ")
                csv_data.append([data["id"], data["name"], data["displayName"], discp_str])
                number = number + 1
        elif response.status_code == 429:
            time.sleep(60)
        else:
            print("http error {response.status_code}")
        time.sleep(0.1)
    print(f"There are {number} users to review" )
    Write_CSV(csv_data)

def Friend_Finder():
    userId = int(input("userId: " ));
    friends_URL = f"https://friends.roblox.com/v1/users/{userId}/friends"
    response = requests.get(friends_URL)
    if response.status_code == 200:
        friends_data = response.json()
        for member_data in friends_data['data']:
            all_IDs.append(member_data["id"])
    elif response.status_code == 429:
        print("too many requests")
    else:
        print(f"http error: {response.status_code} for {friends_URL}")

def Group_Finder(groupSize, groupId):
    temp = 0
    temp = f'{(groupSize / 100):.0f}'
    next_page_cursor = ""
    for i in tqdm (range(int(temp)), desc="Geting UserIds", unit=" 100 Ids"):
        URL = f"https://groups.roblox.com/v1/groups/{groupId}/users?sortOrder=Asc&limit=100&Cursor={next_page_cursor}"
        response = requests.get(URL)
        groups_data = response.json()
        for member_data in groups_data['data']:
            all_IDs.append(member_data['user']['userId'])
        next_page_cursor = groups_data['nextPageCursor']

def basic_info(groupId):
    URL = f"https://groups.roblox.com/v1/groups/{groupId}/"
    response = requests.get(URL)
    data = response.json()
    group_memberCount = data["memberCount"]
    print(f"member count = {group_memberCount}")
    return group_memberCount

def main():
    repeat = True
    while repeat is not False:
        command = str(input("(Group_Finder, Friend_Finder, Done, help): " ));
        if command == "Group_Finder":
            groupId = int(input("groupId: " ));
            Group_Finder(basic_info(groupId), groupId)
        elif command == "Friend_Finder":
            Friend_Finder()
        elif command == "Done":
            repeat = False
            uniqueIDs = list(set(all_IDs))
            if Ban_status == "Y":
                V1_User(uniqueIDs)
            else:
                Write_txt(uniqueIDs)
        elif command == "help":
            print("Group_Finder, finds the userIds of all of the users in a group")
            print("Friend_Finder, finds the userIds of the users who are friends with annother user")
            print("Done, ends the collection loop and processes the userIds")
            print("")
        else:
            print("invalid input")

if __name__ == '__main__':
    user_Json = {}
    user_List = []
    all_IDs = []
    csv_data = []
    print("Do you want to run the ban check when processing User IDs? It is slow, 5 IDs / Second")
    Ban_status = input("(Y / n): ")
    main()
