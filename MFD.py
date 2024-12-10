import requests
import json
import time

userList = []
assetList = []
repeat_users = True
repeat_assets = True
repeat = True
index = 0
number = 0
text_file = open("API_KEY.txt", "r")
API_KEY = text_file.read()
text_file.close()
headers = {"Content-Type": "application/json", "x-api-key": API_KEY}

print("welcome to the moderation for dummies toolkit. What do you want to do? ")
while repeat is not False:
    Ans = str(input("(users or assets): " ));
    if Ans == "users":
        repeat_assets = False
        repeat = False
    elif Ans == "assets":
        repeat_users = False
        repeat = False
    else:
        print("invalid input")

while repeat_users is not False:
    command = str(input("(Group_Finder, Friend_Finder, Done, help): " ));
    if command == "Group_Finder":
        groupId = int(input("groupId: " ));
        next_page_cursor = ""
        while next_page_cursor is not None:
            URL = f"https://groups.roblox.com/v1/groups/{groupId}/users?sortOrder=Asc&limit=100&Cursor={next_page_cursor}"
            response = requests.get(URL)
            data = response.json()
            for member_data in data['data']:
                print(member_data['user']['userId'])
                userList.append(member_data['user']['userId'])
            next_page_cursor = data['nextPageCursor']
    elif command == "Friend_Finder":
        userId = int(input("userId: " ));
        URL = f"https://friends.roblox.com/v1/users/{userId}/friends/"
        response = requests.get(URL)
        data = response.json()
        for  member_data in data['data']:
            print(member_data['id'])
            userList.append(member_data['id'])
    elif command == "Done":
        #Gets rid of duplicate UserIds.
        uniqueIDs = list(set(userList))
        #Checks to see if user is Banned. API v1 data can be out of date.
        print("Checking to see if users are already banned.")
        time.sleep(1)
        for x in uniqueIDs:
            userId = uniqueIDs[index]
            URL = f"https://apis.roblox.com/cloud/v2/users/{userId}"
            response = requests.get(URL, headers=headers)
            print("Checking user", uniqueIDs[index])
            if response.status_code == 200:
                with open("UserIDs_to_Review.txt", "a") as f:
                    print(uniqueIDs[index], file=f)
                    number = number + 1
                f.close()
            index = index + 1
        print("There are", number, "users to review" )
    elif command == "help":
        print("Group_Finder, finds the userIds of the users in a group")
        print("Friend_Finder, finds the userIds of the users who are friends with annother user")
        print("Done, ends the collection loop and processes the userIds")
        print("")
    else:
        print("invalid input")

while repeat_assets is not False:
    command = str(input("(Group_Store, Clothes_Finder, Done, help): " ));
    if command == "Group_Store":
        groupId = int(input("groupId: " ));
        nextPageCursor = ""
        while nextPageCursor is not None:
            URL = f"https://catalog.roblox.com/v1/search/items/details?Category=3&CreatorType=2&CreatorTargetId={groupId}&Limit=30&Cursor={nextPageCursor}"
            response = requests.get(URL)
            data = response.json()
            for member_data in data['data']:
                assetList.append(member_data['id'])
                print(member_data['id'])
            nextPageCursor = data['nextPageCursor']
    elif command == "Clothes_Finder":
        userId = int(input("userId: " ));
        AssetTypes = "CLASSIC_TSHIRT,MODEL,CLASSIC_SHIRT,CLASSIC_PANTS,FACE,DECAL" #Can change this. I just think that most bypassed items are one of these.
        URL = f"https://apis.roblox.com/cloud/v2/users/{userId}/inventory-items?maxPageSize=100&filter=inventoryItemAssetTypes={AssetTypes}"
        response = requests.get(URL, headers=headers)
        if response.status_code == 200:
            data = json.loads(response.text)
            inventory = data['inventoryItems']
            for member_data in inventory:
                print(member_data['assetDetails']['assetId'])
                assetList.append(member_data['assetDetails']['assetId'])
        elif response.status_code == 403:
            print("can-view-inventory = false")
        else:
            print("IDK", response)
    elif command == "Done":
        #Gets rid of duplicate asset Ids.
        uniqueIDs = list(set(assetList))
        for x in uniqueIDs:
            with open("AssetsIDs_to_Review.txt", "a") as f:
                print(uniqueIDs[index], file=f)
            f.close()
            index = index + 1
        print("There are", len(uniqueIDs), "assets to review" )
    elif command == "help":
        print("Group_Finder, finds the userIds of the users in a group")
        print("Friend_Finder, finds the userIds of the users who are friends with annother user")
        print("Done, ends the collection loop and processes the asset Ids")
        print("")
    else:
        print("invalid input")