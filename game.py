#!/usr/bin/env/python

import discord
from scrutin import Scrutin
from settings import Settings

class Game:
    def __init__(self, game_name):
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
        for role in self.roles:
            self.turns_played[role] = False
        #les villageois n'ont rien a faire
        for role in self.roles:
            self.turns_played[role] = False
        self.turns_played['VILLAGER'] = True


    def check_end_night(self):
        """VErifie si la nuit est finie, si oui détruit le dictionnaire turns_played. A appeler à l'issue de chaque commande de role de nuit, et si True est renvoyé on appelle launch_day"""
        if self.night:
            if not(False in [x for x in self.turns_played]):
                print('nuit finie !')
                self.turns_played = None
                return True
            print('nuit pas finie !')
        else:
            raise("Appel à check_end_night le jour, t'as du oublié un truc khey")
        

