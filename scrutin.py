from utils import players_that_are_alive, players_that_are_wolves, players_that_are_not_wolves

class Scrutin:
    """Les clés sont les objets members de discord, cad l'attribut user de ma classe Player"""
    def __init__(self, GAME):
        self.votes = {} #votant:voté, None si pas encore voté
        self.suffrages = {} #joueur:nombre de vote sur sa geule
        for player in players_that_are_alive(GAME):
            self.votes[player.user] = None
            self.suffrages[player.user] = 0

    def get_majority(self):
        """renvoie le player avec le plus de vote, ne gère pas l'égalité pour le moment"""
        return max(self.suffrages, key=lambda k: self.suffrages[k])


class ScrutinWolf:
    def __init__(self, GAME):
        self.votes = {} #votant:voté, None si pas encore voté
        self.suffrages = {} #joueur:nombre de vote sur sa geule
        for player in players_that_are_wolves(GAME):
            self.votes[player.user] = None
        for player in players_that_are_not_wolves(GAME):
            self.suffrages[player.user] = 0
            
    def get_majority(self):
        """renvoie le player avec le plus de vote, ne gère pas l'égalité pour le moment"""
        return max(self.suffrages, key=lambda k: self.suffrages[k])