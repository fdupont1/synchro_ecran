#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 12:19:37 2020

@author: F Dupont
depuis l'exemple QCM de Fabrice Sincère
"""

# python 3
# ubuntu : OK
# win XP, 7 : OK

# biblio : Gérard Swinnen

# Définition d'un client réseau gérant en parallèle l'émission
# et la réception des messages (utilisation de 2 THREADS).

# adresse IP et port utilisé par le serveur

import socket, sys, threading, time, tkinter

HOST = "192.168.1.10"
PORT = 50026

"""
etat :
0, arrêt du client
1, attente des autres clients
2, job 1
3, fin job 1
"""

etat = 1

class job1_tk(tkinter.Tk):

    def __init__(self):
        tkinter.Tk.__init__(self)
        # création de la fenêtre

        self.bind_all('q', self.destroy)
        # création de la zone de dessin
        self.canv = tkinter.Canvas(self, width=400, height=300, background='#fff')
        self.canv.pack()
        # création de la balle
        # balle, coordonnées du centre et rayon
        self.xb, self.yb, self.r = 55, 55, 5
        self.balle = self.canv.create_oval(self.xb-self.r,self.yb-self.r,
                                           self.xb+self.r,self.yb+self.r,
                                           fill="red", tag='balle')
        self.canv.itemconfigure(self.balle, state = 'hidden')
        # déplacement sur x et y
        self.dx,self.dy = 2,3
        # position du client gauche, milieu ou droite
        self.position = ''

    def exit(self):
        self.quit()
        
    # renvoi les coordonnées de la balle et son déplacement
    def coord_balle(self):
        x = self.canv.coords('balle')[0]+self.r
        y = self.canv.coords('balle')[1]+self.r
        return x, y, self.dx, self.dy
    
    # positionne la balle
    def pos_balle(self, x, y):
        print('def pos_balle')
        self.canv.coords('balle', x-self.r, y-self.r, x+self.r, y+self.r)
        self.canv.itemconfigure(self.balle, state = 'normal')

    # Fonction pour animer le canevas
    def animation(self) :
        global etat
        if etat == 2 :

            # test de collision avec les bords et inversion de la direction
            # si bord gauche ou droit
            if self.canv.coords(self.balle)[2] > 400:
                print('tape droite')
                if self.position != 'droite':
                    self.canv.itemconfigure(self.balle, state = 'hidden')
                    etat = 3
                    #break
                else:
                    self.dx = -self.dx

            elif self.canv.coords(self.balle)[0] < 0:
                print('tape gauche')
                if self.position != 'gauche':
                    self.canv.itemconfigure(self.balle, state = 'hidden')
                    etat = 3
                    #break
                else:
                    self.dx = -self.dx

            # si bord haut ou bas
            if self.canv.coords(self.balle)[3] > 300 or self.canv.coords(self.balle)[1] < 0 :
                self.dy = -self.dy

            self.canv.move('balle',self.dx,self.dy)
        if etat == 2 :
            self.canv.after(50, self.animation)
            #self.canv.after(50)
            #self.canv.update()
        #print('fin animation')    

        
class ThreadReception(threading.Thread):
    """objet thread gérant la réception des messages"""

    def __init__(self, conn, gui):
        threading.Thread.__init__(self)
        self.connexion = conn  # réf. du socket de connexion
        self.gui = gui

    def run(self):
        global etat
        while etat > 0:
            try:
                # en attente de réception
                message_recu = self.connexion.recv(4096)
                message_recu = message_recu.decode(encoding='UTF-8')
                # protocole message :
                # 1 : config du client, 'gauche' ou 'milieu' ou 'droite'
                # 2 : lancement animation, coord x, y et déplacement dx, dy
                if message_recu == 'fin':
                    print('client reçoit fin')
                    etat = 0
                    break

                elif message_recu[0] == '1':
                    message_recu = message_recu.split(',')
                    print('client position :',message_recu[1])
                    self.gui.position = message_recu[1]
                    
                elif message_recu[0] == '2':
                    message_recu = message_recu.split(',')
                    print('message recu :',message_recu)
                    self.gui.pos_balle(int(float(message_recu[1])),int(float(message_recu[2])))
                    self.gui.dx, self.gui.dy = int(float(message_recu[3])),int(float(message_recu[4]))
                    etat = 2
                    self.gui.animation()

                elif message_recu == 'boulot':
                    print('message serveur : boulot')
                    etat = 2
                    gui.animation()

                else:
                    print(message_recu)
            except:
                # fin du thread
                print('probleme connexion')
                break
        print("ThreadReception arrêté. Connexion interrompue.")
        self.connexion.close()
        gui.exit()

class ThreadEmission(threading.Thread):
    """objet thread gérant l'émission des messages"""

    def __init__(self, conn, gui):
        threading.Thread.__init__(self)
        self.connexion = conn   # réf. du socket de connexion
        self.gui = gui

    def run(self):
        global etat
        print('attente emission')
        while etat != 0:
            if etat == 3:
                try:
                    # émission
                    message =''
                    for val in self.gui.coord_balle():
                        message += ','+str(val)
                    message ='3'+message
                    print('envoi :', message)
                    self.connexion.send(bytes(message,'UTF-8'))
                except:
                    # fin du thread
                    break
                etat = 1
        print("ThreadEmission E arrêté. Connexion interrompue.")
        self.connexion.close()

class ThreadWork(threading.Thread):
    """objet thread gérant l'émission des messages"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.gui = job1_tk()

    def run(self):
        global etat
        print('attente emission')
        while etat != 0:
            if etat == 2:
                self.gui.update()
                etat = 3

        print("ThreadWork arrêté.")


# Programme principal - Établissement de la connexion
# protocoles IPv4 et TCP
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mySocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
try:
    mySocket.connect((HOST, PORT))
except socket.error:
    print("La connexion a échoué.")
    sys.exit()

# Dialogue avec le serveur : on lance deux threads pour gérer
# indépendamment l'émission et la réception des messages
#th_W = ThreadWork()
#th_W.start()
gui = job1_tk()
th_R = ThreadReception(mySocket, gui)
th_R.start()
th_E = ThreadEmission(mySocket, gui)
th_E.start()

gui.mainloop()

th_R.join()
th_E.join()
gui.destroy()
#th_W.join()
print('fermeture du client')
