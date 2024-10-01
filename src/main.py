# -*- coding: utf-8 -*-

# Nicolas, 2021-03-05
from __future__ import absolute_import, print_function, unicode_literals

import random 
import numpy as np
import sys
import math
import time
from itertools import chain


from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame  # it is important to import pygame after that

from pySpriteWorld.gameclass import Game,check_init_game_done
from pySpriteWorld.spritebuilder import SpriteBuilder
from pySpriteWorld.players import Player
from pySpriteWorld.sprite import MovingSprite
from pySpriteWorld.ontology import Ontology
import pySpriteWorld.glo

from search.grid2D import ProblemeGrid2D
from search import probleme






# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

game = Game()

def init(_boardname=None):
    global player,game
    name = _boardname if _boardname is not None else 'mini-quoridorMap'
    game = Game('./Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 5  # frames per second
    game.mainiteration()
    player = game.player
    
def main():

    #for arg in sys.argv:
    iterations = 100 # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    # print ("Iterations: ")
    # print (iterations)

    init()
    

    
    #-------------------------------
    # Initialisation
    #-------------------------------
    
    nbLignes = game.spriteBuilder.rowsize
    nbCols = game.spriteBuilder.colsize
    assert nbLignes == nbCols # a priori on souhaite un plateau carre
    lMin=2  # les limites du plateau de jeu (2 premieres lignes utilisees pour stocker les murs)
    lMax=nbLignes-2 
    cMin=2
    cMax=nbCols-2
   
    
    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)
    
       
           
    # on localise tous les états initiaux (loc du joueur)
    # positions initiales des joueurs
    initStates = [o.get_rowcol() for o in players]
    ligneObjectif = (initStates[1][0],initStates[0][0]) # chaque joueur cherche a atteindre la ligne ou est place l'autre 
    # print(ligneObjectif)
    
    # on localise tous les murs
    # sur le layer ramassable    
    walls = [[],[]]
    walls[0] = [o for o in game.layers['ramassable'] if (o.get_rowcol()[0] == 0 or o.get_rowcol()[0] == 1)]  
    walls[1] = [o for o in game.layers['ramassable'] if (o.get_rowcol()[0] == nbLignes-2 or o.get_rowcol()[0] == nbLignes-1)]
    allWalls = walls[0]+walls[1]
    nbWalls = len(walls[0])
    assert len(walls[0])==len(walls[1]) # les 2 joueurs doivent avoir le mm nombre de murs
    
    #-------------------------------
    # Fonctions permettant de récupérer les listes des coordonnées
    # d'un ensemble d'objets murs ou joueurs
    #-------------------------------
    
    def wallStates(walls): 
        # donne la liste des coordonnees dez murs
        return [w.get_rowcol() for w in walls]
    
    def playerStates(players):
        # donne la liste des coordonnees dez joueurs
        return [p.get_rowcol() for p in players]
    
   
    #-------------------------------
    # Rapport de ce qui est trouve sut la carte
    #-------------------------------
    # print("lecture carte")
    # print("-------------------------------------------")
    # print("lignes", nbLignes)
    # print("colonnes", nbCols)
    # print("Trouvé ", nbPlayers, " joueurs avec ", int(nbWalls/2), " murs chacun" )
    # print ("Init states:", initStates)
    # print("-------------------------------------------")

    #-------------------------------
    # Carte demo 
    # 2 joueurs 
    # Joueur 0: place au hasard
    # Joueur 1: A*
    #-------------------------------
    
        
    #-------------------------------
    # On choisit une case objectif au hasard pour chaque joueur
    #-------------------------------
    
    allObjectifs = ([(ligneObjectif[0],i) for i in range(cMin,cMax)],[(ligneObjectif[1],i) for i in range(cMin,cMax)])
    # print("Tous les objectifs joueur 0", allObjectifs[0])
    # print("Tous les objectifs joueur 1", allObjectifs[1])
    global objectifTab
    objectifTab = [0,0]
    # objectifs =  (allObjectifs[0][random.randint(cMin,cMax-3)], allObjectifs[1][random.randint(cMin,cMax-3)])
    # print("Objectif joueur 0 choisi au hasard", objectifs[0])
    # print("Objectif joueur 1 choisi au hasard", objectifs[1])

    #-------------------------------
    # Fonctions definissant les positions legales et placement de mur aléatoire
    #-------------------------------
    
    def legal_wall_position(pos):
        row,col = pos
        # une position legale est dans la carte et pas sur un mur deja pose ni sur un joueur
        # attention: pas de test ici qu'il reste un chemin vers l'objectif
        return ((pos not in wallStates(allWalls)) and (pos not in playerStates(players)) and row>lMin and row<lMax-1 and col>=cMin and col<cMax)

                    
    def legal_wall_position_and_path(player,pos1,pos2):
        enemy = (player+1)%2
        objectifTabTemp = [0,0]
        objectifTabTemp[player] = objectifTab[player]
        objectifTabTemp[enemy] = objectifTab[enemy]
        objectifTabRes = [0,0]
        row1,col1 = pos1
        row2,col2 = pos2
        if ((pos1 not in wallStates(allWalls)) and (pos1 not in playerStates(players)) and row1>lMin and row1<lMax-1 and col1>=cMin and col1<cMax) and ((pos2 not in wallStates(allWalls)) and (pos2 not in playerStates(players)) and row2>lMin and row2<lMax-1 and col2>=cMin and col2<cMax) :
            
            # On garde en mémoire l'ancien emplacement du mur
            loc1Init = walls[player][cmptWalls[player]].get_rowcol()
            loc2Init = walls[player][cmptWalls[player]+1].get_rowcol()

            # Puis on simule le placement du mur
            walls[player][cmptWalls[player]].set_rowcol(row1,col1)
            walls[player][cmptWalls[player]+1].set_rowcol(row2,col2)

            # On calcul les objectifs et path des deux joueurs après avoir posé ce mur
            objectifTab[player], newPathP1 = findObjectif(player)
            objectifTab[enemy], newPathP2 = findObjectif(enemy)

            if objectifTab[player] not in newPathP1 or objectifTab[enemy] not in newPathP2:
                # Il ne faut pas oublier de re-mettre à zero les valeurs objectif, walls, etc.
                objectifTab[player] = objectifTabTemp[player]
                objectifTab[enemy] = objectifTabTemp[enemy]
                (row,col) = loc1Init
                walls[player][cmptWalls[player]].set_rowcol(row,col)
                (row,col) = loc2Init
                walls[player][cmptWalls[player]+1].set_rowcol(row,col)
                return False, -1, -1, -1, -1
            
            objectifTabRes[player] = objectifTab[player]
            objectifTabRes[enemy] = objectifTab[enemy]

            # Il ne faut pas oublier de re-mettre à zero les valeurs objectif, walls, etc.
            objectifTab[player] = objectifTabTemp[player]
            objectifTab[enemy] = objectifTabTemp[enemy]
            (row,col) = loc1Init
            walls[player][cmptWalls[player]].set_rowcol(row,col)
            (row,col) = loc2Init
            walls[player][cmptWalls[player]+1].set_rowcol(row,col)
            
            return True, newPathP1, newPathP2, objectifTabRes[player], objectifTabRes[enemy]
        
        return False, -1, -1, -1, -1
            
                    
    def draw_random_wall_legal_path(player):
        # tire au hasard un couple de position permettant de placer un mur
        while True:
            random_loc = (random.randint(lMin,lMax),random.randint(cMin,cMax))
            if legal_wall_position(random_loc):  
                inc_pos =[(0,1),(0,-1),(1,0),(-1,0)] 
                random.shuffle(inc_pos)
                for w in inc_pos:
                    random_loc_bis = (random_loc[0] + w[0],random_loc[1]+w[1])
                    (bool,_,_,_,_) = legal_wall_position_and_path(player,random_loc,random_loc_bis)
                    if bool:
                        return(random_loc,random_loc_bis)


    def locOfTheBestWall(player):
        global paths
        temp = []
        resLoc1, resLoc2 = -1,-1
        resPathPlayer, resPathEnemy, resObjectifPlayer, resObjectifEnemy = -1, [], -1, -1
        best = 0
        enemy = (player+1)%2
        objectifTabTemp = [0,0]
        objectifTabTemp[player] = objectifTab[player]
        objectifTabTemp[enemy] = objectifTab[enemy]

        for i in range(nbLignes):
            for j in range(nbCols):
                loc1 = (i,j)
                if legal_wall_position(loc1):
                    inc_pos =[(0,1),(0,-1),(1,0),(-1,0)]
                    for w in inc_pos:
                        loc2 = (i+w[0],j+w[1])
                        (bool, newPathPlayer, newPathEnemy, newObjectifPlayer, newObjectifEnemy) = legal_wall_position_and_path(player,loc1,loc2)
                        if bool:
                            if len(newPathEnemy) > len(paths[enemy]) and len(newPathEnemy) > len(resPathEnemy):
                                if (best == 1 and len(paths[player]) == len(newPathPlayer)) or best != 1:
                                    resLoc1 = loc1
                                    resLoc2 = loc2
                                    resPathPlayer = newPathPlayer
                                    resPathEnemy = newPathEnemy
                                    resObjectifPlayer = newObjectifPlayer
                                    resObjectifEnemy = newObjectifEnemy
                                    if len(paths[player]) == len(newPathPlayer):
                                        best = 1    # un des meilleurs coups

                            elif len(newPathEnemy) > len(paths[enemy]) and len(newPathEnemy) == len(resPathEnemy):
                                if (best == 1 and len(paths[player]) == len(newPathPlayer)) or best != 1:
                                    (rowTemp,colTemp) = resLoc1; (rowP,colP) = posPlayers[player]; (rowNew,colNew) = loc1
                                    if (math.sqrt((rowTemp - rowP)**2 + (colTemp - colP)**2) < math.sqrt((rowNew - rowP)**2 + (colNew - colP)**2)):
                                        resLoc1 = loc1
                                        resLoc2 = loc2
                                        resPathPlayer = newPathPlayer
                                        resPathEnemy = newPathEnemy
                                        resObjectifPlayer = newObjectifPlayer
                                        if len(paths[player]) == len(newPathPlayer):
                                            best = 1    # un des meilleurs coups


        return (resLoc1, resLoc2, resPathPlayer, resPathEnemy, resObjectifPlayer, resObjectifEnemy)


    #-------------------------------
    # Fonctions permettent de placer un mur
    #-------------------------------

    def placeRandomWall(player, cmpt):
        ((x1,y1),(x2,y2)) = draw_random_wall_legal_path(player)
        walls[player][cmpt].set_rowcol(x1,y1)
        walls[player][cmpt+1].set_rowcol(x2,y2)
        game.mainiteration()
        cmpt += 2
        return cmpt

    # exemple d'utilisation :
    # cmptWallsP1 = placeRandomWall(1, cmptWallsP1)

    def placeWall(player, cmpt, loc1, loc2):
        ((x1,y1),(x2,y2)) = (loc1,loc2)
        walls[player][cmpt].set_rowcol(x1,y1)
        walls[player][cmpt+1].set_rowcol(x2,y2)
        game.mainiteration()
        cmpt += 2
        return cmpt
    

    def findObjectif(player):
        res = 0
        
        for i in allObjectifs[player]:
            pathTemp = findPath(player, i)
            
            if res != 0:
                if len(pathRes) > len(pathTemp):
                    res = i
                    pathRes = pathTemp
            else:
                res = i
                pathRes = pathTemp

        return res, pathRes


    #-------------------------------
    # calcul A* pour un joueur
    #-------------------------------
    
    def findPath(player, objectif):
        g =np.ones((nbLignes,nbCols),dtype=bool)  # une matrice remplie par defaut a True  
        for w in wallStates(allWalls):            # on met False quand murs
            g[w]=False
        for i in range(nbLignes):                 # on exclut aussi les bordures du plateau
            g[0][i]=False
            g[1][i]=False
            g[nbLignes-1][i]=False
            g[nbLignes-2][i]=False
            g[i][0]=False
            g[i][1]=False
            g[i][nbLignes-1]=False
            g[i][nbLignes-2]=False

        p = ProblemeGrid2D(initStates[player],objectif,g,'manhattan')
        path = probleme.astar(p,verbose=False)
        return path

    
    #-------------------------------
    # Déplacements d'un joueur
    #-------------------------------
            
    def move(player, path, posPlayers):    
        row,col = path[1]
        posPlayers[player]=(row,col)
        players[player].set_rowcol(row,col)
        # print("pos joueur ", player+1, " : ", row,col)
        
        # mise à jour du pleateau de jeu
        game.mainiteration()
        
        return posPlayers


    #-------------------------------
    # Stratégies
    #-------------------------------


    def stratRandom(player, path):
        global cmptWalls
        global posPlayers

        # déplacement = 0 ; poser mur = 1
        action = random.randint(0,1)

        if cmptWalls[player] != len(walls[player]):
            if action == 0:
                posPlayers = move(player, path, posPlayers)
                
            else:
                cmptWalls[player] = placeRandomWall(player, cmptWalls[player])
            
        else:
            posPlayers = move(player, path, posPlayers)
    

    def stratHalf(player, path, last):
        global cmptWalls
        global posPlayers
        
        # last == 0 signifie que le dernier coup etait un move / last == 1 , un placeWall

        if cmptWalls[player] != len(walls[player]):     # Un wall est-il disponible ?
            loc1,loc2,_,_,_,_ = locOfTheBestWall(player)     # Si oui, y'a t-il un bon wall ?
            if (loc1,loc2) != (-1,-1):
                
                # Si last = 1, alors on se déplace
                if last == 1:
                    posPlayers = move(player, path, posPlayers)
                    last = 0

                # si last = 0, alors on pose ce mur disponible
                else:
                    cmptWalls[player] = placeWall(player, cmptWalls[player], loc1, loc2)
                    last = 1

                # apres avoir joué on sort de la fonction
                return last
        
        # Si aucun wall n'est dispo ou aucun wall n'est posable, alors on se déplace
        posPlayers = move(player, path, posPlayers)
        last = 0

        return last

    global cmpt0
    global cmpt1
    cmpt0 = 0
    cmpt1 = 0

    def stratEarlyWall(player, path):
        global cmpt0
        global cmpt1

        def earlyWall(player, path, cmpt):
            global cmptWalls
            global posPlayers

            (row,col) = posPlayers[player]

            if (row == 4 or row == 6) and cmpt < 3:
                if cmptWalls[player] != len(walls[player]):
                    loc1,loc2,_,_,_,_ = locOfTheBestWall(player)
                    if (loc1,loc2) != (-1, -1):
                        cmptWalls[player] = placeWall(player, cmptWalls[player], loc1, loc2)
                    else:
                        posPlayers = move(player, path, posPlayers)
                else:
                    posPlayers = move(player, path, posPlayers)
                   
                return cmpt + 1

            else:
                posPlayers = move(player, path, posPlayers)
            
            return cmpt

        if player == 0:
            cmpt0 = earlyWall(player, path, cmpt0)
        else:
            cmpt1 = earlyWall(player, path, cmpt1)

        
        

    global valeur
    valeur = {}
    successeurs = {'j':['p1','p2'],'p1':['a','b'],'p2':['c','d']}   # Pour mieux comprendre notre arbre, je vous renvoie au schéma présent dans le README.md
    inf = 1000  # joue le role de infini

    def initValues(player, pathP1):
        global cmptWalls
        global posPlayers

        # 0 : coup negatif pour player
        # 1 : coup moyen
        # 2 : coup positif

        # Variables nécéssaire pour nos calculs
        player2 = (player+1)%2
        pathP2 = findPath(player2, objectifTab[player2])
        objectifTabTemp = [0,0]
        objectifTabTemp[0] = objectifTab[0]
        objectifTabTemp[1] = objectifTab[1]

        pathsTemp = [0,0]
        pathsTemp[0] = paths[0]
        pathsTemp[1] = paths[1]

        # Premiere possibilité : p1 move -> p2 move
        values = {'a':1}    # Si les deux avancent vers leur objectif respectif, l'enchainement est considéré comme moyen, donc = 1


        # Deuxieme possiblilité : p1 move -> p2 wall
        row,col = pathP1[1]
        players[player].set_rowcol(row,col)     # On simule le déplacement du joueur 1 vers l'objectif (On le replacera après notre calcul)

        if cmptWalls[player2] != len(walls[player2]):   # Le joueur 2 a-t-il encore un mur de disponible ?
            paths[player] = findPath(player,objectifTab[player])
            (loc1,loc2,newPathP2,newPathP1,_,_) = locOfTheBestWall(player2)  # Un wall est-il posable ? Si oui loc1,loc2 est le meilleur
            if (loc1,loc2) != (-1, -1):

                # Puis on évalue la note de cet enchainement grace à notre fonction rateThisPlay
                values['b'] = rateThisPlay(pathP1, newPathP1, pathP2, newPathP2)

        if 'b' not in values:
            val = values['a']
            values['b'] = val     # Le coup ne se produira pas car p2 ne posera pas de wall, donc c'est comme si il se deplacait et que p2 se deplacait aussi donc situation a

        # On replace notre joueur 1 à sa place initiale au début du round
        (row,col) = posPlayers[player]
        players[player].set_rowcol(row,col)

        # On remet a son état initial le path de player
        paths[player] = pathsTemp[player]


        # Troisieme possibilité : p1 wall -> p2 move
        if cmptWalls[player] != len(walls[player]):     # Le joueur 1 a-t-il encore un mur de disponible ?
            (loc1,loc2,newPathP1,newPathP2,objectifTab[player],objectifTab[player2]) = locOfTheBestWall(player)   # Un wall est-il posable ? Si oui loc1,loc2 est le meilleur
            if (loc1,loc2) != (-1, -1):
                # On pose le mur puis on l'enlevera pour trouver le path de P2 avec ce mur :

                # On garde en mémoire l'ancien emplacement du mur
                loc1Init = walls[player][cmptWalls[player]].get_rowcol()
                loc2Init = walls[player][cmptWalls[player]+1].get_rowcol()

                # Puis on simule le placement du mur
                (row1,col1) = loc1
                (row2,col2) = loc2
                walls[player][cmptWalls[player]].set_rowcol(row1,col1)
                walls[player][cmptWalls[player]+1].set_rowcol(row2,col2)

                # On simule le déplacement du joueur 2 vers l'objectif (On le replacera après notre calcul)
                row,col = newPathP2[1]
                players[player2].set_rowcol(row,col)
                newPathP2 = findPath(player2, objectifTab[player2])

                # Puis on évalue la note de cet enchainement grace à notre fonction rateThisPlay
                values['c'] = rateThisPlay(pathP1, newPathP1, pathP2, newPathP2)

                # Il ne faut pas oublier de re-mettre à zero les valeurs objectif, position, etc.
                (row,col) = posPlayers[player2]
                players[player2].set_rowcol(row,col)
                (row,col) = loc1Init
                walls[player][cmptWalls[player]].set_rowcol(row,col)
                (row,col) = loc2Init
                walls[player][cmptWalls[player]+1].set_rowcol(row,col)
        
        if 'c' not in values:
            val = values['a']
            values['c'] = val     # Le coup ne se produira pas car player1 ne posera pas de wall, donc c'est comme si on effectuait l'enchainement a
        
        objectifTab[player] = objectifTabTemp[player]
        objectifTab[player2] = objectifTabTemp[player2]


        # Quatrieme possibilité : p1 wall -> p2 wall
        if cmptWalls[player] != len(walls[player]):     # Le joueur 1 a-t-il encore un mur de disponible ?
            (loc1,loc2,newPathP1,newPathP2,objectifTab[player],objectifTab[player2]) = locOfTheBestWall(player)   # Un wall est-il posable ? Si oui loc1,loc2 est le meilleur
            if (loc1,loc2) != (-1, -1):
                if cmptWalls[player2] != len(walls[player2]):   # Le joueur 2 a-t-il encore un mur de disponible ?
                    # On pose le mur puis on l'enlevera pour trouver le path de P2 avec ce mur :

                    # On garde en mémoire l'ancien emplacement du mur
                    loc1Init = walls[player][cmptWalls[player]].get_rowcol()
                    loc2Init = walls[player][cmptWalls[player]+1].get_rowcol()

                    # Puis on simule le placement du mur
                    (row1,col1) = loc1
                    (row2,col2) = loc2
                    walls[player][cmptWalls[player]].set_rowcol(row1,col1)
                    walls[player][cmptWalls[player]+1].set_rowcol(row2,col2)

                    # On modifie les valeurs de paths pour leurs utilisation dans locOfTheBestWall
                    paths[player] = newPathP1
                    paths[player2] = newPathP2

                    (loc1P2,loc2P2,newPathP2,newPathP1,objectifTab[player2],objectifTab[player]) = locOfTheBestWall(player2)  # Un wall est-il posable ? Si oui loc1,loc2 est le meilleur
                    if (loc1P2,loc2P2) != (-1, -1):
                        # Puis on évalue la note de cet enchainement grace à notre fonction rateThisPlay
                        values['d'] = rateThisPlay(pathP1, newPathP1, pathP2, newPathP2)
                    
                    (row,col) = loc1Init
                    walls[player][cmptWalls[player]].set_rowcol(row,col)
                    (row,col) = loc2Init
                    walls[player][cmptWalls[player]+1].set_rowcol(row,col)

                    paths[player] = pathsTemp[player]
                    paths[player2] = pathsTemp[player2]

                if 'd' not in values:
                    val = values['c']
                    values['d'] = val     # Le coup ne se produira pas car player2 ne posera pas de wall, donc c'est égal à l'enchainement c

        # Il ne faut pas oublier de re-mettre à zero les valeurs objectifs
        objectifTab[player] = objectifTabTemp[player]
        objectifTab[player2] = objectifTabTemp[player2]

        if 'd' not in values:
            if cmptWalls[player2] != len(walls[player2]):   # Le joueur 2 a-t-il encore un mur de disponible ?
                val = values['b']
                values['d'] = val     # p1 se déplace donc et p2 pose un mur donc enchainement b (ici pas besoin de calculer locOfTheBestWall() car si il n'y a pas de mur posable pour p2, alors la valeur de la feuille b sera égale à celle de a)
            else:
                val = values['a']
                values['d'] = val    # P1 se déplace donc et p2 aussi donc enchainement a


        return values

    def rateThisPlay(pathP1, newPathP1, pathP2, newPathP2):
        oldP1 = len(pathP1)
        newP1 = len(newPathP1)
        oldP2 = len(pathP2)
        newP2 = len(newPathP2)

        if oldP1 - newP1 > oldP2 - newP2:
            return 2
        elif oldP1 - newP1 == oldP2 - newP2:
            return 1
        
        return 0

    def minimax(state, player, path):
        global valeur
        valeur = initValues(player, path)
        # print(valeur)
        v, state = maxValue(state, -inf, inf)
        return state

    def feuille(state):
        if state in valeur:
            return True
        return False

    def maxValue(state, alpha, beta):
        if feuille(state): # si feuille on renvoie la valeur
            return valeur[state], state
        v = -inf
        st = state
        for s in successeurs[state]:
            vPrime, sPrime = minValue(s, alpha, beta)
            if vPrime > v:
                v = vPrime
                st = s
            if v >= beta:
                return v, st
            alpha = max(alpha, v)
        return v, st
                
    def minValue(state, alpha, beta):
        if feuille(state): # si feuille on renvoie la valeur
            return valeur[state], state
        v = inf
        st = state
        for s in successeurs[state]:
            vPrime, sPrime = maxValue(s, alpha, beta) 
            if vPrime < v:
                v = vPrime
                st = s
            if v >= alpha:
                return v, st
            beta = max(beta, v)
        return v, st


    def stratMiniMax(player, path):
        global cmptWalls
        global posPlayers

        choix = minimax('j', player, path)
        if choix == 'p1' and valeur['a']+valeur['b'] >= valeur['c']+valeur['d']:
            posPlayers = move(player, path, posPlayers)
        else:
            loc1,loc2,_,_,_,_ = locOfTheBestWall(player)
            cmptWalls[player] = placeWall(player, cmptWalls[player], loc1, loc2)
    

    #-------------------------------
    # Lancement du jeu
    #-------------------------------
    

    def start():
        global posPlayers
        global objectifTab
        global cmptWalls
        global paths

        posPlayers = initStates

        cmptWalls = [0,0]

        paths = [0,0]

        # rand = random.randint(0,1)

        # if rand == 1:
        #     player1 = 1
        #     player2 = 0
        
        # else:
        player1 = 0
        player2 = 1

        # si on utilise stratHalf :
        last1 = random.randint(0,1)
        last2 = random.randint(0,1)


        for i in range(iterations):
            objectifTab[player1], paths[player1] = findObjectif(player1)
            objectifTab[player2], paths[player2] = findObjectif(player2)

            stratMiniMax(player1, paths[player1])

            if posPlayers[player1] == objectifTab[player1]:
                # print("le joueur ", player1+1, " a atteint son but!")
                print(player1+1)
                return

            objectifTab[player1], paths[player1] = findObjectif(player1)
            objectifTab[player2], paths[player2] = findObjectif(player2)

            stratRandom(player2, paths[player2])

            if posPlayers[player2] == objectifTab[player2]:
                # print("le joueur ", player2+1, " a atteint son but!")
                print(player2+1)
                return

    start()

    pygame.quit()
    
    
    
    
    #-------------------------------
    
        
    
    
   

if __name__ == '__main__':
    main()
    


