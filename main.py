from telethon import TelegramClient
from telethon import functions, errors
from telethon.tl.types import *
from dotenv import load_dotenv
import asyncio
import readline  # for input history

load_dotenv()

# You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")


client = TelegramClient("session_name", api_id, api_hash)

default_admin = ChatAdminRights(
    change_info=True,
    post_messages=True,
    edit_messages=True,
    delete_messages=True,
    ban_users=True,
    invite_users=True,
    pin_messages=True,
    manage_call=True,
    other=True,
    manage_topics=True,
    post_stories=True,
    edit_stories=True,
    delete_stories=True,
)


async def getGroups():
    """
    Get a list of groups where the user is an admin or creator.

    Returns:
        list: A list of groups where the user is an admin or creator.
    """
    dialogs = await client.get_dialogs()
    return [
        d
        for d in dialogs
        if d.is_group
        and not (hasattr(d.entity, "migrated_to") and d.entity.migrated_to)
        and (d.entity.creator or d.entity.admin_rights)
    ]


async def getUserByUsername(group, username):
    """
    Get the user ID of a Telegram user in a group by their username.

    Args:
        group (int): The ID of the Telegram group.
        username (str): The username of the user to search for.

    Returns:
        int: The ID of the user.

    Raises:
        ValueError: If the user is not found or an invalid index is entered.
    """
    possible = await client.get_participants(group, limit=10, search=username)
    if not possible:
        raise ValueError("User not found")

    # Try to find exact match
    for i in range(len(possible)):
        if possible[i].username == username:
            return possible[i].id

    # Fuzzy match
    for i in range(len(possible)):
        user = possible[i]
        print(f"{i} {user.username} - {user.first_name} {user.last_name}")
    index = int(input("Enter the index of the user: "))
    if index < 0 or index >= len(possible):
        raise ValueError("Invalid index")
    return possible[index].id


async def listTitles(admins):
    """
    Print the titles and ranks of the given admins.

    Args:
        admins (list): A list of admins.

    Returns:
        None
    """
    print("Admins:")
    for i in range(len(admins)):
        user = admins[i]
        rank = user.participant.rank or "(Admin)"
        print(f"{i : <4}{user.first_name} {user.last_name}\t{rank}")


async def getAdmins(group):
    """
    Get the list of admins for the given group.

    Args:
        group (int): The ID of the group.

    Returns:
        list: A list of admins for the given group.
    """
    return await client.get_participants(group, filter=ChannelParticipantsAdmins)


async def removeAdmin(admins, userIndex, group):
    """
    Remove an admin from a group.

    Args:
        admins (list): List of admin users.
        userIndex (int): Index of the user to remove.
        group (str): Group name or ID.

    Returns:
        None
    """
    user = admins[userIndex]
    await client.edit_admin(group, user.id, is_admin=False)
    print(f"Removed admin role from {user.first_name} {user.last_name}")


async def changeRank(admins, userIndex, group):
    """
    Change the rank of an admin in the given group.

    Args:
        admins (list): A list of admins.
        userIndex (int): The index of the admin to change the rank for.
        group (int): The ID of the group.

    Returns:
        None
    """
    user = admins[userIndex]
    rights = user.participant.admin_rights
    rank = input(f"Enter new rank for {user.first_name} {user.last_name}: ")
    # await client.edit_admin(group, user.id, title=rank)
    try:
        await client(
            functions.channels.EditAdminRequest(
                channel=group, user_id=user.id, admin_rights=rights, rank=rank
            )
        )
    except errors.rpcerrorlist.AdminRankInvalidError as err:
        print(err)


async def addAdmin(group):
    """
    Adds an admin to the specified group.

    Parameters:
    - group: The group/channel to add the admin to.

    Returns:
    - None
    """
    username = input("Enter the username of the user to add: ")
    user_id = await getUserByUsername(group, username)
    rank = input(f"Enter the rank for {username}: ")
    await client(
        functions.channels.EditAdminRequest(
            channel=group, user_id=user_id, admin_rights=default_admin, rank=rank
        )
    )


async def selectGroup():
    """
    Displays a list of groups and prompts the user to select a group by entering the index.

    Returns:
        int: The ID of the selected group.
    """
    groups = await getGroups()
    for i in range(len(groups)):
        print(f"{i}: {groups[i].name}")
    index = int(input("Enter the index of the group: "))
    print()
    return groups[index].id


async def loop(group):
    group_entity = await client.get_entity(group)
    print(f"Current group: {group_entity.title}")
    admins = await getAdmins(group)
    await listTitles(admins)
    print(
        """Commands:
edit <index> - Edit the title of an admin
remove <index> - Remove an admin
add - Add an admin
print - Print the list of admins
exit - Exit the program"""
    )
    while True:
        print()
        command = input("Enter command: ").split()
        if command[0] == "edit" and len(command) == 2:
            index = int(command[1])
            await changeRank(admins, index, group)
        elif command[0] == "remove" and len(command) == 2:
            index = int(command[1])
            await removeAdmin(admins, index, group)
        elif command[0] == "add":
            await addAdmin(group)
        elif command[0] == "print":
            admins = await getAdmins(group)
            await listTitles(admins)
        elif command[0] == "exit":
            break
        else:
            print("Invalid command")


async def main():
    """
    The main function that runs the program.

    Returns:
        None
    """
    await client.start()
    group = await selectGroup()
    await loop(group)


asyncio.run(main())
