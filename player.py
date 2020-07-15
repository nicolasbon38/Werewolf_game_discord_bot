import discord

from utils import send_dm

class Player:
    def __init__(self, user, name):
        self.user = user
        self.name = name
        self.role = None
        self.alive = True
        self.state_witch = None
        self.state_hunter = None # True si son pouvoir a été utilisé, False sinon, None s'il n'est pas hunter

    async def kill(self, GAME):
        self.alive = False
        await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("{} est mort. Il était {}.".format(self.name, self.role))
        #il ne peut plus parler nulle part, sauf dans le cimetière
        await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(send_messages=False))
        await discord.utils.get(GAME.guild.channels, name='loups-garous', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(send_messages=False))
        await discord.utils.get(GAME.guild.channels, name='cimetière', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(read_messages=True))
        await discord.utils.get(GAME.guild.channels, name='cimetière', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(send_messages=True))
        if self.role == 'HUNTER':
            await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""The Hunter have to send me in private the name of the person he wants to kill""")
            await send_dm(self.user, """You died. You have to shoot a player with `!shoot <name>.""")
            GAME.game_blocked = True
            self.alive = True #pour qu'il puisse lancer sa commande, il mourra à ce moment là
