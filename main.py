from telethon import TelegramClient
from telethon import functions
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
    await client(
        functions.channels.EditAdminRequest(
            channel=group, user_id=user.id, admin_rights=rights, rank=rank
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
