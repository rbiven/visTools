'''
 utilities for groundwater flow model visualization
 expects binary head output from modflow (http://water.usgs.gov/ogw/modflow/)
 writes BOV files for visualization in VisIt (https://wci.llnl.gov/codes/visit/)
 
 currently supports only uniform grid models (x and y dimensions can differ,
 but they cannot be variably spaced)
'''
__author__='fluidmotion'

import os,sys,struct

class visMod():
    '''class to read modflow binary heads or cell-by-cell flow and write bov files for VisIt
    expects model layer to be visualized, model precision, x and y cell dimensions
    origin of bottom left, name of binary heads file, output path for BOV.
    additional variables for cell by cell flow are total number of layers and 
    the type of flow budget to export
    '''
    def __init__(self,layer,precision,xdim,ydim,origin,filename,outpath,totalLayers,type='hds'):
        self.layer=layer
        self.totalLayers=totalLayers
        self.precision=precision.lower()
        self.xdim=xdim
        self.ydim=ydim
        self.origin=origin
        self.filename=filename
        self.outpath=outpath
        self.fvis=''
        self.nPer=0
        self.nStep=0
        self.outrel=''
        self.relfile=''
        self.col=0
        self.row=0
        self.iLay=0
        self.bytepos=0
        self.type=type
        self.fobj=''
  
    def BOVheads(self):
        prec=4
        if self.precision=='double':
            prec=8  
        if not os.path.exists(self.outpath):
            print('{} does not exist or cannot be found'.format(self.outpath))
            exit()
        self.outrel=os.path.relpath(self.outpath)
        curdir=os.getcwd()
        os.chdir(self.outrel)
        if not os.path.exists(self.filename):
            print('{} does not exist or cannot be found'.format(self.filename))
            exit()
        self.relfile=os.path.relpath(self.filename)
        os.chdir(curdir)
        f=open(self.filename,'rb')
          
        for i in range(0,self.layer):
            self.bytepos=0
            f.seek(0,2)
            fileend=f.tell()
            f.seek(0)
            self.fvis=open(os.path.join(self.outrel,'bovlayer'+str(self.layer)+'.visit'),'w')
            while self.bytepos<=fileend:
                self.readheader(f)
                self.bytepos=f.tell()
                if self.iLay==self.layer:
                    self.writeBOV()
                self.bytepos=self.row*self.col*prec+f.tell()
                f.seek(self.bytepos)
                if self.bytepos>=fileend:
                    break
            self.fvis.close()
        f.close()
  
    def readheader(self,f):
        self.nStep = struct.unpack('i',f.read(4))[0]
        self.nPer = struct.unpack('i',f.read(4))[0]
        if self.precision=='single':
            perLen = struct.unpack('f',f.read(4))
            StartTime = struct.unpack('f',f.read(4))
        else:
            perLen = struct.unpack('d',f.read(8))
            StartTime = struct.unpack('d',f.read(8))    
        textType = f.read(16)
        self.col = struct.unpack('i',f.read(4))[0]
        self.row = struct.unpack('i',f.read(4))[0]
        self.iLay = struct.unpack('i',f.read(4))[0]

    def readCCF(self):
        '''read binary cell-by-cell file from modflow
        currently only reads non-compact budget file'''
        prec=4
        if self.precision=='double':
            prec=8  
        type=self.type.upper()
        self.outrel=os.path.relpath(self.outpath)
        curdir=os.getcwd()
        os.chdir(self.outrel) 
        self.relfile=os.path.relpath(self.filename)
        os.chdir(curdir)
        f=open(self.filename,'rb')
        nVal=[]
        nbType=[]
        nList=[]
        self.bytepos=0
        f.seek(0,2)
        fileend=f.tell()
        f.seek(0)
        self.fvis=open(os.path.join(self.outrel,self.type.replace(' ','')+'CCF'+str(self.layer)+'.visit'),'w')
        while self.bytepos<=fileend:
            self.bytepos=f.tell()
            if self.bytepos==fileend:
                print 'done'
                return()
            self.nStep = struct.unpack('i',f.read(4))[0]
            self.nPer = struct.unpack('i',f.read(4))[0]
            textType = f.read(16)
            self.col = struct.unpack('i',f.read(4))[0]
            self.row = struct.unpack('i',f.read(4))[0]
            nlCode = struct.unpack('i',f.read(4))
            print textType+' available '
            if nlCode[0] < 0:
                nval = 0
                nbType = struct.unpack('i',f.read(4))
                nbtype=nbType[0]
                if self.precision=='single':
                    ddelt = struct.unpack('f',f.read(4))
                    dpertim = struct.unpack('f',f.read(4))
                    dtottime = struct.unpack('f',f.read(4))
                else:
                    ddelt = struct.unpack('d',f.read(8))
                    dpertim = struct.unpack('d',f.read(8))
                    dtottime = struct.unpack('d',f.read(8))
                if nbType[0] == 5:
                    nVal = struct.unpack('i',f.read(4))
                    nval=nVal[0]
                    if nVal[0] > 1:
                        for J in range(1,nVal[0]):
                            ctmp = f.read(16)
                else:
                    nval =1
                if nbType[0]==5 or nbType[0]==2:
                    nList = struct.unpack('i',f.read(4))
                    nlist=nList[0]
            else:
                nval=0
                nbtype=0
                nlist=0
            if nbtype==0 or nbtype==1: #flow thru faces, storage
                for i in range(0,self.totalLayers):
                    if textType.find(type)>-1 and i+1==self.layer:
                        print 'exporting '+textType
                        self.bytepos=f.tell()  
                        self.writeBOV()
                    f.seek(self.row*self.col*prec,1)
            elif nbtype==2 or nbtype==5: #constant heads, stream, mnw
                if textType.find(type)>-1: # and i+1==layer[layidx]:
                    print 'exporting '+textType+' stress period='+str(nPer[0])
                    currentPos=f.tell()
                    self.bytepos=f.tell()
                    writeBOV()
                    f.seek(self.row*self.col*prec,1)
            elif nbtype==4:
                f.seek(self.row*self.col*self.totalLayers*prec,1)
            else: #recharge nbtype=3
                f.seek(self.row*self.col*4,1) #seek past array of layers for recharge
                if textType.find(type)>-1:
                    print 'exporting '+textType
                    self.bytepos=f.tell()
                    self.writeBOV()
                f.seek(self.row*self.col*prec,1)
        
    def writeBOV(self):
        print 'BOV '+self.type+' layer='+str(self.layer)+' stress period='+str(self.nPer)+' time step='+str(self.nStep)
        outfile=open(os.path.join(self.outrel,self.type+'SP'+str(self.nPer)+'TS'+str(self.nStep)+'Lay'+str(self.layer)+'.bov'),'w')
        self.fvis.write(self.type+'SP'+str(self.nPer)+'TS'+str(self.nStep)+'Lay'+str(self.layer)+'.bov\n')
        outfile.write('TIME: '+str(self.nPer)+'.'+str(self.nStep)+'\n')
        outfile.write('DATA_FILE: '+self.relfile+'\n')
        outfile.write('DATA SIZE: '+str(self.col)+' '+str(self.row)+' 1\n')
        if self.precision=='double':
            outfile.write('DATA_FORMAT: DOUBLE\n')
        else:
            outfile.write('DATA_FORMAT: FLOAT\n')
        outfile.write('VARIABLE: simHeads\n')
        outfile.write('DATA_ENDIAN: LITTLE\n')
        outfile.write('CENTERING: zonal\n')
        outfile.write('BRICK ORIGIN: '+str(self.origin[0])+' '+str(self.origin[1])+' 0.\n')
        outfile.write('BRICK_SIZE: '+str(self.col*self.xdim)+' '+str(self.row*self.ydim)+' 1.\n')
        outfile.write('BYTE_OFFSET: '+str(self.bytepos)+'\n')
        outfile.close()
        