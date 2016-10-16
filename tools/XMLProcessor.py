#!/usr/bin/env python
'''
Created on Oct 4, 2016

@author: fu
'''

import os
import numpy as np
import xml.sax as sax
from Log import Log

# prcess the vasprun.xml, extract the lattics, forces and energy of every ionic step
class SaxHandler(sax.ContentHandler):
    def __init__(self, log=None):
        self.isComplete = True # whether data of a structure in vasprun.xml file is complete
        
        self.isAtominfo = False # <atominfo>
        self.isAtomNum = False # <atoms>
        self.isAtoms = False # <array name="atoms">
        self.isAtomSet = False # <set>
        self.isAtomName = False # <c>
        self.counter2AtomName = 0 # select the name of element from array of element and its type
        
        self.isCalculation = False
        self.isStructure = False
        self.isBasis = False
        self.isPositions = False
        self.isForces = False
        self.isEnergy = False
        self.isScstep = False

        # element set
        self.elementNum = 0
        self.element = []

        # save every ionic step
        self.tmpL = []
        self.tmpF = []
        self.tmpE = []

        # save all ionic step
        self.lattice = [] # [structure, basis+posiion, xyz]
        self.forces = []  # [structure, forceOfatom, xyz]
        self.energy = []  # [structure, energy, e_fr/e_wo/e_0]
        
        self.counter = -1 # counter of structure in vasprun.xml
        
        # log object
        if log == None:
            self.log=Log()
        else:
            self.log=log
        
    def startElement(self, name, attrs):
        
        if name == "atominfo":
            self.isAtominfo = True
        if self.isAtominfo and (name == "atoms"):
            self.isAtomNum = True
        if self.isAtominfo and (name == "array") and (attrs.getValueByQName("name") == "atoms"):
            self.isAtoms = True
        if self.isAtoms and (name == "set"):
            self.isAtomSet = True
        if self.isAtomSet and (name == "c"):
            if self.counter2AtomName == 0:
                self.isAtomName = True
        
        if name == "calculation":
            self.isCalculation = True
            self.counter += 1
                
        if self.isCalculation:
            if name == "structure":
                self.isStructure = True
            elif name == "scstep":
                self.isScstep = True
            elif (name == "varray") and (attrs.getValueByQName("name") == "forces"):
                self.isForces = True
            elif(name == "scstep"):
                self.isScstep = True
            elif (not self.isScstep) and (name == "energy"): # exclude the energy of scf
                self.isEnergy = True
                
        if self.isStructure:
            if (name == "varray") and (attrs.getValueByQName("name") == "basis"):
                self.isBasis = True
            elif (name == "varray") and (attrs.getValueByQName("name") == "positions"):
                self.isPositions = True
            
    def endElement(self, name):
        if name == "atominfo":
            self.isAtominfo = False
        if self.isAtominfo and (name == "atoms"):
            self.isAtomNum = False
        if self.isAtominfo and (name == "array"):
            self.isAtoms = False
        if self.isAtoms and (name == "set"):
            self.isAtomSet = False
        if self.isAtomSet and (name == "c"):
            if self.counter2AtomName == 0:
                self.isAtomName = False
            self.counter2AtomName=self.counter2AtomName+1
            if self.counter2AtomName == 2:
                self.counter2AtomName = 0
                   
        if name == "calculation":
            self.isCalculation = False
            
            # check data integrity
            # 1. pop illegal data
            if not(self.isComplete) or ():
                self.lattice.pop(-1)
                self.forces.pop(-1)
                self.energy.pop(-1)

        if self.isCalculation:
            if name == "structure":
                self.isStructure = False
            elif name == "scstep":
                self.isScstep = False
            elif self.isForces and (name == "varray"):
                self.isForces = False
                
                self.forces.append(self.tmpF)
                self.tmpF = []
                
            elif name == "scstep":
                self.isScstep = False
            elif (not self.isScstep) and (name == "energy"): # exclude the energy of scf
                self.isEnergy = False

                self.energy.append(self.tmpE)
                self.tmpE = []

        if self.isStructure:
            if self.isBasis and (name == "varray"):
                self.isBasis = False
            elif self.isPositions and (name == "varray"):
                self.isPositions = False
                
                self.lattice.append(self.tmpL)
                self.tmpL = []

    def characters(self, content):
        if self.isAtomNum:
            self.elementNum = int(content)
        if self.isAtomName:
            self.element.append(content)
        
        if self.isBasis:
            tmp = [float(s0) for s0 in content.split()]
            if (len(tmp) != 0):
                self.tmpL.append(tmp)
        elif self.isPositions:
            try:
                tmp = [float(s0) for s0 in content.split()]
            except ValueError:
                for s0 in content.split():
                    tmp=[]
                    if (s0 == "-"):
                        tmp.append(0.0)
                        string = "Warning! value of position will be set to 0.0"
                        print string
                        self.log.write(string)
                        self.isComplete = False
                    else:
                        tmp.append(float(s0))
                
            if (len(tmp) != 0):
                self.tmpL.append(tmp)
                    
        elif self.isForces:
            try:
                tmp = [float(s0) for s0 in content.split()]
            except ValueError:
                # log information
                string = "Force isn't a digit! '%s' -> 0.0; skipping" %content.strip()
                print string
                self.log.write(string)
                self.isComplete = False
                
                tmp = content.split()
                for i in xrange(0, len(tmp)):
                    try:
                        tmp[i] = float(tmp[i])
                    except ValueError:
                        self.isComplete = False
                        
                        tmp[i] = 0.0
                        
            if len(tmp) != 0:
                self.tmpF.append(tmp)
        elif self.isEnergy:
            try:
                tmp = [float(s0) for s0 in content.split()]                
            except ValueError:
                # log information
                string = "Energy isn't a digit! %s" %content
                print string
                self.log.write(string)
                self.isComplete = False                
                
                tmp = 0.0
                
            if len(tmp) != 0:
                self.tmpE.append(tmp[-1])
    
    def getElement(self):
        if len(self.element) != self.elementNum:
            self.log.write("Error! number of elements isn't consistent.")
        return np.array(self.element)
                    
    def getLattice(self):
        return np.array(self.lattice)
    
    def getForces(self):
        return np.array(self.forces)
    
    def getEnergy(self):
        return np.array(self.energy)


class XMLProcessor():
    def __init__(self, filename, log='None'):
        self.filename = filename
        # log object
        if log == None:
            self.log=Log()
        else:
            self.log=log
            
    def read(self):
        parser = sax.make_parser()
        handler = SaxHandler(self.log)
        parser.setContentHandler(handler)
        parser.parse(open(self.filename, "r"))

        element = handler.getElement()
        lattice = handler.getLattice()
        forces = handler.getForces()
        energy = handler.getEnergy()

        return element, lattice, forces, energy

# --------------------test--------------------
#x = XMLProcessor("/home/fu/workspace/nnp/Te/trainStructure/001/vasprun.xml")
#element, lattice, forces, energy = x.read()

#print element
#print lattice.shape
#print forces.shape
#print '%4.10f %4.10f %4.10f' %(forces[-1][-1][0], forces[-1][-1][1], forces[-1][-1][2])
#print energy.shape