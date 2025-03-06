import requests
import json
import time

def ban_check(uniqueIDs):
    with open("API_KEY.txt", "r") as text_file:
        API_KEY = text_file.read()
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    index = 0
    number = 0
    for x in uniqueIDs:
        userId = uniqueIDs[index]
        URL = f"https://apis.roblox.com/cloud/v2/users/{userId}"
        response = requests.get(URL, headers=headers)
        print("Checking user", uniqueIDs[index])
        if response.status_code == 200:
            with open("UserIDs_to_Review.txt", "a") as f:
                print(uniqueIDs[index], file=f)
                number = number + 1
        index = index + 1
    return number

def process(uniqueIDs):
    index = 0
    for x in uniqueIDs:
        userId = uniqueIDs[index]
        with open("UserIDs_to_Review.txt", "a") as f:
            print(uniqueIDs[index], file=f)
        index = index + 1
    number = len(uniqueIDs)
    return number

def Friend_Finder():
    userId = int(input("userId: " ));
    URL = f"https://friends.roblox.com/v1/users/{userId}/friends/"
    response = requests.get(URL)
    data = response.json()
    for  member_data in data['data']:
        print(f"found {member_data['id']}")
        userList.append(member_data['id'])
    return userList

def Group_Finder():
    groupId = int(input("groupId: " ));
    next_page_cursor = ""
    while next_page_cursor is not None:
        URL = f"https://groups.roblox.com/v1/groups/{groupId}/users?sortOrder=Asc&limit=100&Cursor={next_page_cursor}"
        response = requests.get(URL)
        data = response.json()
        for member_data in data['data']:
                userList.append(member_data['user']['userId'])
                print(f"found {member_data['user']['userId']}")
        next_page_cursor = data['nextPageCursor']
    return userList

def main():
    repeat_users = True
    while repeat_users is not False:
        command = str(input("(Group_Finder, Friend_Finder, Done, help): " ));
        if command == "Group_Finder":
            Group_Finder()
        elif command == "Friend_Finder":
            Friend_Finder()
        elif command == "Done":
            repeat_users = False
            ban = str(input("Run ban check? API key required (Y/n): " ));
            uniqueIDs = list(set(userList))
            if ban == "Y":
                num = ban_check(uniqueIDs)
            if ban == "n":
                num = process(uniqueIDs)
            print(f"There are {num} users to review" )
        elif command == "help":
            print("Group_Finder, finds the userIds of the users in a group")
            print("Friend_Finder, finds the userIds of the users who are friends with annother user")
            print("Done, ends the collection loop and processes the userIds")
            print("")
        else:
            print("invalid input")

if __name__ == '__main__':
    userList = []
    assetList = []
    main()