#Imported libraries
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import os
import sys
from os.path import isfile, join
import re
import pickle
import time
from os import listdir
from copy import deepcopy
from math import *


sys.path.insert(0, 'DARK/python/')
from darknet import *

""" This is simply a script to test out the confidence of a recognition model
We also do all the crop head out part in here at the same time, so that we can just give any image
to start with  """

# this array stores the seen pets, we will store this array later in a file and not write it like this
global full
standSize = (150,150) #we take this a standard size to begin with


with open('PetName.txt','r') as f:
    full = [n.strip() for n in f.readlines() if n.strip() != '']

###########################################################################################################


""" Just some auxiliary func """

# i want to avoid any  copy of arrays so I will just output here the correct dimensions and resize using cv2 in main
def dimension(width,height):
    while width > standSize[0] or height > standSize[1]:
        width *= 0.99
        height *= 0.99
    return int(width),int(height) 


###########################################################################################################

""" All the nice classes here """

class Yoloface:

    def __init__(self,thresh=0.2,nms=0.1):
        self.net = load_net("DARK/cfg/cat-dog-yolov3-tiny.cfg".encode("utf-8"), "DARK/weights/front_prof_230k.weights".encode("utf-8"), 0)
        self.meta = load_meta("DARK/cfg/cat-dog-obj.data".encode('utf-8'))
        self.thresh = thresh
        self.nms = nms
            
    def detect(self,img):
        R = detect_s(self.net,self.meta,img,thresh=self.thresh,nms=self.nms)
        if len(R) == 0: 
            print('no damn thing detected')
            sys.exit(0)
        return R

class HaarCascadeExt:
    def __init__(self,SF=1.03,N=6):
        self.cat_ext_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalcatface_extended.xml')
        self.SF = SF
        self.N = N
    
    def detect(self,img,dim):
        R = self.cat_ext_cascade.detectMultiScale(img,scaleFactor=self.SF,minNeighbors=self.N,minSize=dim)
        return R


class Model:
    def __init__(self,filename,mod=1):
        
        if mod == 1:self.model = cv2.face.LBPHFaceRecognizer_create()
        elif mod == 2 :self.model = cv2.face.FisherFaceRecognizer_create()
        elif mod == 3 :self.model = cv2.face.EigenFaceRecognizer_create()
        try :
            self.model.read('models/'+filename)
        except:
            print("Alright, you must have a starting model to update later on")
            sys.exit(0)
        self.filename = filename
        self.mod = mod    

    def prediction(self,img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return self.model.predict(gray)
        
    def training(self,array,label_nb): #Might need to do some resizing here
        Training_Data, Labels = [] , [] 
        for im in array:
            Training_Data.append( np.asarray( im, dtype=np.uint8))
            Labels.append(label_nb)
        print('Gathering Data to train on !')
        Labels = np.asarray(Labels, dtype=np.int32) #I mean, i guess database won't exceed 256 for now
            
        face= np.asarray( Training_Data)
        if self.mod == 1:
            try: self.model.update(face,Labels) 
            except: sys.exit(0) 
        else: 
            try: self.model.train(face,Labels) 
            except: sys.exit(0) 
        print("Model updated sucessefully, Congratulations")
            
        try :self.model.save('models/'+self.filename)
        except: print('Could not save the model')



###########################################################################################################

""" Recognition script, just takes a filepath and then prints out confidence from what crop """

def recognize(filepath,verbose = False):

    if not os.path.exists(filepath): 
        print('File not found')
        sys.exit(0)


    #initialization
    yoloface = Yoloface(thresh=0.5,nms=0.1)
    cascadeExt = HaarCascadeExt(SF=1.03,N=5)
    model = Model('test.xml', mod=1)
    img = cv2.imread(filepath)
    
    #detection/cropping one
    R1 = yoloface.detect(img)
    for (R,P,(x,y,w,h)) in R1:

        x,y,w,h = int(x),int(y),int(w),int(h)
        x,y = x-w//2,y-h//2
        if x < 0: x = 0
        if y < 0: y = 0

        next = img[y:y+h,x:x+w]
        L = cascadeExt.detect(next,(w//3,h//3))

        if len(L) == 0: 
            
            next = cv2.resize(next,(150,150),interpolation=cv2.INTER_AREA)
            name,neg = model.prediction(next)
            print(full[name]+': '+str(neg)+' using Yoloface')
        else:
            X,Y,W,H = L[0] #assume uniqueness 
            start = time.time()
            tmp = cv2.resize(next[Y:Y+H,X:X+W],(150,150),interpolation=cv2.INTER_AREA)
            name, neg = model.prediction(tmp)
            print(time.time()-start)
            print(full[name]+': '+str(neg)+' using Cascade')
            if verbose: cv2.imwrite('result/'+full[name]+'_cascade.jpg',tmp)
        if verbose: cv2.imwrite('result/'+full[name]+'_yoloface.jpg',next)





###########################################################################################################

        

def main(): 
    #here through syntax, you can either train your file/ do videos_yolos/ or vid_yolo
    array = sys.argv[1:]
    if len(array) >= 3: print('Too many arguments check -h for usage')
    
    if array[0] == '-v':
        if len(array) == 1 : print('Not the right nb of argument, this feature receives only a path/filename')
        if len(array) == 2:  recognize(array[1],verbose=True)
    elif array[0] == '-h':
        if len(array) > 1: print('Not the right nb of argument, this requires no extra arguments')
        else: print('-v filepath: to see the cropped pictures ; filepath: no need for cropped pictures')
    elif array[0] != '-v': recognize(array[0])
    else:
        print("argument unknown check -h for usage")

if __name__ == '__main__':
    main()