import discord

def roles_enumeration(game):
    """renvoie une chaine de caractère avec les rôles de la game"""
    s = ""
    for role in game.roles[:-1]:
        s += role + ", "
    s += game.roles[-1]
    return s


def players_that_are_alive(GAME):
    """renvoie une liste des joueurs encore vivants"""
    return([x for x in GAME.players if x.alive])


def players_that_are_wolves(GAME):
    """renvoie la liste des joueus vivants LGs"""
    return([x for x in GAME.players if x.alive and x.role == 'WEREWOLF'])


def players_that_are_not_wolves(GAME):
    """renvoie la liste des joueus vivants LGs"""
    return([x for x in GAME.players if x.alive and x.role != 'WEREWOLF'])

def name_of_the_members(ctx):
    """renvoie une liste des noms des membres du serveur"""
    return [x.name for x in ctx.guild.members]

def get_player_from_discord_user(GAME, discord_user):
    for player in GAME.players:
        if player.name == discord_user.name:
            return player
    return None

async def send_dm(ctx, member, content):
    channel = await member.create_dm()
    await channel.send(content)