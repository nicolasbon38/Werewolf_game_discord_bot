#!/usr/bin/env/python

import discord
from scrutin import Scrutin
from settings import Settings

class Game:
    def __init__(self, ctx, game_name):
        self.guild = ctx.guild
        self.name = game_name
        self.players = []
        self.roles = []
        self.started = False
        self.scrutin = None
        self.scrutinwolf = None
        self.night = False
        self.deaths_this_night = []
        self.settings = Settings()

    async def launch_night(self):
        self.night = True
        self.turns_played = {}
        self.deaths_this_night = []
        for role in self.roles:
            self.turns_played[role] = False
        #les villageois n'ont rien a faire
        self.turns_played['VILLAGER'] = True


    def check_end_night(self):
        """Vérifie si la nuit est finie, si oui détruit le dictionnaire turns_played. A appeler à l'issue de chaque commande de role de nuit, et si True est renvoyé on appelle launch_day"""
        print(self.turns_played)
        if self.night:
            print([x for x in self.turns_played])
            if not(False in [self.turns_played[x] for x in self.turns_played]):
                print('nuit finie !')
                self.turns_played = None
                return True
            print('nuit pas finie !')
            return False
        else:
            raise("Appel à check_end_night le jour, t'as du oublié un truc khey")
        

