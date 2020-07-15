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

def get_player_from_role(GAME, role, alive_select=True):
    """renvoie une liste de players jouant le rôle passé en argument. Le booleen alive_select permet de choisr si on filtre les morts ou pas"""
    to_return = []
    for player in GAME.players:
        if player.role == role:
            if (alive_select and player.alive) or not(alive_select):
                to_return.append(player)
    return to_return


async def check_permissions_to_use_power(ctx, GAME, role):
    """A appeler au début de chaque commande de pouvoir de nuit. Vérifie si le joueur est bien celui qu'il prétend être, qu'il est vivant, qu'il n'a pas déjà joué et qu'on est bien la nuit."""
    if get_player_from_discord_user(GAME, ctx.message.author).role != role:
        await ctx.send("""Only the {} can use this power""".format(role))
        return False
    if get_player_from_discord_user(GAME, ctx.message.author).alive == False:
        await ctx.send("""You have to be alive to use your power.""")
        return False
    if not(GAME.night):
        await ctx.send("""You can use your power only at night.""")
        return False
    if GAME.turns_played[role]:
        await ctx.send("""You can only use your power once a night""")
        return False
    return True