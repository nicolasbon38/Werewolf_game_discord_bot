import discord

class Player:
    def __init__(self, user, name):
        self.user = user
        self.name = name
        self.role = None
        self.alive = True

    async def kill(self, ctx, GAME):
        self.alive = False
        await discord.utils.get(ctx.guild.channels, name='place-publique', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("{} est mort. Il était {}.".format(self.name, self.role))
        #il ne peut plus parler nulle part, sauf dans le cimetière
        await discord.utils.get(ctx.guild.channels, name='place-publique', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(send_messages=False))
        await discord.utils.get(ctx.guild.channels, name='loups-garous', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(send_messages=False))
        await discord.utils.get(ctx.guild.channels, name='cimetière', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(read_messages=True))
        await discord.utils.get(ctx.guild.channels, name='cimetière', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).set_permissions(self.user, overwrite=discord.PermissionOverwrite(send_messages=True))

