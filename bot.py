# bot.py
import os
from dotenv import load_dotenv
from random import choice
from datetime import datetime, timedelta

from discord.ext import commands, tasks
import discord.utils


from game import Game
from player import Player
from utils import roles_enumeration, name_of_the_members, players_that_are_alive, players_that_are_wolves, players_that_are_not_wolves, get_player_from_discord_user, send_dm, get_player_from_role, check_permissions_to_use_power
from scrutin import Scrutin, ScrutinWolf
from state_witch import State_witch


SUPPORTED_ROLES = ['VILLAGER', 'WEREWOLF', 'SEER', 'WITCH', 'HUNTER']


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

# """Test pour passer une commande en DM"""
# @bot.command(name='test')
# async def test(ctx):
#     await ctx.message.author.send("""J'ai compris que tu me parles""")
#     await ctx.send(ctx.message.channel.name)


"""Commande permettant de créer une instance de GAME globale, et de setup les salons, etc"""
@bot.command(name='newgame')
async def create_game(ctx, *args):
    #arg is the name of the channel specified by the user
    if not(args):
        await ctx.send('Création de partie impossible : Vous devez spécifier le nom de votre partie')
    game_name = ' '.join(args)
    global GAME
    GAME = Game(ctx, game_name)
    guild = ctx.guild
    print('Creating channels for the new game')
    category = await guild.create_category(game_name)
    channel_admin = await guild.create_text_channel('Admin', category=category)
    await channel_admin.send("""Welcome on the Admin Channel. Type `!help` to have a list of commands""")
    channel_join = await guild.create_text_channel('join', category=category)
    await channel_join.send("""Welcome on the Join Channel. Type `!join` to join the game, `!quit` to quit the game.""")
    channel_setup_role = await guild.create_text_channel('setup roles', category=category)
    await channel_setup_role.send("""Ecrire un texte""")
    channel_settings = await guild.create_text_channel('settings', category=category)
    await channel_settings.send("""Ecrire in texte ici""")
    print('Creating the admin role')
    role_admin = await guild.create_role(name='Admin ' + game_name)
    await ctx.message.author.add_roles(role_admin)
    print('Creating the player role')
    role_player = await guild.create_role(name='Player ' + game_name)
    await ctx.message.author.add_roles(role_player)


"""Commande permettant de supprimer les salons d'une game"""
@bot.command(name='deletegame')
async def deletegame(ctx, arg):
    category = discord.utils.get(ctx.guild.categories, name=arg)
    if category:
        for channel in category.channels:
            await channel.delete()
        await category.delete()
    else:
        await ctx.send("""Unknown game : {}. Maybe it is already finished ?""".format(arg))


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
        return
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


"""Commande permettant de set up la durée du timer de vote du village"""
@bot.command(name='setuptimer')
async def setuptimer(ctx, arg):
    if not(arg):
        await ctx.send("""Vus n'avez pas spécifié de duréee""")
        return
    if ctx.channel.name == 'settings':
        GAME.settings.timer_duration = int(arg)
        await ctx.send("""The duration of the voting timer is now of {} seconds.""".format(arg))
    else:
        await ctx.send('The settings have to be modified in the settings channel')



"""Commande permettant de lancer la game (admin uniquement). Le bot vérifie qu'il y a le même nombre de joueurs que de rôles, attribue un rôle à chaque joueur, supprime les channels inutiles"""
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
        await send_dm(player.user, "You are {} !".format(player.role))
        #On met le marqueur de potion à la sorcière, et le marquerur du chasseur
        if player.role == 'WITCH':
            player.state_witch = State_witch()
        elif player.role == 'HUNTER':
            player.state_hunter = False
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
        #On envoie l'info à la sorcière, si elle est vivante :
        if 'WITCH' in GAME.roles:
            try:
                witch = get_player_from_role(GAME, 'WITCH', True)[0]
            except:
                witch = None
            if witch:
                await send_dm(witch.user, """{} has been slayed by the werewolves tonight.""".format(victim.name))
        await ctx.channel.send("You have chosen to slay {} this night.".format(victim.name))
        GAME.deaths_this_night.append(victim)
        GAME.turns_played['WEREWOLF'] = True
        if GAME.check_end_night():
            print("bloqué ? :", GAME.game_blocked)
            await launch_day()
    else:
        print("Ce mec est con")


"""Fonction qui résout la nuit, lance la procédure de vote, avec le timer en arrière-plan"""
async def launch_day():
    await discord.utils.get(GAME.guild.channels, name="place-publique", category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""Le jour se lève.""") # ici on utilise GAME.guild et non pas ctx.guild car le ctx est celui du DMChannel dans les cas où le dernier à jouer n'est pas loup-garou
    if len(GAME.deaths_this_night) == 0:
        await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""Nobody died this night.""")
    for victim in GAME.deaths_this_night:
        await victim.kill(GAME)
    GAME.deaths_this_night = []
    if GAME.game_blocked:
        return
    GAME.night = False
    if not(await check_win()):
        final_time = datetime.now() + timedelta(seconds=GAME.settings.timer_duration)
        await discord.utils.get(GAME.guild.channels, name="place-publique", category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""Les votes sont ouverts""")
        check_time.start(final_time=final_time)
    else:
        return


"""Tasks gérant le timer des votes"""
@tasks.loop(seconds=10, count=None)
async def check_time(final_time):
    if datetime.now() > final_time:
        await discord.utils.get(GAME.guild.channels, name="place-publique", category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""Temps écoulé ! Les votes sont clos""")
        mort = get_player_from_discord_user(GAME, GAME.scrutin.get_majority())
        await mort.kill(GAME)
        print(GAME.scrutin.votes, GAME.scrutin.suffrages)
        GAME.scrutin = None
        await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""It's the Night""")
        if await check_win():
            check_time.cancel()
            return
        check_time.stop()
    elif datetime.now() > final_time - timedelta(seconds=11):
        await discord.utils.get(GAME.guild.channels, name="place-publique", category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""Il reste dix secondes.""")
       
        

"""afetr_loop relatif à la task précédente qui sert à lance la nuit quand la loop du jour se termine"""
@check_time.after_loop
async def after_check_time():
    print("j'ai pris le relais !")
    if not(check_time.is_being_cancelled()): #si il est cancel, c'est que la partie est finie
        GAME.night = True
        await GAME.launch_night()


"""FOnction qui promet d'être super compliquée et qui, appelée le matin et le soir, vérifie si la partie est finie"""
async def check_win():
    if len(players_that_are_alive(GAME)) == 0:
        await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""TOUT LE MONDE EST MORT !""")
        return True
    if len(players_that_are_wolves(GAME)) == 0:
        await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""Tous les loups-Garous sont morts ! Les Villageois ont gagnés !""")
        return True
    if len(players_that_are_wolves(GAME)) > len(players_that_are_not_wolves(GAME)) and len(players_that_are_alive(GAME)) != 0:
        await discord.utils.get(GAME.guild.channels, name='place-publique', category=discord.utils.get(GAME.guild.categories, name=GAME.name)).send("""Les loups-garous sont en surnombre ! Les Villageois ont gagnés !""")
        return True
    return False


###########################################COMMANDES DE RÔLES##############################################

#########VOYANTE###########
@bot.command(name='seer')
async def seer(ctx, arg):
    if not(arg):
        await ctx.send("""Please specify a player to watch""")
        return
    if await check_permissions_to_use_power(ctx, GAME, 'SEER'):
        user = discord.utils.get(GAME.guild.members, name=arg)
        if user is None:
            await ctx.send("""You must target a valid player. Please check your spelling.""")
            return
        await ctx.send("""In your crystal ball, you see that {} is {} !""".format(arg, get_player_from_discord_user(GAME, user).role))
        GAME.turns_played['SEER'] = True
        if GAME.check_end_night():
            await launch_day()

#########################SORCIERE##############################


"""Commande permettant à la sorcière de ressuciter la victime des loup-garous. Pour le moment elle peut en théorie sauver n'importe qui, mais chut"""
@bot.command(name='save')
async def save(ctx, arg):
    if await check_permissions_to_use_power(ctx, GAME, 'WITCH'):
        user_to_save = discord.utils.get(GAME.guild.members, name=arg)
        if user_to_save is None:
            await ctx.send("""You must target a valid player. Please check your spelling.""")
            return
        if get_player_from_discord_user(GAME, ctx.message.author).state_witch.life_potion == False:
            await ctx.send("""You have already use your life potion.""")
            return
        #on enlève le miraculé de la liste des morts
        GAME.deaths_this_night.remove(get_player_from_discord_user(GAME, user_to_save))
        await ctx.send("""You have saved {} from the werewolves. You cannot use this power anymore.""".format(arg))
        #on note que la potion a été utilisée
        get_player_from_discord_user(GAME, ctx.message.author).state_witch.life_potion = False
        #on note la fin de tour
        GAME.turns_played['WITCH'] = True
        if GAME.check_end_night():
            await launch_day()


"""Commande permettant à la sorcière de tuer quelqu'un"""
@bot.command(name='kill')    
async def kill(ctx, arg):
    if await check_permissions_to_use_power(ctx, GAME, 'WITCH'):
        user_to_kill = discord.utils.get(GAME.guild.members, name=arg)
        if user_to_kill is None:
            await ctx.send("You must target a valid player. Please check your spelling.")
            return
        if get_player_from_discord_user(GAME, ctx.message.author).state_witch.death_potion == False:
            await ctx.send("""You have already use your life potion.""")
            return
        #On doit vérifier si il est vivant
        if not(get_player_from_discord_user(GAME, user_to_kill) in players_that_are_alive(GAME)):
            await ctx.send("""You can't kill a dead person""")
            return
        GAME.deaths_this_night.append(get_player_from_discord_user(GAME, user_to_kill))
        await ctx.send("""You have chosen to kill {} with your death potion""".format(user_to_kill.name))
        #on note que la potion a été utilisée
        get_player_from_discord_user(GAME, ctx.message.author).state_witch.death_potion = False
        #on note la fin de tour
        GAME.turns_played['WITCH'] = True
        if GAME.check_end_night():
            await launch_day()



"""Commande permettant à la sorcière de passer son tour"""
@bot.command(name='do-nothing')
async def do_nothing(ctx):
    if await check_permissions_to_use_power(ctx, GAME, 'WITCH'):
        GAME.turns_played['WITCH']= True
        await ctx.send("""You have chosen to do nothing this night.""")
        if GAME.check_end_night():
            await launch_day()


###########CHASSEUR#############


"""Commande permettant au chasseur de tuer un autre joueur à sa mort"""
@bot.command(name='shoot')
async def shoot(ctx, arg):
    if get_player_from_discord_user(GAME, ctx.message.author).role != 'HUNTER':
        await ctx.send("""Only the HUNTER can use this power""")
        return
    if get_player_from_discord_user(GAME, ctx.message.author).state_hunter == False:    #SI LE POUVOIR N'A PAS DÉJÀ ÉTÉ UTILISÉ
        victim = get_player_from_discord_user(GAME, discord.utils.get(GAME.guild.members, name=arg))
        if not(victim):
            await ctx.send("""Unknown player : {}. Please check your spelling""".format(arg))
            return
        if victim not in players_that_are_alive(GAME):
            await ctx.send("""You cannot killed an already dead player.""")
            return
        await victim.kill(GAME)
        get_player_from_discord_user(GAME, discord.utils.get(GAME.guild.members, name=arg)).state_hunter = True
        GAME.game_blocked = False
        get_player_from_discord_user(GAME, ctx.message.author).alive = False
        if not(GAME.night):
            GAME.night = True
            await GAME.launch_night()
        else:
            GAME.night = False
            await launch_day()


bot.run(TOKEN)
