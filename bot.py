# bot.py
import os
from dotenv import load_dotenv
from random import choice
from datetime import datetime, timedelta

from discord.ext import commands, tasks
import discord.utils


from game import Game
from player import Player
from utils import roles_enumeration, name_of_the_members, players_that_are_alive, players_that_are_wolves, players_that_are_not_wolves, get_player_from_discord_user, send_dm
from scrutin import Scrutin, ScrutinWolf


SUPPORTED_ROLES = ['VILLAGER', 'WEREWOLF']


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')


"""Event permettant de vérifier si le bot se lance"""
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')



"""Gestion des commandes inconnues avec un petit message convivial et explicite"""
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('Unknown Command : ' + ctx.message.content)
    raise error

# """Gestion des commandes non permies avec un message convivial"""
# @bot.event
# async def permission_command_error(ctx, error):
#     if isinstance(error, commands.errors.)


"""Commande permettant de créer une instance de GAME globale, et de setup les salons, etc"""
@bot.command(name='newgame')
async def create_game(ctx, *args):
    #arg is the name of the channel specified by the user
    if not(args):
        await ctx.send('Création de partie impossible : Vous devez spécifier le nom de votre partie')
    game_name = ' '.join(args)
    global GAME
    GAME = Game(game_name)
    guild = ctx.guild
    print('Creating channels for the new game')
    category = await guild.create_category(game_name)
    channel_admin = await guild.create_text_channel('Admin', category=category)
    await channel_admin.send("""Welcome on the Admin Channel. Type `!help` to have a list of commands""")
    channel_join = await guild.create_text_channel('join', category=category)
    await channel_join.send("""Welcome on the Join Channel. Type `!join` to join the game, `!quit` to quit the game.""")
    channel_setup_role = await guild.create_text_channel('setup roles', category=category)
    await channel_setup_role.send("""Ecrire un texte""")
    print('Creating the admin role')
    role_admin = await guild.create_role(name='Admin ' + game_name)
    await ctx.message.author.add_roles(role_admin)
    print('Creating the player role')
    role_player = await guild.create_role(name='Player ' + game_name)
    await ctx.message.author.add_roles(role_player)


"""Commande permettant à un utilisateur de rejoindre la partie dans le channel join"""
@bot.command(name='join')
async def join(ctx):
    if ctx.channel.name == 'join':
        if ctx.message.author.name in [player.name for player in GAME.players]:
            await ctx.send(f'{ctx.message.author.mention} You have already joined this game.')
        else:
            GAME.players.append(Player(ctx.message.author, ctx.message.author.name))
            await ctx.message.author.add_roles(discord.utils.get(ctx.guild.roles, name='Player ' + GAME.name))
            await ctx.send('You have successfully joined the game. There are currently {} players in this game'.format(len(GAME.players)))
    else:
        await ctx.send('To join the game, you have to type this command in the channel *Join*')



"""COmmande permettant à un joueur de quitter une partie dans laquelle il est inscrit (avant qu'elle soit lancée bien sûr)"""
@bot.command(name='quit')
async def quit(ctx):
    if ctx.channel.name == 'join':
        if not(ctx.message.author.name in [player.name for player in GAME.players]):
            await ctx.send(f'{ctx.message.author.mention} You are not in this game.')
        else:
            for player in GAME.players:
                if player.name == ctx.message.author.name:
                    GAME.players.remove(player)
            await ctx.message.author.remove_roles(discord.utils.get(ctx.guild.roles, name='Player ' + GAME.name))
            await ctx.send('You have successfully quitted the game. There are currently {} players in this game'.format(len(GAME.players)))
    else:
        await ctx.send('To quit the game, you have to type this command in the channel *Join*')



"""Commande permettant d'ajouer des roles à la partie"""
@bot.command(name='addrole')
async def addrole(ctx, *args):
    if not(args):
        await ctx.send("""Vous n'avez spécifié aucun rôle à ajouter""")
    if ctx.channel.name == 'setup-roles':
        for role in args:
            if role in SUPPORTED_ROLES:
                GAME.roles.append(role)
                await ctx.send('{} ajouté à la partie'.format(role))
                await ctx.send('Il y a actuellement {} roles dans la partie :  '.format(len(GAME.roles)) + roles_enumeration(GAME) + '.')
            else:
                await ctx.send('Unknown Role :' + str(role))
    else:
        await ctx.send('To add a role to this game, you have to type this command in the channel *setup-roles*')


"""Commande permettant de retirer un rôle de la partie"""
@bot.command(name='removerole')
async def removerole(ctx, *args):
    if not(args):
        await ctx.send("""Vous n'avez spécifié aucun rôle à supprimer""")
    if ctx.channel.name == 'setup-roles':
        for role in args:
            if role in SUPPORTED_ROLES:
                GAME.roles.remove(role)
                await ctx.send('{} retiré de la partie'.format(role))
                await ctx.send('Il y a actuellement {} roles dans la partie :  '.format(len(GAME.roles)) + roles_enumeration(GAME) + '.')
            else:
                await ctx.send('Unknown Role :' + str(role))
    else:
        await ctx.send('To remove a role from this game, you have to type this command in the channel *setup-roles*')




"""Commande permettant de lancer la game (admin uniquement). Le bot vérifie qu'il y a le même nombre de joueurs que de rôles, attribue un rôle à chaque joueur, supprimme les channels inutiles"""
@bot.command(name='start')
async def start(ctx):
    if not("Admin " + GAME.name in [x.name for x in ctx.author.roles]):
        await ctx.send("You must be an admin to start the game.")
        return
    if len(GAME.players) != len(GAME.roles):
        await ctx.send("There are currently {} players, but {} roles. Impossible to start the game.".format(len(GAME.players), len(GAME.roles)))
        return
    #on attribue les rôles
    copy_roles = [x for x in GAME.roles]
    for player in GAME.players:
        player.role = choice(copy_roles)
        copy_roles.remove(player.role)
        print(player.name, player.role)
        #On envoie les rôles en DM aux joueurs
        await send_dm(ctx, player.user, "You are {} !".format(player.role))

    #On crée tous les salons
    guild = ctx.guild
    category = discord.utils.get(guild.categories,id=ctx.message.channel.category_id)
    channel_place_publique = await guild.create_text_channel('Place publique', category=category)
    channel_lg = await guild.create_text_channel('loups-garous', category=category)
    channel_morts = await guild.create_text_channel('cimetière', category=category)
    #On supprime ceux qui ne servent plus à rien
    await discord.utils.get(guild.channels, name='join', category=discord.utils.get(guild.categories, name=GAME.name)).delete(reason="Game has begun. Channel no longer necessary")
    await discord.utils.get(guild.channels, name='setup-roles', category=discord.utils.get(guild.categories, name=GAME.name)).delete(reason="Game has begun. Channel no longer necessary")
    #on rend invisible le salon loup-garous sauf par les loups-garous evidemment, et le salon cimetière invisible par tout le monde
    for player in GAME.players:
        if player.role != 'WEREWOLF':
            await channel_lg.set_permissions(player.user, overwrite=discord.PermissionOverwrite(read_messages=False))
        await channel_morts.set_permissions(player.user, overwrite=discord.PermissionOverwrite(read_messages=False))
    await channel_lg.send("Welcome on the Werewolfs' channel")
    GAME.started = True
    await channel_place_publique.send("""THE GAME BEGINS""")
    GAME.night = True
    await discord.utils.get(ctx.guild.channels, name='place-publique', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""It's the Night""")
    await GAME.launch_night()



"""Commande permettant de voter pour éliminer un joueur. Un second appel à cette commande permet de modifier son vote. La commande ne fonctionne que sur la place publqiue Le premier appel à cette commande permet de créer un nouveau scrutin"""
@bot.command(name='vote')
async def vote(ctx, arg):
    if not(arg):
        await ctx.send("""Vous n'avez spécifié aucun nom de joueur""")
    if ctx.channel.name == 'place-publique':
        if GAME.night:
            await ctx.send("""You cannot vote at night""")
            return
        #on vérifie si il vote pour une personne qui est vivant
        if not(arg in [x.name for x in players_that_are_alive(GAME)]):
            await ctx.send("You must for an alive person. Check your spelling")
            return
        #On crèe le scrutin si il n'existe tjrs pas
        if not(GAME.scrutin):
            GAME.scrutin = Scrutin(GAME)
        #Si il n'a jamais voté
        if not(GAME.scrutin.votes[ctx.message.author]):
            GAME.scrutin.votes[ctx.message.author] = discord.utils.get(ctx.guild.members, name=arg)
            GAME.scrutin.suffrages[discord.utils.get(ctx.guild.members, name=arg)] += 1
            await ctx.send("Vote pris en compte")
        else:
            GAME.scrutin.suffrages[GAME.scrutin.votes[ctx.message.author]] -= 1
            GAME.scrutin.votes[ctx.message.author] = discord.utils.get(ctx.guild.members, name=arg)
            GAME.scrutin.suffrages[discord.utils.get(ctx.guild.members, name=arg)] += 1
            await ctx.send("Vote pris en compte")
        # print(GAME.scrutin.votes)
        # print(GAME.scrutin.suffrages)
    else:
        await ctx.send("""You can only vote in the Place-publique channel""")


"""Commande permettant aux loups de voter pour manger un joueur. Même fonctionnement que le vote normal en gros, mais on change de classScrutin"""
@bot.command(name='votewolf')
async def votewolf(ctx, arg):
    if not(arg):
        await ctx.send("""Vous n'avez spécifié aucun nom de joueur""")
    if ctx.channel.name == 'loups-garous':
        if not(GAME.night):
            await ctx.send("""Wolves cannot vote to slay a player during the day.""")
            return
        #on vérifie si c'est l'admin qui trolle
        if ctx.message.author.guild_permissions.administrator and get_player_from_discord_user(GAME, ctx.message.author) not in players_that_are_wolves(GAME):
            await ctx.send("""Sir Administrator, please don't try to cheat. I'm the fucking God of this game. Thank you.""")
            return
        #on vérifie si il vote pour une personne qui est vivante
        if not(arg in [x.name for x in players_that_are_alive(GAME)]):
            await ctx.send("You must vote for an alive person. Check your spelling")
            return
        #On vérifie si il vote pour une personne qui n'est pas un loup
        if not(arg in [x.name for x in players_that_are_not_wolves(GAME)]):
            await ctx.send("You cannot vote for an other wolf")
            return
        #On crèe le scrutin si il n'existe tjrs pas
        if not(GAME.scrutinwolf):
            GAME.scrutinwolf = ScrutinWolf(GAME)
        #Si il n'a jamais voté
        if not(GAME.scrutinwolf.votes[ctx.message.author]):
            GAME.scrutinwolf.votes[ctx.message.author] = discord.utils.get(ctx.guild.members, name=arg)
            GAME.scrutinwolf.suffrages[discord.utils.get(ctx.guild.members, name=arg)] += 1
            await ctx.send("Vote pris en compte")
        else:
            GAME.scrutinwolf.suffrages[GAME.scrutin.votes[ctx.message.author]] -= 1
            GAME.scrutinwolf.votes[ctx.message.author] = discord.utils.get(ctx.guild.members, name=arg)
            GAME.scrutinwolf.suffrages[discord.utils.get(ctx.guild.members, name=arg)] += 1
            await ctx.send("Vote pris en compte")
        print(GAME.scrutinwolf.suffrages)
    else:
        print("Ce mec est con")



"""Commande permettant aux loup-garous de mettre fin aux votes et e dévorer la victime majoritaire. Ne gère pas l'égalité pour l'instant"""
@bot.command(name='slay')
async def slay(ctx):
    if ctx.channel.name=='loups-garous':
        if not(GAME.night):
            await ctx.send("Wolves cannot slay a villager during the day.")
            return
        #On récupère la victime, et on la stocke:
        victim = get_player_from_discord_user(GAME, GAME.scrutinwolf.get_majority())
        GAME.deaths_this_night.append(victim)
        GAME.turns_played['WEREWOLF'] = True
        if GAME.check_end_night():
            await launch_day(ctx)
    else:
        print("Ce mec est con")


"""Fonctions qui résout la nuit, lance la procédure de vote, avec le timer en arrière-plan"""
async def launch_day(ctx):
    await discord.utils.get(ctx.guild.channels, name="place-publique", category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""Le jour se lève.""")
    GAME.night = False
    for victim in GAME.deaths_this_night:
        await victim.kill(ctx, GAME)
    if not(await check_win(ctx)):
        final_time = datetime.now() + timedelta(seconds=30)
        await discord.utils.get(ctx.guild.channels, name="place-publique", category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""Les votes sont ouverts""")
        check_time.start(ctx=ctx, final_time=final_time)
    else:
        return


"""Tasks gérant le timer des votes"""
@tasks.loop(seconds=10, count=None)
async def check_time(ctx, final_time):
    if datetime.now() > final_time:
        await discord.utils.get(ctx.guild.channels, name="place-publique", category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""Temps écoulé ! Les votes sont clos""")
        mort = get_player_from_discord_user(GAME, GAME.scrutin.get_majority())
        await mort.kill(ctx, GAME)
        print(GAME.scrutin.votes, GAME.scrutin.suffrages)
        GAME.scrutin = None
        GAME.night = True
        await discord.utils.get(ctx.guild.channels, name='place-publique', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""It's the Night""")
        if await check_win(ctx):
            check_time.cancel()
            return
        check_time.stop()
    elif datetime.now() > final_time - timedelta(seconds=11):
        await discord.utils.get(ctx.guild.channels, name="place-publique", category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""Il reste dix secondes.""")
       
        

"""afetr_loop relatif à la task précédente qui sert à lance la nuit quand la loop du jour se termine"""
@check_time.after_loop
async def after_check_time():
    print("j'ai pris le relais !")
    if not(check_time.is_being_cancelled()): #si il est cancel, c'est que la partie est finie
        await GAME.launch_night()


"""FOnction qui promet d'être super compliquée et qui, appelée le matin et le soir, vérifie si la partie est finie"""
async def check_win(ctx):
    if len(players_that_are_wolves(GAME)) == 0:
        await discord.utils.get(ctx.guild.channels, name='place-publique', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""Tous les loups-Garous sont morts ! Les Villageois ont gagnés !""")
        return True
    if len(players_that_are_wolves(GAME)) > len(players_that_are_not_wolves(GAME)) and len(players_that_are_alive(GAME)) != 0:
        await discord.utils.get(ctx.guild.channels, name='place-publique', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""Les loups-garous sont en surnombre ! Les Villageois ont gagnés !""")
        return True
    if len(players_that_are_alive(GAME)) == 0:
        await discord.utils.get(ctx.guild.channels, name='place-publique', category=discord.utils.get(ctx.guild.categories, name=GAME.name)).send("""TOUT LE MONDE EST MORT !""")
        return True
    return False
   

bot.run(TOKEN)
