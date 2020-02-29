#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 12:21:55 2020

@author: F Dupont
depuis l'exemple QCM de Fabrice Sincère
"""
# ubuntu : OK
# win XP, 7 : OK

# localhost : OK
# réseau local : OK (firewall à paramétrer)
# Internet : OK (box - routeur NAT à paramétrer)

# fonctionne aussi avec un simple client telnet
# telnet localhost 50026

import socket, sys, threading, time

# variables globales

# adresse IP et port utilisés par le serveur
HOST = ""
PORT = 50026

# 0 : fermeture, 1 : attente clients, 2 : attente ordre, 3 : demarre job1
# 4 : job1 en cours
etat_serveur = 1
list_clients = []  # liste des connexions clients
command = 'null'
coord = []

class ThreadDialog(threading.Thread):
    '''dérivation de classe pour gérer la connexion avec un client'''
    
    def __init__(self):
        threading.Thread.__init__(self)
        print('dialog start')
        
    def run(self):
        global command, etat_serveur, coord
        print(command)
        while etat_serveur >0:
            command = input('commande :')
            if command == 'fin':
                MessagePourTous('fin')
                etat_serveur = 0
            elif command == 'go':
                etat_serveur = 2
            elif command == 'boulot':
                etat_serveur = 3
            elif command[0] == '2':
                coord = command
                etat_serveur = 3
            command=''
        print(command, 'ok')
        etat_serveur = 0
        
class ThreadClient(threading.Thread):
    '''dérivation de classe pour gérer la connexion avec un client'''
    
    def __init__(self,conn):

        threading.Thread.__init__(self)
        global list_clients
        self.connexion = conn
        self.etat_client = 0
        # dictionnaire pour la transmission de paramêtre de balle
        self.coord_balle = {}
        
        # Mémoriser la connexion dans la liste
        self.nom = self.getName() # identifiant du thread "<Thread-N>"
        list_clients.append([self, self.connexion])
        
        print("Connexion du client", self.connexion.getpeername(),self.nom ,
              self.connexion)
        
        message = bytes("Vous êtes connecté au serveur.\n","utf-8")
        self.connexion.send(message)
        
    def run(self):
        global etat_serveur, coord
        self.connexion.send(b"Serveur connecte\n")
        # attente réponse client
        while etat_serveur > 0:
            message = self.connexion.recv(4096)
            message = message.decode(encoding='UTF-8')
            #print("message du client", self.connexion.getpeername(),">", message)
            if message:
                if message[0] == '3':
                    print(message)
                    coord = message.split(',')
                    self.etat_client = 0
        print("\nFin du thread",self.nom)
        self.connexion.close()

class ThreadJob1(threading.Thread):
    '''dérivation de classe pour gérer la connexion avec un client'''
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        global command, etat_serveur, list_clients, coord
        print('job1 start')
        list_clients[0][1].send(bytes(coord,"utf8"))
        list_clients[0][0].etat_client = 1
        # tant que le client n'a pas fini
        while list_clients[0][0].etat_client == 1:
            pass
        client, compteur = 0, 6
        for i in range(compteur):
            while client > -1:
                if int(coord[3]) > 0:
                    client += 1
                    coord[1] = '7'
                else:
                    client -= 1
                    coord[1] = '393'
                print(client)
                if client > -1:
                    coord[0]  ='2' 
                    coord = ','.join(coord)
                    print('envoi coord :', coord)
                    list_clients[client][1].send(bytes(coord,"utf8"))
                    list_clients[client][0].etat_client = 1
                    while (list_clients[client][0].etat_client == 1
                           and etat_serveur > 0):
                        pass
        # fin, remettre serveur en attente
        etat_serveur = 2
        print('job1 stop')
        
def MessagePourTous(message):
    """ message du serveur vers tous les clients"""
    for client in list_clients:
        client[1].send(bytes(message,"utf8"))

def job1(command):
    for client in list_clients:
        client[1].send(bytes(command,"utf8"))
        client[0].etat_client = 1
        # tant que le client n'a pas fini
        while client[0].etat_client == 1:
            pass
        
# Initialisation du serveur
# Mise en place du socket avec les protocoles IPv4 et TCP
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mySocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
try:
    mySocket.bind((HOST, PORT))
except socket.error:
    print("La liaison du socket à l'adresse choisie a échoué.")
    sys.exit()
print("Serveur prêt (port",PORT,") en attente de clients...")
mySocket.listen(5)
mySocket.settimeout(1.0)

# Démarrage du dialog
com = ThreadDialog()
com.start()

while etat_serveur == 1:
    # Attente connexion nouveau client
    try:
        connexion, adresse = mySocket.accept()
        # Créer un nouvel objet thread pour gérer la connexion
        th = ThreadClient(connexion)
        # The entire Python program exits when no alive non-daemon threads are left
        th.setDaemon(1)
        th.start()
    except socket.timeout:
        #print('socket timeout')
        pass

#mySocket.settimeout(5.0)
print(list_clients)
for i, c in enumerate(list_clients):
    if i == 0:
        c[1].send(bytes('1,gauche',"utf8"))
    elif i == len(list_clients)-1:
        c[1].send(bytes('1,droite',"utf8"))
    else:
        c[1].send(bytes('1,milieu',"utf8"))
        
MessagePourTous("\nDémarre\n")

while etat_serveur>0:
    if etat_serveur == 3:
        job = ThreadJob1()
        etat_serveur = 4
print('serveur fin')
job.join()
# fermeture des sockets
for client in list_clients:
    client[1].close()
    print("Déconnexion du socket", client)
th.join()
mySocket.close()
com.join()
input("\nAppuyer sur Entrée pour quitter l'application...\n")
# fermeture des threads (daemon) et de l'application