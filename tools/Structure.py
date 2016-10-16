#!/usr/bin/env python
'''
Created on Oct 4, 2016

@author: fu
'''

import numpy as np
import os
from progressbar import *
from Log import Log
from XMLProcessor import XMLProcessor

class Structure(object):
    '''
    generate the XSF-formatted structure files come from vasprun.xml of VASP
    
    Args:
        path: path of structures
    '''

    def __init__(self, path):
        if path == None:
            self.path = os.getcwd()
        else:
            self.path = path
            
        if os.path.exists(self.path+'/monitor.log'):
            os.system('rm %s/monitor.log' %self.path)
        self.log=Log(self.path)
    
    def direct2cartesian(self, lattice):
        '''
        transfer direct to cartesian
        
        '''
        for i in xrange(3, lattice.shape[0]): # atom
            tmp = 0
            for j in xrange(0, lattice.shape[1]): # dirction
                tmp += lattice[i][j]*lattice[j]
            lattice[i] = tmp
        return lattice
        
        
    def  translate2XSFs(self, files, fileLength=3, identifier='vasprun.xml', fileLength2=4):  
        '''
        batch version to XSF files
        
        Args:
            files: [start, end]
            fileLength: length of file name
            identifier: indicate the start of a structure to distinguish these different structures
            fileLength2: length of file name
        '''
        if not(os.path.exists(self.path+'/xsf')):
           os.mkdir(self.path+'/xsf')
        else:
            os.system('rm -r %s/xsf/*' %self.path)
        
        # progress bar
        pbar = ProgressBar(widgets=['Read: ', Percentage(), ' ', Bar(),
                                    ' ', ETA()], maxval=files[1]).start()
                                    
        counter=0 # counter of XSF files
        for ii in xrange(files[0], files[1]):
            dir = (fileLength - len(str(ii))) * "0" + str(ii)
            # ensure exist directory
            try:
                os.chdir(self.path+'/'+dir)
            except OSError:
                string =  "No such directory: " + dir
                self.log.write(string)
                string = "Warning! skip this directory."
                self.log.write(string)
                continue
            # ensure exist needed file
            try:
                element, lattice, forces, energy= XMLProcessor(identifier, self.log).read()
                
                for j in xrange(lattice.shape[0]):
                    counter=counter+1
                    filename='structure'+(fileLength2 - len(str(counter)))*"0"+str(counter)+'.xsf'
                                    
                    self.outXSF(element, lattice[j], forces[j], energy[j], filename)
                    
                    #print filename
                #print lattice.shape
                #print forces.shape
                #print energy.shape
            except IOError:
                string = "vasprun.xml is inexistent! " + str(ii)
                self.log.write(string)
                continue
            
             #time.sleep(0.01)
            #pbar.update(ii)
            #print os.getcwd()
            os.chdir(self.path)
            
        #pbar.finish()
        
    def outXSF(self, element, lattice, forces, energy, filename):
        with open(self.path+'/xsf/'+filename, 'w') as out:
            element=np.array(element)
            lattice=np.array(lattice)
            forces=np.array(forces)
            energy=np.array(energy)
            #print lattice.shape[1], forces.shape[1], energy.shape
            
            try:
                if (lattice.shape[1]) == 3 and (forces.shape[1] == 3) and (lattice.shape[0] == forces.shape[0])+3 and (energy.shape[0] == 3):
                    lattice=self.direct2cartesian(lattice)
                    
                    out.write('# total energy = %14.10f eV\n\n' % energy[0])
            
                    out.write('CRYSTAL\n')
                    out.write('PRIMVEC\n')
            
                    for i in xrange(3):
                        out.write('\t%14.10f \t%14.10f \t%14.10f\n' %(lattice[i][0], lattice[i][1], lattice[i][2]))
                
                    out.write('PRIMCOORD\n')
                    out.write('%d 1\n' %element.shape[0])
                    for i in xrange(0, forces.shape[0]):
                        out.write('%s  \t%14.10f \t%14.10f \t%14.10f  \t%14.10f \t%14.10f \t%14.10f\n' 
                                  %(element[i], lattice[i+3][0], lattice[i+3][1], lattice[i+3][2], forces[i][0], forces[i][1], forces[i][2]))
                    
            except IndexError:
                self.log.write("lattice:"+str(lattice.shape)+"\tforces:"+str(forces.shape)+"\tenergy:"+str(energy.shape))
            
# --------------------test--------------------
s=Structure('/home/fu/workspace/nnp/Te/trainStructure')
#s=Structure('/home/fu/workspace/nnp/SiO2/trainStructure')
s.translate2XSFs([1,200],fileLength=3)

