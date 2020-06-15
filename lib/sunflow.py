# ---------------------------------------------------------------------------
#
# SunFlow
# 
# Copyright (c) 2019-2020, AI-Technologies - Rainer Wallwitz
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. 
#
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------------
#
# Path definitions
#
sunFlowChartPath = 'py/pydata/tempdata/sunflowtemp/'      # path, where graph charts are saved
sunFlowFramePath = 'py/pydata/tempdata/sunflowtemp/'      # path, where the result of optimization is saved
sunFlowDataPath  = 'py/pydata/datasets/'                  # path, from where freight tables being loaded

azure = False

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from graphviz import Digraph
import numpy as np
from scipy.optimize import linprog
import pprint as pp
import pandas as pd
import sys
import aitpath

# ----------------------------------------------------------------------------
#
#  Master Data Klasse und Typen
#

cat_entity = 0
cat_supplier = 1
cat_location = 2
cat_material = 3
cat_freight = 4
cat_source = 5
cat_product = 6
cat_node = 7
cat_supplynet = 7
cat_optimization= 8
cat_country= 9
cat_capacity= 10
cat_demand= 11
cat_unknown = -1

def catDescr(cat):
    if cat == cat_supplier: return 'Supplier'
    elif cat == cat_entity: return 'Entity'
    elif cat == cat_location: return 'Location'
    elif cat == cat_material: return 'Material'
    elif cat == cat_freight: return 'Freight'
    elif cat == cat_product: return 'Product'
    elif cat == cat_source: return 'Source'
    elif cat == cat_node: return 'Node'
    elif cat == cat_supplynet: return 'SupplyNet'
    elif cat == cat_optimization: return 'Optimization'
    elif cat == cat_country: return 'Country'
    elif cat == cat_capacity: return 'Capacity'
    elif cat == cat_demand: return 'Demand'
    else: return 'Unknown type'
    
    
def classType(obj):
    if isinstance(obj, _System): return 'System'
    elif isinstance(obj, Supplier): return 'Supplier'
    elif isinstance(obj, Entity): return 'Entity'
    else: return 'Unknown type'
    
prop_supplier = 0
prop_material = 1
prop_varcost = 2
prop_fixcost = 3
prop_capacity = 4
prop_demand = 5
prop_activity = 6
prop_unknown = -1

activity_manufacturing = 0
activity_distribution = 1
activity_sourcing = 2
activity_unknown = -1

# findFreight
# 1.Rückgabewert
find_freight_invalid_input                 = -1
find_freight_invalid_input_for_inheritance = -2
find_freight_no_entry                      = -3
find_freight_no_entry_after_inheritance    = -4
# 2. Rückgabewert
find_freight_no_entry_found = 0
find_freight_inherited      = 1
find_freight_entry          = 2


initSF   = False

sys_user                = '/users/'+aitpath.sysUser()+'/'
sunFlowGraphicsDir      = sunFlowChartPath      # path, where graphics are saved
sunFlowDefaultSheetPath = sunFlowFramePath      # Optimization().save() => path, where Excel result of optimization
sunFlowDefaultDataPath  = sunFlowDataPath       # System().loadFreights() => path, from where freight table being loaded

    
opt_quantities = 'quantities'
opt_cost = 'cost'
opt_iterations = 'iterations'
opt_success = 'success'
opt_status = 'status'
opt_capacities = 'capacities'

def isWindows(): return True if aitpath.operatingSystem()!='darwin' else True
    
def activityDescr(act):
    if act == activity_manufacturing: return 'Production' #'Manufacturing'
    elif act == activity_distribution: return 'Distribution'
    elif act == activity_sourcing: return 'Buying' #'Sourcing'
    else: return 'unknown activity'
    
def isSourcingAct(act): return True if act == activity_sourcing else False
def isManufacturingAct(act): return True if act == activity_manufacturing else False
def isProductionAct(act): return isManufacturingAct(act)
def isDistributionAct(act): return True if act == activity_distribution else False
def isCapacityDecl(obj): return True if isinstance(obj,Capacity) else False  # ist obj eine Capacity Declaration?
def isDemandDecl(obj): return True if isinstance(obj,Demand) else False  # ist obj eine Demand Declaration?
def isInt(obj): return True if isinstance(obj,int) else False
def isFloat(obj): return True if isinstance(obj,float) else False
def isStr(obj): return True if isinstance(obj,str) else False
def isNumeric(obj): return True if isInt(obj) or isFloat(obj) else False
def capacityValue(capa): return capa.value() if isCapacityDecl(capa) else capa
def demandValue(demand): return demand.value() if isDemandDecl(demand) else demand
def isCapacityEq(c1,c2):
    #
    # 2 capas sind dann gleich, wenn sie in Namen und Wert übereinstimmen
    #
    if c1==None or c2==None: return False
    c1_is_decl = isCapacityDecl(c1)
    c2_is_decl = isCapacityDecl(c2)
    c1_is_num = isNumeric(c1)
    c2_is_num = isNumeric(c2)
    if (c1_is_num and not c2_is_num) or (c2_is_num and not c1_is_num) : return False
    if (c1_is_decl and not c2_is_decl) or (c2_is_decl and not c1_is_decl) : return False
    if c1_is_num:
        return True if c1==c2 else False
    else:
        eq_value = True if c1.value()==c2.value() else False
        eq_name = True if c1.name()==c2.name() else False
        return True if eq_value and eq_name else False  

def showMatList(text,matlist):
    s = text
    for mat in matlist: s += '{} '.format(mat.name())
    print(s)
    
def createTensor(nLines,nCols=0):
    # Matrix        nxm ==> createTensor(n,m)
    # Spaltenvektor nx1 ==> createTensor(n,1)
    # Zeilenvektor  1xn ==> createTensor(n)
    nLines = int(nLines); nCols = int(nCols)
    return np.ones(nLines)*0 if nCols == 0 else np.ones((nLines,nCols))*0

def isInt(s)   : return True if isinstance(s,int) or isinstance(s,np.int64) else False
def isFloat(s) : return True if isinstance(s,float) or isinstance(s,np.float64) else False
def isNum(s)   : return True if isInt(s) or isFloat(s) else False

# ========================================================
# Ab hier Klassen mit globalen Variablen
# ========================================================

bShowInits = False

# ---------------------------------------------------------
# Net -Var
# ---------------------------------------------------------
class CurrentNet:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self.name())  
    def show(self): print('{}'.format(self.name())); return self
    
    def __init__(self ):  
        self._name = 'CurrentNet'
        self._currentNet = None
        if bShowInits: print('**********init:',self.name())
        
    def name(self): return self._name
        
    def net(self,net=None): 
        if net != None: 
            self._currentNet = net
            return net
        return self._currentNet
       

_currentNet = CurrentNet()

# ---------------------------------------------------------
# Vergabe von eineindeutigen Nummern pro erzeugte Entity
# ---------------------------------------------------------
class Idents:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self.name())  
    def show(self): print('{}'.format(self.name())); return self
    
    def __init__(self ):  
        self._name = 'Idents'
        self._entityId = 0
        if bShowInits: print('**********init:',self.name())
        
    def name(self): return self._name
        
    def newEntity(self): 
        newId = self._entityId
        self._entityId += 1
        return newId

_idents = Idents()

# ---------------------------------------------------------
# Database aller Entities => alle Objekte, die sich von Entity ableiten
# ---------------------------------------------------------
#
class Entities:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self): 
        print('{}'.format(self.name())) 
        for entity in self._entities:
            print('  [{:3}] {:10}  {}'.format(entity.ident(),entity.catName(),entity.name()))
        return self
    
    def __init__(self ):  
        self._name = 'Entities'
        self._entities = []
        if bShowInits: print('**********init:',self.name())
        
    def name(self): return self._name
    def add(self,obj): self._entities.append(obj)
    def entity(self,ident): # liefert das Entity-Object über dessen Index (=Ident)
        return self._entities[ident] if ident >= 0 and ident <= len(self._entities) else -1
    def entities(self): return self._entities
    
_enty = Entities()

# ---------------------------------------------------------
# Database aller Substitutes => alle Objekte von Typ Entity, die im Reasoning-Process 
# als identisch angesehen werden sollen, aber unterschiedliche Werte haben
# ---------------------------------------------------------
#
class Substitutes:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self): 
        print('{}'.format(self.name())) 
        for i,tuple in enumerate(self._substitutes):
            lOrig = 'sub' if tuple[0].isSubstitute() else 'orig'
            rOrig = 'sub' if tuple[1].isSubstitute() else 'orig'
            print('  [{:3}] {:4}: {:10} = {:4}: {:10}'.format(i,lOrig,tuple[0].name(),rOrig,tuple[1].name()))
        return self
    
    def __init__(self ):  
        self._name = 'Substitutes'
        self._substitutes = []
        if bShowInits: print('**********init:',self.name())
        
    def name(self): return self._name
    def add(self,entity1,entity2): self._substitutes.append((entity1,entity2))
    def substitutes(self): return self._substitutes
    
    def identical(self,entity1,entity2=None):
        if entity2 == None:
            if type(entity1) is tuple: 
                inside = True if entity1 in self._substitutes else False
                return True if inside else (entity1[1],entity1[0]) in self._substitutes
        else:
            if isinstance(entity1,Entity) and isinstance(entity2,Entity):
                return ((entity1,entity2) in self._substitutes) or ((entity2,entity1) in self._substitutes)
        return False
    
_substitutes = Substitutes()


# ---------------------------------------------------------
# SunFlow Initialisierung
#
# Muss die letzte globale Klasse / Variable sein !!!!!!!!
# ---------------------------------------------------------
#
def version(): return "SunFlow  1.03 / 14.6.20   Copyright (c) AI-Technologies"

class _System:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self.name())  
    def show(self,details=False): 
        print('{}'.format(self.name())); 
        self.entities().show()
        if details:
            for entity in self.entities().entities(): entity.show()
        
        return self
    
    def __init__(self ):  
        self._name = 'SunFlow'
        self._currentNet = None
        self._entities = _enty
        self._substitutes = _substitutes
        self._idents = _idents
        self._currentNet = _currentNet
        self._useFreightInheritance = True
        
        self._userDir  = sys_user
        self._chartDir = sunFlowGraphicsDir
        self._frameDir = sunFlowDefaultSheetPath
        self._dataDir  = sunFlowDefaultDataPath

        if bShowInits: print('**********init:',self.name())
        
    def name(self): return self._name
    def entities(self): return self._entities
    def useFreightInheritance(self): return self._useFreightInheritance
    
    def userDir(self, directory=''): 
        if directory=='': return self._userDir
        self._userDir = directory
        return self
    def chartDir(self, directory=''): 
        if directory=='': return self._chartDir
        self._chartDir = directory
        return self
    def frameDir(self, directory=''): 
        if directory=='': return self._frameDir
        self._frameDir = directory
        return self
    def dataDir(self, directory=''): 
        if directory=='': return self._dataDir
        self._dataDir = directory
        return self
    
    def buildPath(self, filename='', path='', kind='chart'):
        if kind=='chart': dir_path = self.chartDir()
        elif kind=='frame': dir_path = self.frameDir()
        else:
            dir_path = self.dataDir()
        dir_path = dir_path if path=='' else path
        return self.userDir()+dir_path+filename
  
    #
    # Liefert ein Entity-Objekt (den ersten Eintrag in der Entity-Tabelle), 
    # das als Pointer für alle Entity-basierten Methoden dienen kann
    #
    def entity(self): 
        entities = self.entities().entities()
        return entities[0]
    
    def find(self,country=None,material=None,location=None):
        entys = self.entities().entities()
        cat = cat_unknown
        name = ''
        if country != None: 
            cat = cat_country
            name = country
        elif material != None: 
            cat = cat_material
            name = material
        elif location != None:
            cat = cat_location
            name = location
        else:
            return None
        for i,item in enumerate(entys):
            #item.show()
            if item.cat() == cat:
                if item.name() == name: return item 
        return None
    
    def country(self,name): return self.find(country=name)
    def material(self,name): return self.find(material=name)
    def location(self,name): return self.find(location=name)
    
    def init(self):
        #
        # can be used for initialization
        #
        return self
    
    def loadFreights(self, filename='', path='', execute=True):
        index_name = 'from'
        def locationExists(locname): 
            return True if System.location(locname)!=None else False
        def column2Index(df, name=index_name): 
            # turns a column into an index column
            df.set_index(name, inplace=True)
            df.rename_axis(None, inplace=True)
        def loadFile(filename='', path=''): 
            fpath = (path if path!='' else self.userDir()+self.dataDir())+filename
            return pd.read_excel(fpath,keep_default_na=False) if filename!='' else 0
           
        frm = loadFile(filename,path)
        if isinstance(frm,pd.DataFrame):
            from_locs = list(frm[index_name])
            column2Index(frm,index_name) # from_locs need to be loaded before this call !!
            to_locs = list(frm.columns.values)
            #
            # register Locations and Freight
            #
            for toloc in to_locs:
                if not locationExists(toloc): Location(toloc)
                for fromloc in from_locs:
                    if not locationExists(fromloc): Location(fromloc)
                    rel = frm[toloc][fromloc]
                    if isNum(rel): Freight(fromloc,toloc,rel)
        return frm
 
    
System = _System()

# ========================================================
# bis hierhin Klassen mit globalen Variablen
# ========================================================
# 
# ---------------------------------------------------------
# Verwaltung aller Node -> Node Links
# ---------------------------------------------------------
#
class NodeLinks:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self.name())  
    def show(self): 
        print('\n{}'.format(self.name())); 
        for i,link in enumerate(self._links): 
            freight_find_result = link[0].findFreight(link[0],link[1]); #print('**** freight=',freight[0],freight[1],type(freight[0]))
            f = freight_find_result[0].price() if freight_find_result[1]==find_freight_entry else -1
            fromLocName = link[0].source().supplier().location().name()
            toLocName = link[1].source().supplier().location().name()
            if f != -1:
                print('  variable [{:3}] = ({},{})  |  {} => {}   {} -> {} @ {} €/t'.
                  format(i,link[0].name(),link[1].name(),link[0].name(),link[1].name(),fromLocName,toLocName,f))
            else:
                print('  variable [{:3}] = ({},{})  |  {} => {}   {} -> {} '.
                  format(i,link[0].name(),link[1].name(),link[0].name(),link[1].name(),fromLocName,toLocName))
        return self
    
    def __init__(self ):  
        self._name = 'NodeLinks'
        self._iterCount = 0 # für den Iterator
        self._links = []    # für den Iterator
    
    def __iter__(self): return self  # für den Iterator
    def __next__(self):              # für den Iterator
        n = len(self._links)
        if self._iterCount >= n: 
            self._iterCount = 0      # counter zurücksetzen
            raise StopIteration
        count = self._iterCount
        self._iterCount += 1
        #
        #  Iteratorrückgabe:    Link:  n1 -> n2    n1=von    n2=nach   Typ(n1)=Node
        #                       l[0]=n1 (from)
        #                       l[1]=n2 (to)
        #
        return self._links[count] 
     
    def name(self): return self._name
    def add(self, fromNode, toNode):
        if fromNode != toNode:
            if fromNode.cat() == toNode.cat() and fromNode.cat() == cat_node:  # nur Objekte vom Typ Node können 'gelinkt' werden
                newLink = (fromNode,toNode)
                if not newLink in self._links: self._links.append(newLink)     # keine doppelten Einträge
        return self
    
    def index(self,fromNode,toNode): # liefert den Index eines Links=(fromNode,toNode) oder -1, wenn dieser nicht in der Liste ist
        link = (fromNode,toNode)
        return self._links.index(link) if link in self._links else -1
    
    def count(self): return len(self._links) # Anzahl der Links

# ----------------------------------------------------------------------------

# -----------------------------------------------
# Entity
# -----------------------------------------------

class Entity:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self): print('{}'.format(self.name())); return self
    
    def __init__(self, name='e#' ):  
        self._name = name 
        self._cat = cat_entity
        self._ident = _idents.newEntity() # eindeutige Ident erzeugen
        _enty.add(self)                   # Entity in Entities-DB ablegen
        self._system = System
        
    def ident(self): return self._ident # liefert die Ident-Nummer
    def entities(self): return _enty    # liefert die Entity - Database
    def getSubstitutes(self): return _substitutes
    def system(self): return self._system
       
    def name(self,name=None): 
        if name == None: return self._name
        self._name = name
        return self
    
    def cat(self, cat=None): 
        if cat == None: return self._cat
        self._cat = cat
        return self
    
    def catName(self): return catDescr(self._cat)
    
     # -------- Eintrag via Namen und category finden
        
    def findObj(self, name, cat=cat_unknown):
        found = []
        entys = self.entities().entities()
        for i,item in enumerate(entys):
            cat_match = True if cat==cat_unknown else (True if item.cat()==cat else False)
            if cat_match and item.name() == name: found.append( item )
        return found
    
    # -------- Country oriented functions
    
    def findCountry(self, countryName):
        entys = self.entities().entities()
        for i,item in enumerate(entys):
            if item.cat() == cat_country:
                if item.name() == countryName: return item 
        return None
    
    # ------- Location und Freight orientierte Methoden
    
    #
    # Input: Die Location wird aus dem String-Namen ermittelt.
    #        Wenn es mehrere Locations mit gleichem Namen gibt, wird die zuerst gefundene zurückgeliefert
    #
    # Return: a) das Objekt vom Typ Location
    #         b) None, falls kein Eintrag gefunden wurde 
    #
    def findLocation(self, locName):
        entys = self.entities().entities()
        for i,item in enumerate(entys):
            if item.cat() == cat_location:
                if item.name() == locName: return item 
        return None
     
    #
    # liefert die Frachtrate (=price) zwischen 2 Locations zurück
    #
    # Input:   zwei Objekte vom Ty a) String
    #                              b) Location
    #                              c) Supplier
    #                              d) Node
    #
    # return: a) Freight Object:  nicht der price() => price = freight.price()
    #         b) find_freight_invalid_input (-1)
    #         c) find_freight_invalid_input_for_inheritance (-2)
    #         d) find_freight_no_entry (-3):                       falls kein passender Eintrag gefunden wurde
    #         e) find_freight_no_entry_after_inheritance (-4):     falls kein passender Eintrag nach Inheritance gefunden wurde
    #
    
    def findFreight(self,fromInst,toInst):
        
        def findFreightNoInheritance(fromInst,toInst):
            if isinstance(fromInst,str) and isinstance(toInst,str):
                fromLoc = self.findLocation(fromInst)
                if fromLoc != None:
                    toLoc = self.findLocation(toInst)
                    if toLoc == None: return -1   
            elif fromInst.cat() == cat_supplier and toInst.cat() == cat_supplier:
                fromLoc = fromInst.location()
                toLoc = toInst.location()
            elif  fromInst.cat() == cat_location and toInst.cat() == cat_location:
                fromLoc = fromInst
                toLoc = toInst
            elif fromInst.cat() == cat_node and toInst.cat() == cat_node:
                fromLoc = fromInst.source().supplier().location()
                toLoc = toInst.source().supplier().location()
            else:
                return -1
            entys = self.entities().entities()
            for i,item in enumerate(entys):
                if item.cat() == cat_freight:
                    if item._fromLoc == fromLoc:
                        if item._toLoc == toLoc: return item
            return -1
        
        #
        # Zugriff auf globale Variable System
        #
        sys = System
    
        if isinstance(fromInst,str) and isinstance(toInst,str):
            fromLoc = fromInst
            toLoc = toInst
        elif fromInst.cat() == cat_supplier and toInst.cat() == cat_supplier:
            fromLoc = fromInst.location()
            toLoc = toInst.location()
        elif  fromInst.cat() == cat_location and toInst.cat() == cat_location:
            fromLoc = fromInst
            toLoc = toInst
        elif fromInst.cat() == cat_node and toInst.cat() == cat_node:
            fromLoc = fromInst.source().supplier().location()
            toLoc = toInst.source().supplier().location()
        else:
            return (find_freight_invalid_input,find_freight_no_entry_found)
        #
        # zunächst prüfen, ob ein konkreter Eintrag für die Kombination fromInst ==> toInst vorliegt
        f = findFreightNoInheritance(fromLoc,toLoc)
        if isinstance(f,Freight): return (f,find_freight_entry )
        
        if not sys.useFreightInheritance(): 
            return (find_freight_no_entry,find_freight_no_entry_found)
        #print('-->inheritance')
    
        #
        # es liegt kein (!!!!) konkreter Eintrag für die Kombination fromInst ==> toInst vor
        # ==> nun nach vererbten Einträgen via Country-Zuordnung suchen
    
        #
        # Umwandlung der Instanzen in Namen der Locations
        if isinstance(fromInst,str) and isinstance(toInst,str):
            pass
        elif fromInst.cat() == cat_supplier and toInst.cat() == cat_supplier:
            fromLoc = fromInst.location().name()
            toLoc = toInst.location().name()
        elif  fromInst.cat() == cat_location and toInst.cat() == cat_location:
            fromLoc = fromInst.name()
            toLoc = toInst.name()
        elif fromInst.cat() == cat_node and toInst.cat() == cat_node:
            fromLoc = fromInst.source().supplier().location().name()
            toLoc = toInst.source().supplier().location().name()
        else:
            return (find_freight_invalid_input_for_inheritance,find_freight_no_entry_found)
        
        cnty_from = sys.location(fromLoc) 
        if cnty_from != None: 
            cnty_from = cnty_from.country()
        else: 
            return (find_freight_invalid_input_for_inheritance,find_freight_no_entry_found)
        cnty_to = sys.location(toLoc); 
        if cnty_to != None: 
            cnty_to=cnty_to.country()
        else: 
            return (find_freight_invalid_input_for_inheritance,find_freight_no_entry_found)
        #print('hier')
        if cnty_from != None and cnty_to != None:
            f = findFreightNoInheritance(cnty_from.name(),cnty_to.name())
            return (f,find_freight_inherited) if isinstance(f,Freight) else (find_freight_no_entry_after_inheritance,find_freight_no_entry_found)
        return (find_freight_invalid_input_for_inheritance,find_freight_no_entry_found)
   
   
    #def updateFreightx(self,fromInst,toInst,newprice):
    #    fromInst.findFreight(fromInst,toInst,instance=True).price(newprice)

# -----------------------------------------------
# Country
# -----------------------------------------------

class Country(Entity):
    #
    # Countries and Taxes are preliminary !!
    #
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self):
        print('\nCountry {}'.format(self.name()))
        return self.showTaxes()
    
    def __init__(self, name='l#' ): 
        super().__init__(name)
        super().cat(cat_country)
        
        self.key_world   = 'world'          # case = case_world
        self.key_country = 'country'        # case = case_country
        self.key_mat     = 'mat'            # case = case_mat
        self.key_countrymat = 'countrymat'  # case = case_countrymat

        self.case_world      = 0
        self.case_country    = 1
        self.case_mat        = 2
        self.case_countrymat = 3
        
        self._importTaxes = {}
        self._exportTaxes = {}
        
        self._exportTax = 0
        self._importTax = 0
   
    def exportTax(self, tax=None, country=None, material=None ):
        if tax != None:
            self._addTax(self._exportTaxes,tax,country,material)
            return self
        if type(country) is str: country = System.country(country) 
        else:
            if country != None and not isinstance(country, Country): print('Error: exportTax(): country "{}" not a country nor a string!'.format(country))
        return self._getTax(self._exportTaxes,country,material)
    
    def importTax(self, tax=None, country=None, material=None ):
        if tax != None:
            self._addTax(self._importTaxes,tax,country,material)
            return self
        if type(country) is str: country = System.country(country) 
        else:
            if country != None and not isinstance(country, Country): print('Error: importTax(): country "{}" not a country nor a string!'.format(country))
        if country != None: print(country.name(),' ==> ',self.name())
        return self._getTax(self._importTaxes,country,material)
    
    # ------------- Tax methods
    
    def showTaxes(self): 
        self._displayTax(self._importTaxes,'Import tax')
        self._displayTax(self._exportTaxes,'Export tax')
        return self
        
    def _displayTax(self,dct,txt,offset=2):
        if dct == {}: return
        ofs = ' '*offset
        print(ofs+txt)
        w_tax =  dct.get( self.key_world,-1 )
        if w_tax != -1:
            print(ofs+'  worldwide   :  {:4.1f} %'.format(w_tax*100))
    
        countries = dct.get(self.key_country,{}) 
        if len(countries)>0:
            print(ofs+'  by country')
            for cnty in countries.items():
                s = ofs+'    {:10}:  {:4.1f} %'.format(cnty[0].name(),cnty[1]*100)
                print(s)
    
        materials = dct.get(self.key_mat,{})
        if len(materials)>0:
            print(ofs+'  by material')
            for mat in materials.items():
                s = ofs+'    {:10}:  {:4.1f} %'.format(mat[0].name(),mat[1]*100)
                print(s)
        
        countrymats = dct.get(self.key_countrymat,{}) 
        if len(countrymats)>0:
            print(ofs+'  by country & material')
            for cnty in countrymats.items():
                cnty_items = countrymats[cnty[0]]
                for mat in cnty_items.items():
                    s = ofs+'    {:10}:  {:4.1f} %   {}'.format(cnty[0].name(),mat[1]*100,mat[0].name())
                    print(s)

    def _classifyTaxRequest(self,country=None,material=None):
        if country == None: return self.case_world   if material==None else self.case_mat
        else:               return self.case_country if material==None else self.case_countrymat
    
    def _addTax(self,tax_dict,tax,country=None,material=None):
        case = self._classifyTaxRequest(country,material)
        if case == self.case_world:
            tax_dict.update( {self.key_world:tax} )              # erste Ebene nach key_world lesen + updaten
        elif case == self.case_country: 
            countries = tax_dict.get(self.key_country,{})        # erste Ebene nach key_country lesen
            countries.update( {country:tax})                # zweite Ebene nach Land lesen + updaten
            tax_dict.update( {self.key_country:countries} )      # erste Ebene nach key_country updaten
        elif case == self.case_mat:
            materials = tax_dict.get(self.key_mat,{})            # erste Ebene nach key_mat lesen
            materials.update( {material:tax})               # zweite Ebene nach mat lesen + updaten
            tax_dict.update( {self.key_mat:materials} )          # erste Ebene nach key_mat updaten
        elif case == self.case_countrymat:
            countrymats = tax_dict.get(self.key_countrymat,{})   # erste Ebene nach key_countrymat lesen
            country_item = countrymats.get(country,{})      # zweite Ebene nach Land lesen
            country_item.update( {material:tax})            # dritte Ebene nach material updaten
            countrymats.update( {country:country_item} )    # zweite Ebene nach Land updaten
            tax_dict.update( {self.key_countrymat:countrymats} ) # erste Ebene nach countrymat updaten
        else:
            print('error')
        return
   
    def _getTax(self,tax_dict,country=None,material=None):
        tax = -1
        case = self._classifyTaxRequest(country,material)
        if case == self.case_world:
            return tax_dict.get( self.key_world,0 )              # erste Ebene nach key_world lesen 
        elif case == self.case_country: 
            countries = tax_dict.get(self.key_country,{})        # erste Ebene nach key_country lesen
            #print('case by cnty: from cnty=',country.name())
            tax = countries.get(country,-1)
            return tax if tax != -1 else self._getTax(tax_dict)
            #else: return tax
            #return countries.get(country,0)
        elif case == self.case_mat:
            materials = tax_dict.get(self.key_mat,{})            # erste Ebene nach key_mat lesen
            tax = materials.get(material,-1)
            return tax if tax != -1 else self._getTax(tax_dict)
            #return materials.get(material,0)
        elif case == self.case_countrymat:
            countrymats = tax_dict.get(self.key_countrymat,{})   # erste Ebene nach key_countrymat lesen
            country_item = countrymats.get(country,{})      # zweite Ebene nach Land lesen
            tax = country_item.get(material,-1)
            return tax if tax != -1 else self._getTax(tax_dict)
            #return country_item.get(material,0)
        else: 
            return 0
    
    
    

        
# -----------------------------------------------
# Location
# -----------------------------------------------

class Location(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self): 
        cnty = '' if self.country() == None else ' in {}'.format(self.country().name())
        print('{}{}'.format(self.name(),cnty)); return self
    
    def __init__(self, name='l#', country=None ): 
        loc = self.findLocation(name)
        if loc != None:
            print('*** Warning: location "{}" in "{}" already existing ==> use sun.location("{}") instead !!'.format(loc.name(),loc.country().name(),loc.name()))
        super().__init__(name)
        super().cat(cat_location)
        if country != None:
            self.country(country)
        else:
            self._country = None
        
    def country(self,country=None):
        if country != None:
            if type(country) is str:
                cnty = self.findCountry(country)
                country = Country(country) if cnty == None else cnty
            self._country = country
            return self
        return self._country

# -----------------------------------------------
# Freight
# -----------------------------------------------   

class Freight(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self): 
        print('{}  {} => {} @ {} €/t'.format(self.name(),self._fromLoc.name(),self._toLoc.name(),self._price))
        return self
    
    def __init__(self, fromLoc=None, toLoc=None, price=0 ):  
        #
        # erst Prüfung, ob es ein namensgleiches Objekt schon gibt
        # erst dann die Init der Superclass, da das neu zu erzeugende Objekt sonst ebenfalls gefunden würde!!!
        #
        if fromLoc != None and toLoc != None:
            (f,inheritance) = self.findFreight( fromLoc, toLoc)
            if isinstance(f,Freight) and not (inheritance == find_freight_inherited): 
                print('*** Warning: freight {} => {} already existing: {} €/t ==> double entry !!'.format(fromLoc,toLoc,f.price()))
        name = 'f#'
        super().__init__(name)
        super().cat(cat_freight)
        # get location by name or Location-Object
        self._fromLoc = self._getLocByType(fromLoc)
        self._toLoc = self._getLocByType(toLoc)
        self._price = price
        # reset name now
        if self._fromLoc != None and self._toLoc != None:
            self.name('{} => {}'.format(self._fromLoc.name(),self._toLoc.name()))
        
    def _getLocByType(self,name_or_loc):
        location = None
        if type(name_or_loc) is str:
            loc = self.system().location(name_or_loc)
            if loc != None: location = loc
            else: 
                print('Error: location {} unknown!'.format(name_or_loc))
        else:
            if isinstance(name_or_loc,Location): location = name_or_loc
            else:
                print('Error: object {} not of type Location!'.format(name_or_loc.name()))
        return location
        
    def price(self,price=None):
        if price != None:
            self._price = price
            return self
        return self._price
    
    def relation(self,fromLoc=None,toLoc=None): 
        if fromLoc != None and toLoc != None:
            self._fromLoc = fromLoc
            self._toLoc = toLoc
            return self
        return (self._fromLoc,self._toLoc)
    
    def priceRelation(self,fromLoc,toLoc):
        if fromLoc == self._fromLoc and toLoc == self._toLoc: return self.price()
        return -1
    
# -----------------------------------------------
# Capacity
# -----------------------------------------------
#
# die Kapa wird hier als Zahl gespeichert
#
class Capacity(Entity):
    def __str__(self): return "<Class '{}'|{} = {}> id={}".format(self.__class__.__name__,self._name,self._capacity,id(self))  
    def show(self): 
        print('{} = {}'.format(self.name(),self.value())); return self
    
    def __init__(self, name='c#', capacity=-1 ): 
        need_name = False
        if isCapacityDecl(name): # anstelle eines Namens wurde ein Capacity-Objekt übergeben
            capacity = name
            name = 'c#'
            need_name = True
        else:
            if isNumeric(name):
                capacity = name
                name = 'c#'
                need_name = True
                
        # Initialisierung durchführen
        super().__init__(name)
        super().cat(cat_capacity)
        if need_name: self.name('capa{}'.format(self.ident())) # Namen neu setzen
        self._capacity = capacityValue(capacity) if isCapacityDecl(capacity) else capacity
        
    def value(self,capacity=None): # hier ist self._capacity eine Zahl oder None !!!
        if capacity != None: 
            self._capacity = capacity 
            return self
        return self._capacity
      
class CompoundCapacity(Capacity): pass


# -----------------------------------------------
# Demand
# -----------------------------------------------
#
# die Demand wird hier als Zahl gespeichert
#
class Demand(Entity):
    def __str__(self): return "<Class '{}'|{} = {}> id={}".format(self.__class__.__name__,self._name,self._demand,id(self))  
    def show(self): 
        print('{} = {}'.format(self.name(),self.value())); return self
    
    def __init__(self, name='c#', demand=-1 ): 
        need_name = False
        if isDemandDecl(name): # anstelle eines Namens wurde ein Capacity-Objekt übergeben
            demand = name
            name = 'd#'
            need_name = True
        else:
            if isNumeric(name):
                demand = name
                name = 'd#'
                need_name = True
                
        # Initialisierung durchführen
        super().__init__(name)
        super().cat(cat_demand)
        if need_name: self.name('demand{}'.format(self.ident())) # Namen neu setzen
        self._demand = demandValue(demand) if isDemandDecl(demand) else demand
        
    def value(self,demand=None): # hier ist self._demand eine Zahl oder None !!!
        if demand != None: 
            self._demand = demand 
            return self
        return self._demand

# -----------------------------------------------
# Material
# -----------------------------------------------

class Material(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self): print('{}'.format(self.name())); return self
    
    #def __init__(self, name='m#' ):  
    def __init__(self, name=None ):  
        super().__init__(name if name!=None else 'm#')
        super().cat(cat_material)
        if name==None: self.name('m{}'.format(self.ident()))
        self.isSubstitute_ = False
        self._substitutes = []
        self._node = None
      
    def isSubstitute(self): return self.isSubstitute_
    def isIdentical(self,mat): return True if mat == self else self.getSubstitutes().identical(self,mat)
    
    def substituting(self,substitutingMat): 
        #  self           : das Substitut für das Material substitutingMat
        #  substitutingMat: das Original
        self.getSubstitutes().add(self,substitutingMat)
        self.isSubstitute_ = True
        return self
    def substituteOf(self,substitutingMat): return self.substituting(substitutingMat)
    
    def original(self):
        # liefert das Material, zu dem self ein Substitut ist oder self, falls self kein Substitut ist
        if self.isSubstitute():
            subs = self.getSubstitutes().substitutes()
            for sub_orig_tuple in subs:
                if sub_orig_tuple[0] == self: return sub_orig_tuple[1]
        return self
    
    # --------------------------------------------
    #
    # Methoden von SupplyNet werden mittels _currentNet.net() auf die Objekte vom Typ Material abgebildet
    #
    def raw(self,title=None):
        if _currentNet.net() != None: 
            return _currentNet.net().raw(self).title(title) if title != None else _currentNet.net().raw(self)
        print('\n   Error: material.raw() does not have a valid net() assignment!\n')
        return None
    
    def distribution(self,*bkwrdNodes): 
        if _currentNet.net() != None: return _currentNet.net().distribution(*bkwrdNodes)
        print('\n   Error: product.warehouse(): node.net() does not have a valid net() assignment!\n')
        return None
    
    def warehouse(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
    def manufacturing(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
        
        
        
# -----------------------------------------------
# Product
# -----------------------------------------------

class Product(Material):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    
    def show(self,offset=''):
        print('{}{}'.format(offset,self.name()))
        s = offset+'  '
        for mat,qnty in self._recipe.items(): print(s,mat.name(),qnty)
        return self

    def __init__(self, name='l#' ):  
        super().__init__(name)
        super().cat(cat_product)
        self._recipe = {}
        
    def raw(self):
        print('not allowed for Products')
        return _currentNet.net()
        
    def ingr(self,mat,qnty): return self.ingredient(mat,qnty)
    def ingredient(self,mat,qnty): 
        # falls mat ein Substitut ist, wird immer das Original benutzt
        self._recipe.update({mat.original():qnty}); return self
    def has(self,mat): return True if mat in self._recipe else False
    
    def quantity(self,mat): 
        if self.has(mat):
            return self._recipe[mat]
        return -1
    
    def recipe(self): return self._recipe.items()      # Liste der Mat:value Kombinationen
    def ingredients(self): return self._recipe.keys()  # die Liste der Materialien
    def quantities(self): return self._recipe.values()  # die Liste der Mengen der Materialien
    def isIngredient(self,mat):
        # Return : True, True => ist ein Ingredient UND ist ein Substitute
        ings = self.ingredients()
        if mat in ings: return True,False  # mat ist Teil der Rezeptur
        for ing_mat in ings:
            if mat.isIdentical(ing_mat): return True,True  # mat ist ein Substitut zu Materialien der Rezeptur
        return False,False
   
    # --------------------------------------------
    #
    # Methoden von SupplyNet werden mittels _currentNet.net() auf die Objekte vom Typ Product abgebildet
    #
    def production(self,*bkwrdNodes): 
        if _currentNet.net() != None: return _currentNet.net()._manuf_production(Supplier(),self,*bkwrdNodes)
        """
        # so würde es auch gehen!!!!
        for node in bkwrdNodes: 
            if node.cat() == cat_node: return _currentNet.net()._manuf_production(Supplier(),self,*bkwrdNodes)
        """
        print('\n   Error: product.production(): node.net() does not have a valid net() assignment!\n')
        return None
    #
    # synonyms to production
    #
    def blend(self,*bkwrdNodes):        return self.production(*bkwrdNodes)
    def mill(self,*bkwrdNodes):         return self.production(*bkwrdNodes)
    def produce_with(self,*bkwrdNodes): return self.production(*bkwrdNodes)
    
    # -------------------------------------------
   
    def ingredientsWithSubstitutes(self, matList=[], show=False):
        def showIngs(_ings,_pings):
            print('\nIngredients of product "{}" with Substitutes:'.format(self.name()))
            for ing_mat in _ings:
                substitutes = _pings[ing_mat]
                s = '  ingredient: {}: ['.format(ing_mat.name())
                for sub_mat in substitutes: 
                    s += '{}  '.format(sub_mat.name())
                s += ']'
                print(s)
            print()
            
        def deleteListByValue(lst,val):
            def indexBounded(lst,val): return lst.index(val) if val in lst else None
            def deleteListByIndex(lst,index):
                if lst != [] and len(lst) > index: del lst[index]      
            index = indexBounded(lst,val)
            if index != None:
                deleteListByIndex(lst,index)
    
        substitutes = self.getSubstitutes().substitutes()
        ingredients = self.ingredients()
        
        # 
        # basierend auf MasterData wird nun das Dict zusammengestellt, das pro ingredient alle Materialien enthält,
        # die entweder in der Recipe enthalten sind oder als Substitute von diesen in den MasterData definiert wurden.
        #
        
        productIngsWithSubsMaster = {} # basierend auf MasterData
        productIngsWithSubsMasterQnty = {}
        for ing_mat in ingredients:
            productIngsWithSubsMaster.update({ing_mat:[ing_mat]}) # init Liste mit ingredient-Material
            productIngsWithSubsMasterQnty.update({ing_mat:[self.quantity(ing_mat)]})
    
        for ing_mat in ingredients:
            for sub_mat in substitutes: 
                smat = sub_mat[0]                     # erstes Element des Tupels, weil
                identical = smat.isIdentical(ing_mat) # isIdentical() ist symmetrisch bzgl. der Reihenfolge im Tupel
                if identical:
                    ing_subs = productIngsWithSubsMaster[ing_mat]
                    if not smat in ing_subs:
                        ing_subs.append(smat)
                        productIngsWithSubsMaster.update({ing_mat:ing_subs})
        
        # show based on MasterData
        if show: showIngs(ingredients,productIngsWithSubsMaster) 
        productIngsWithSubs = productIngsWithSubsMaster
        
        if matList != []:
            
            # limit productIngsWithSubsMaster based on matList, 
            # d.h. nur solche von MasterData abgeleiteten Entries sollen erhalten bleiben,
            # die auch in der matList enthalten sind.
            # Dazu wird das dict productIngsWithSubsAct aufgebaut
    
            #showMatList('matList = ',matList)
            productIngsWithSubsAct = {} # basierend auf MasterData und der matList ==> ist eine UND-Verknüpfung von beiden
            for ing_mat in ingredients:
                productIngsWithSubsAct.update({ing_mat:[]}) # init
  
            for ing_mat in productIngsWithSubsMaster:
                ings_subs = productIngsWithSubsMaster[ing_mat]
                for mat in ings_subs:
                    if mat in matList: 
                        ing_subs_act = productIngsWithSubsAct[ing_mat]
                        ing_subs_act.append(mat)
                        productIngsWithSubsAct.update({ing_mat:ing_subs_act})
                        
            if show: showIngs(ingredients,productIngsWithSubsAct)
            productIngsWithSubs = productIngsWithSubsAct
            
        #
        # Anzahl der Einträge des Dict = Anzahl der Ingredients: 
        #                                Beispiel:  dict = { r1 : [r1,r7,r8],
        #                                                    r2 : [r2]}
        #
        #                                                   Ing r1 hat die Substitute r7 und r8
        #                                                   Ing r2 hat keine Substitute
        # 
        # Jeder dict-Eintrag (Liste) enthält mindestens einen Eintrag: das Material des Ingredients
        #
        return productIngsWithSubs,productIngsWithSubsMasterQnty
    
# -----------------------------------------------
# Supplier
# -----------------------------------------------

class Supplier(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self): 
        s = '{} @ {}'.format(self.name(),self.location().name())
        if self.capacity() != None:
            capa = capacityValue(self.capacity())  
            cname = "'{}'".format(self.capacity().name()) if isCapacityDecl(self.capacity()) else ''
            s += ' with capacity {} = {}'.format(cname,capa)
        if self.compoundCapacity() != None:
            capa = capacityValue(self.compoundCapacity())  
            cname = "'{}'".format(self.compoundCapacity().name()) if isCapacityDecl(self.compoundCapacity()) else ''
            s += ' with compound capacity {} = {}'.format(cname,capa)
        print(s); 
        return self
    
    def __init__(self, name='', location=None ):  
        super().__init__(name)
        super().cat(cat_supplier)
        if name == '': # wenn kein Name angegeben, dann wird ident() als Name benutzt
            self.name('s{}'.format(self.ident()))
        self._loc = location if location != None else Location('L.'+self.name())
        self._capacity = None          # das ist ein Capacity-Objekt, keine Zahl!!!
        self._compoundCapacity = None  # ist None oder ein Capacity-Object
        self._demand = None            # das ist ein eine Zahl!
        self._varcost = 0           # das ist ein eine Zahl!
    
    # setter / getter
    def location(self, loc=None):
        if loc == None: return self._loc
        if isinstance(loc, str): loc = Location(loc)
        elif not isinstance(loc,Location): 
            print('Warning: Supplier.location(): not a string nor a Location!')
            loc = Location('L.'+self.name())
        self._loc = loc
        return self
    
    def at(self, loc=None): return self.location(loc)
    
    def capacity(self,capacity=None):
        if capacity != None:
            self._capacity = capacity
            return self
        return self._capacity
        
    def compoundCapacity(self,capacity=None):
        if capacity != None:
            self._compoundCapacity = capacity
            return self
        return self._compoundCapacity
    
    def hasCompoundCapacity(self): return True if self.compoundCapacity()!=None else False 
    
    # 
    # ist nur für 'Customer' relevant   !!!!!!!!!!!!!
    #
    def demand(self,demand=None):
        if demand != None:
            self._demand = demandValue(demand)
            return self
        return self._demand
    
    def varcost(self,vc=None):
        if vc != None:
            self._varcost = vc
            return self
        return self._varcost
        
# -----------------------------------------------
# Customer, Manufacturer,.... = Supplier
# -----------------------------------------------
class Customer(Supplier): pass
class Manufacturer(Supplier): pass
class Producer(Supplier): pass
class Logistics(Supplier): pass
class Distributor(Supplier): pass

# -----------------------------------------------
# Source
# -----------------------------------------------

class Source(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    def show(self,ofs=''): 
        print(ofs+'{}'.format(self.name()))
        print(ofs+'   Supplier = ',self.supplier().name())
        print(ofs+'   Material = ',self.material().name())
        print(ofs+'   Activity = ',activityDescr(self.activity()))
        print(ofs+'   Costs    =  var={}  fix={}'.format(self.varcost(),self.fixcost()))
        print(ofs+'   Capacity = ',capacityValue(self.capacity()) )
        print(ofs+'   Demand   = ',self.demand())
        return self
    
    def __init__(self, name, supplier=None, material=None, varcost=0, fixcost=0, capacity=-1, demand=-1 ):  
        super().__init__(name)
        super().cat(cat_source)
        self._supplier = supplier
        self._material = material
        self._varcost = varcost
        self._fixcost = fixcost
        self._capacity = capacity
        self._demand = demand
        self._activity = activity_unknown
    
    # setter / getter
    def supplier(self, supplier=None): return self._object(prop_supplier, supplier)
    def material(self, material=None): return self._object(prop_material, material)
    def varcost(self, varcost=None): 
        #print('Source:',self.name(),varcost)
        return self._object(prop_varcost, varcost)
    def fixcost(self, fixcost=None): return self._object(prop_fixcost, fixcost)
    def capacity(self, capacity=None): return self._object(prop_capacity, capacity)
    #def compoundCapacity(self, capacity=None): return self._object(prop_compound_capacity, capacity)
    
    def demand(self, demand=None): return self._object(prop_demand, demand)
    def activity(self, activity=None): return self._object(prop_activity, activity)
    def _object(self, prop=None, obj=None ):
        if prop == prop_supplier:
            if obj == None: return self._supplier
            self._supplier = obj
        elif prop == prop_material:
            if obj == None: return self._material
            self._material = obj
        elif prop == prop_varcost:
            if obj == None: return self._varcost
            self._varcost = obj
        elif prop == prop_fixcost:
            if obj == None: return self._fixcost
            self._fixcost = obj
        elif prop == prop_capacity:
            if obj == None: return self._capacity
            self._capacity = obj
        elif prop == prop_demand:
            if obj == None: return self._demand
            self._demand = obj
        elif prop == prop_activity:
            if obj == None: return self._activity
            self._activity = obj
        return self
    
# ************************************************************************************************************

# -----------------------------------------------
# Node
# -----------------------------------------------

class Node(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    
    def __init__(self, name, backwardObjects=[]):
        super().__init__(name)
        super().cat(cat_node)
        self._source = Source('source.'+name)
        self._title = ''
        self.visitedAlready = False
        self._net = None
        self._forward = []
        self._backward = backwardObjects
        for backwObj in backwardObjects: backwObj._forward.append(self)
     
    def net(self,net=None):
        if net != None: 
            self._net = net
            return self
        return self._net
    
    def backward(self): return self._backward
    def forward(self): return self._forward 
    def isTerminal(self): return True if self._backward == [] else False
    def find(self,searchName):
        if searchName == self.name(): return self
        if  self._backward != []:
            for obj in self._backward:
                obj_found = obj if searchName == obj.name() else obj.find(searchName)
                if obj_found != None: return obj_found
        return None
    
    # setzt visitedAlready auf initial False zurück
    def clearVisitedMarker(self):
        self.visitedAlready = False
        if self._backward != []: 
            for obj in self._backward: obj.clearVisitedMarker()
    #
    # danach mit clearVisitedMarker() die gesetzten Flags löschen
    #
    def collectIntermediatesAndTerminals(self,intermediates,terminals):
        self.visitedAlready = True
        if self._backward != []:
            for obj in self._backward:
                if not (obj.visitedAlready and not obj.isTerminal()):
                    if  obj.isTerminal():
                        if not obj in terminals: terminals.append(obj)
                    else:
                        if not obj in intermediates: intermediates.append(obj)
                    obj.collectIntermediatesAndTerminals(intermediates,terminals)
    
    # ------- show and walk -------
    
    def showObjectArray(self,txt,objects):
        if objects != []:
            s = '  '+txt+'['
            for obj in objects: s += '{} ,'.format(obj.name())
            s = s[:len(s)-2] # letztes Komma und Blank entfernen
            s += ']'
            print(s)    
    def show(self):
        print('Node="{}"'.format(self.name()))
        self.source().show('  ')
        self.showObjectArray('backward=',self._backward)
        self.showObjectArray('forward =',self._forward)
        return self
                
    def walkAllVertices(self):
        if self.backward != []:
            for obj in self._backward:
                print('  {}  {}'.format(obj.name(),obj.visitedAlready))
                obj.walkAllVertices()
        
    def walkAllVerticesOnce(self):
        self.visitedAlready = True
        if self.backward != []:
            for obj in self._backward:
                if not (obj.visitedAlready and not obj.isTerminal()):
                    sIntermediate = 'intermediate' if not obj.isTerminal() else ''
                    print('  {}  {}'.format(obj.name(),sIntermediate))
                    obj.walkAllVerticesOnce()
                    
    def walkIntermediates(self):
        self.visitedAlready = True
        if self._backward != []:
            for obj in self._backward:
                if not (obj.visitedAlready and not obj.isTerminal()):
                    if  not obj.isTerminal():
                        print('  intermediate: {}'.format(obj.name()))
                    obj.walkIntermediates()
     
    # -------  setter / getter ----------
    
    def title(self,title=None): 
        if title != None: 
            self._title = title
            return self
        return self._title
    def n(self,title=None): return self.title(title)
    def p(self,title=None): return self.n(title)
    
    def nameTitle(self): return self.title() if self.title() != '' else self.name()
    def source(self,source=None): 
        if source == None: return self._source
        self._source = source
        return self
    def material(self,material=None):
        if material == None: return self.source().material()
        self.source().material(material)
        return self
    def supplier(self,supplier=None):
        if supplier == None: return self.source().supplier()
        self.source().supplier(supplier)
        return self
    def price(self,price=None): return self.varcost(price)
    def varcost(self,varcost=None):
        if varcost == None: return self.source().varcost()
        #print('Node().varcost(): vc=',varcost); print(self.source())
        self.source().varcost(varcost)
        return self
    def fixcost(self,fixcost=None):
        if fixcost == None: return self.source().fixcost()
        self.source().fixcost(fixcost)
        return self
    
    def capacity(self,capacity=None):
        if capacity == None: return self.source().capacity()
        if isNumeric(capacity):
            capacity = Capacity('capa{}'.format(self.ident()),capacity)
            #print('Node.capacity():create new capa obj=',self.ident())
        #print('   Node().capacity():set capacity=',capacity)
        self.source().capacity(capacity)
        return self
    #
    # convenience Methoden, die via Source (==>source.supplier()) umgesetzt wird
    #
    def compoundCapacity(self): return self.supplier().compoundCapacity()
    def hasCompoundCapacity(self): return  self.supplier().hasCompoundCapacity()
    
    #
    # nur aus convenienace gründen eine Methode von Node()
    #
    def capacityValue(self): return capacityValue(self.source().capacity())
    
    def demand(self,demand=None):
        if demand == None: return self.source().demand()
        #print(self.name(),'  demand=',demand)
        self.source().demand(demand)
        return self
    def activity(self,activity=None):
        if activity == None: return self.source().activity()
        self.source().activity(activity)
        return self
    
    def _transferCapaFromSupplierOrNode(self,supplier): 
        if supplier.capacity() != None: self.capacity(supplier.capacity())
        else:
            if supplier.hasCompoundCapacity() and self.capacity()==-1:
                # 
                # falls keine Kapa definiert ist und der Node mit.capacity(xxx) keine Kapa zugeornet wurde (capa==-1),
                # dann der Node die compoundCapa() des Supplier zuordnen
                #
                self.capacity( supplier.compoundCapacity() )
                #print('nun die compound:',supplier.name(),supplier.capacity())
    #
    # am Ende von by() und to() muss at() aufgerufen werden, da sonst der capacity()-Transfer nicht stattfindet
    #
    def by(self,supplier,loc=None): return self.at(supplier,loc)
    def to(self,supplier,loc=None): return self.at(supplier,loc)
    def at(self,supplier,loc=None):
        if (isinstance(supplier,Producer) or isinstance(supplier,Manufacturer) or isinstance(supplier,Logistics) or isinstance(supplier,Distributor)) and supplier.varcost()>0:
            #
            # retrieve the varcost and assign to node
            #
            self.varcost(supplier.varcost())
        else:
            if isinstance(supplier,Customer) and supplier.demand()!=None and supplier.demand()>0:
                #
                # retrieve the demand and assign to node
                #
                self.demand(supplier.demand())
        
        #    if isinstance(supplier,) 
        if type(supplier) is str: supplier = Supplier(supplier)
        else:
            if not isinstance(supplier,Supplier): 
                if isinstance(supplier,Location):
                    loc = supplier                              # supplier wird als Location interpretiert
                    new_supplier = Supplier('s.'+loc.name())    # neuen Supplier mit s.Location-Name erzeugen
                    self.supplier( new_supplier ).location(loc) # und inkl. location() der Node zuweisen
                return self # falls nicht vom Typ Supplier und nicht vom Typ Location ==> ignorieren
        
        self.supplier(supplier)                                 # supplier der Node setzen
        if loc != None: self.location(loc)                      # Location setzen, falls übergeben
        self._transferCapaFromSupplierOrNode(supplier)                # nun die Kapa vom Supplier übertragen, falls vorhanden
        return self
    
    def location(self,loc=None):
        if loc == None: return self.supplier().location()
        if isinstance(loc,Location): self.supplier().location(loc)
        return self
    
# -----------------------------------------------
# SupplyNet
# -----------------------------------------------

class SupplyNet(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self._name)  
    
    def __init__(self, name=None):
        super().__init__(name)
        super().cat(cat_supplynet)
        self._endNodes = []
        self._intermediates = []
        self._terminals = []
        self._allNodes = []
        self.def_node_name = 'sn'
        self.def_node_name_count = 0
        self._links = NodeLinks()
        
        self._graph = None
        self._graphCount = 0
        self._autoGraph = 0
        
        self._debug = False
        self._display = False
        self._showTitle = True
        self._showNodeDescr = True
        self._showVersion = False
        self._eq = 'eq'
        self._lt = 'lt'
        self._constraints = []       # enthält die gesammelten Constraints Stufe 1
        self._eqnEquals = None       # enthält die Constraints Stufe 2: Gleichungen
        self._eqnUpperLimits = None  # enthält die Constraints Stufe 2: Ungleichungen
        self._A_eq = None            # Stufe 3: A_eq = b_eq => numpy-Format
        self._b_eq = None
        self._A_ub = None            # Stufe 3: A_ub <= b_ub => numpy-Format
        self._b_ub = None
        self._c_var_freight = None   # Frachtkosten
        self._c_var = None           # Kosten aus Rohstoffen, Produktion, Distribution
        self._c_fix = None           # Fixkosten aus Produktion, Distribution
        self._c = None               # Stufe 3: enthält die Kosten: Fracht,var,fix => numpy-Format
        self._capacities = None      # Kapazitäten der Nodes
        
        self._linprogResult = None   # Ergebnis der Optimierung mit linprog()
        self._result = None          # Zusammenfassung des Optimierungsergebnisses
        self._optimized = 0          # wird erst durch eine Optimierung gesetzt
        _currentNet.net(self)
        
        self.checkProductRecipes()   # Prüfung, ob Summe der ingredient Mengen == 1 ergibt
        
        
    def endNodes(self): return self._endNodes
    def terminals(self): return self._terminals
    def intermediates(self): return self._intermediates
    def allNodes(self): return self._allNodes
    def links(self): return self._links
    def debug(self,debug=None): 
        if debug != None: self._debug = debug; return self
        return self._debug
    def display(self,display=None): 
        if display != None: self._display = display; return self
        return self._display
    def title(self, title=None): 
        if title!=None: 
            self._showTitle = title
            return self
        return self._showTitle
    def description(self, descr=None): 
        if descr!=None: 
            self._showNodeDescr = descr
            return self
        return self._showNodeDescr
    def showVersion(self): return self._showVersion
    
    def constraints(self): return self._constraints
    
    def eq(self): return self._eq
    def lt(self): return self._lt
    #"""
    def checkProductRecipes(self):
        for enty in self.entities().entities():
            if enty.cat() == cat_product:
                ing_sum = sum(enty.quantities())
                if ing_sum != 1.0:
                    print('\n***Error: Product {} has unbalanced ingredient quantities sum = {} => should be 1.0 !'.format(enty.name(),ing_sum))
                    enty.show('   ')
    #"""
    
    # ------------ view the net graphical --------------
    
    def graph(self): return self._graph
    
    def graphic(self,auto=True): 
        self._autoGraph = auto
        return self
    
    def showGraph(self,name=None, optimized=False, showOptimizedFlowOnly=False, orient='LR'):
        
        def createNode(node,act,name,matName,supName,capa,vc,fc,dmd,locname,from_ccapa_val,from_ccapa_name,hasFlow=False):
            isEndNode = self._isEndNode(node)
            g = self.graph()
            title = node.title()                                      # falls ein Titel definiert ist,
            topDescription = title if title != '' else matName # wird dieser anstelle des Material-Namens in der 1. Zeile der Node dargestellt
            
            if not self.description(): topDescription = ' '
            
            if isSourcingAct(act):
                if isEndNode:
                    g.raw(name,material=topDescription,supplier=supName,capa=capa,vc=vc,location=locname,hasFlow=hasFlow,ccapa_val=from_ccapa_val,ccapa_name=from_ccapa_name)
                else:
                    g.raw(name,material=topDescription,supplier=supName,capa=capa,vc=vc,demand=dmd,location=locname,hasFlow=hasFlow,ccapa_val=from_ccapa_val,ccapa_name=from_ccapa_name)
            elif isProductionAct(act):
                if isEndNode:
                    g.producer(name,supplier=supName,capa=capa,vc=vc,fc=fc,demand=dmd, material=topDescription,location=locname,hasFlow=hasFlow,ccapa_val=from_ccapa_val,ccapa_name=from_ccapa_name)
                else:
                    g.producer(name,supplier=supName,capa=capa,vc=vc,fc=fc, material=topDescription,location=locname,hasFlow=hasFlow,ccapa_val=from_ccapa_val,ccapa_name=from_ccapa_name)
            elif isDistributionAct(act):
                if isEndNode:
                    g.distributor(name,supplier=supName,vc=vc,fc=fc,demand=dmd, material=topDescription,location=locname,capa=capa,isEndNode=isEndNode,hasFlow=hasFlow,ccapa_val=from_ccapa_val,ccapa_name=from_ccapa_name)
                else:
                    g.distributor(name,supplier=supName,vc=vc,fc=fc, material=topDescription,location=locname,capa=capa,isEndNode=isEndNode,hasFlow=hasFlow,ccapa_val=from_ccapa_val,ccapa_name=from_ccapa_name)
            else:
                print('+++++createGraph: ERROR')
        
        def createAndInitGraph(name, optimized, showOptimizedFlowOnly):
            name = self.name()+'_{}'.format(self._graphCount) if name == None else name
            name += '_opt' if optimized else ''
            name += '_flow' if showOptimizedFlowOnly else ''#'_net'
            g = Graph(name, optimized=optimized, showOptimizedFlowOnly=showOptimizedFlowOnly, rankdir=orient)
            self._graph = g
            self._graphCount += 1
            
            g.fontsize(6,'raw')
            g.fontsize(6,'producer')
            g.fontsize(6,'distributor')
            g.fontsize(6,'descr')
            return g
        
        # ------ NodeList Funktionen
        
        def posInNodeList(lst,node):
            for i,x in enumerate(lst): 
                if x[0] == node: return i
            return -1
        
        def createNodeList(links):
            nodeList = []
            tempList = []
            for i,linkEntry in enumerate(links): 
                fromNode = linkEntry[0]
                toNode = linkEntry[1]
                if not fromNode in tempList: 
                    nodeList.append([fromNode,False] )
                    tempList.append(fromNode)
                if not toNode in tempList: 
                    nodeList.append([toNode,False] )
                    tempList.append(toNode)
            return nodeList
        
        def removeNode(node_list, node):                
            index = posInNodeList(node_list,node)
            if index != -1: del node_list[index]
            return node_list
        
        def isInNodeList(node_list, node):
            index = posInNodeList(node_list,node)
            return True if index!=-1 else False
        
        def showNodeList(node_list):
            print('\nNodeList: {}'.format(len(node_list)))
            for i,entry in enumerate(node_list): print('   [{}]  node={}   hasFlow={}'.format(i,entry[0].title(),entry[1]))
            
        def evalNodeFlow(links,node_list):
            def markNode(node, qnty):
                index = posInNodeList(node_list,node)
                entry = node_list[index]
                if node_list[index][1] == False:
                    if abs(qnty)>0.0001:
                        node_list[index][1] = True

            for i,linkEntry in enumerate(links): 
                fromNode = linkEntry[0]
                toNode = linkEntry[1]
                qnty = quantities[i]
                markNode(fromNode,qnty)
                markNode(toNode,qnty)
        
            return node_list
        
        # --------------
        
        g = createAndInitGraph(name, optimized, showOptimizedFlowOnly)
        
        quantities = self._result[opt_quantities] if self._result != None else []
        links = self.links()
        nodeList = createNodeList(links); #showNodeList(nodeList)
        if optimized:
            nodeList = evalNodeFlow(links,nodeList); #showNodeList(nodeList)
       
        #
        #   read the created Nodes
        #
        for i,linkEntry in enumerate(links): 
            fromNode = linkEntry[0]
            toNode = linkEntry[1]
            varIndex = i
            
            nameFrom = fromNode.name()
            nameTo = toNode.name()
            supNameFrom = fromNode.source().supplier().name()
            supNameTo = toNode.source().supplier().name()
            matNameFrom = fromNode.source().material().name()#; print('matNameFrom=',matNameFrom)
            matNameTo = toNode.source().material().name()#; print('matNameTo=',matNameTo)
            actFrom = fromNode.source().activity()
            actTo = toNode.source().activity()
            actNameFrom = activityDescr(actFrom)
            actNameTo = activityDescr(actTo)
            vcFrom = fromNode.source().varcost()
            vcTo = toNode.source().varcost()
            fcFrom = fromNode.source().fixcost()
            fcTo = toNode.source().fixcost()
            
            capaFrom = capacityValue( fromNode.source().capacity() )
            capaTo = capacityValue( toNode.source().capacity() )
            
            dmdFrom = fromNode.source().demand()
            dmdTo = toNode.source().demand()
            locFrom = fromNode.source().supplier().location().name()
            locTo = toNode.source().supplier().location().name()
            
            fromCompCapa_val = -1
            fromCompCapa_name = ''
            supFrom =  fromNode.source().supplier()
            if isinstance(supFrom,Supplier):  # 2 if, da man die Reihenfolge der Abfrage nicht kennt!
                if supFrom.hasCompoundCapacity():
                    fromCompCapa_val = supFrom.compoundCapacity().value()
                    fromCompCapa_name = supFrom.compoundCapacity().name()
        
            #print('index={}  {}:[{}] capa={} vc={} fc={} dmd={} --> {}:[{}] capa={} vc={} fc={} dmd={}'.format(index,nameFrom,actNameFrom,capaFrom,vcFrom,fcFrom, dmdFrom,
                                               # nameTo,actNameTo,capaTo,vcTo,fcTo,dmdTo))
            matNameF = nameFrom if self._debug else matNameFrom
            matNameT = nameTo if self._debug else matNameTo
        
            #
            # draw the node
            #
            if isInNodeList(nodeList,toNode) or isInNodeList(nodeList,fromNode):
                if isInNodeList(nodeList,toNode):
                    hasFlow = nodeList[posInNodeList(nodeList,toNode)][1] if optimized else False
                    if not hasFlow and showOptimizedFlowOnly:
                        pass
                    else:
                        createNode(toNode,   actTo,  nameTo,  matNameT,   supNameTo,  capaTo,  vcTo,  fcTo,  dmdTo,  locTo,  fromCompCapa_val, fromCompCapa_name, hasFlow=hasFlow)
                    nodeList = removeNode( nodeList, toNode )
                if isInNodeList(nodeList,fromNode):
                    hasFlow = nodeList[posInNodeList(nodeList,fromNode)][1] if optimized else False
                    if not hasFlow and showOptimizedFlowOnly:
                        pass
                    else:
                        createNode(fromNode,actFrom, nameFrom ,matNameF, supNameFrom, capaFrom,vcFrom,fcFrom,dmdFrom,locFrom, fromCompCapa_val, fromCompCapa_name, hasFlow=hasFlow)
                    nodeList = removeNode( nodeList, fromNode )
                
        #
        # link created nodes
        #
        #quantities = self._result[opt_quantities] if self._result != None else []
        for i,linkEntry in enumerate(links):
            fromNode = linkEntry[0]
            toNode = linkEntry[1]
            varIndex = i
            
            nameFrom = fromNode.name()
            nameTo = toNode.name()
            # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            (freight,inheritance) = self.findFreight(fromNode,toNode)
            freight = freight.price() if isinstance(freight,Freight) else 0 #freight # falls Fracht gefunden, dann Objekt vom Typ Freight, sonst -1
                                                                                  # Der Preis muss durch die Methode .price() ermittelt werden
            
            #print('  {} ==> {}   freight price={}   index={}'.format(fromNode.location().name(),toNode.location().name(),freight,varIndex))
            index = links.index(fromNode,toNode)
            #print('  {} ==> {}   price={}   index={}'.format(nameFrom,nameTo,freight,index))
            quantity = quantities[i] if quantities != [] else 0
            quantity = round(quantity, 1)
            g.link(nameFrom,nameTo,quantity=quantity,freight=freight)
            
        #
        # description
        #
        g = self.graph()
        if self._optimized==0: 
            # Darstellung des noch nicht optimierten Flownets
            #
            s = "Topological graph of model"
            s += f"\n' {self.name()} '" + (f" \nby {version()}" if self.showVersion() else '')
            if self.title():
                #print('SupplyNet(1)=',self.title())
                g.description(s,'')
        else:
            # Darstellung nach Optimierung
            #
            optimized =  self._optimized
            successful = optimized._successful
            iterations = optimized._iterations
            costs = optimized._cost
            s = "Optimization of ' {} ' ".format(self.name())
            sSuccess = ' successful !' if successful else ' not successful !!! *** !!!'
            s += sSuccess
            costs = 0 if np.isnan(costs) else costs # sometimes costs are delivered as np.nan
            s += '\nTotal costs: {}T€    Iterations: {} ({})'.format(int(costs/1000.0),iterations,optimized._status)
            s += '\nby {}'.format(version()) if self.showVersion() else ''
            s += '\nOnly nodes with a flow are shown here!' if showOptimizedFlowOnly else ''
            if self.title():
                #print('SupplyNet(2)=',self.title())
                g.description(self.name(),s)
        
        return self
            
    def view(self):
        if self.graph() != None: self.graph().view()
   
    
    
    # ------------ build the net --------------
    
    def getMatListString(self,text,matlist):
            s = text+'[ '
            for mat in matlist: s += '{}, '.format(mat.name())
            return s+' ]'
    
    def raw(self,material): return self.add(Supplier(),material)
    def source(self,material=None): 
        #if material==None:
        material = Material() if material==None else material
        return self.raw(material)
    
    def distribution(self,*bkwrdNodes): return self.add(Supplier(),None,*bkwrdNodes)
    #
    # convenience for distribution()
    #
    def market(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
    def delivery(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
    def deliver(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
    def tankfarm(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
    def warehouse(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
    def store(self,*bkwrdNodes): return self.distribution(*bkwrdNodes)
    def manufacturing(self,*bkwrdNodes): return self.add(Supplier(),None,*bkwrdNodes)
    #
    # synonyms for manufacturing
    #
    def manufactured_with(self,*bkwrdNodes): return self.manufacturing(*bkwrdNodes)
    def produce_with(self,*bkwrdNodes):      return self.manufacturing(*bkwrdNodes)
    def consume(self,*bkwrdNodes):           return self.manufacturing(*bkwrdNodes)
    def blend(self,*bkwrdNodes):             return self.manufacturing(*bkwrdNodes)
    def mill(self,*bkwrdNodes):              return self.manufacturing(*bkwrdNodes)
    def fill(self,*bkwrdNodes):              return self.manufacturing(*bkwrdNodes)
    def assemble(self,*bkwrdNodes):          return self.manufacturing(*bkwrdNodes)
    
    def production(self,product,*bkwrdNodes): return self._manuf_production(Supplier(),product,*bkwrdNodes)
    #
    # convenience for production()
    #
    def blender(self,product,*bkwrdNodes): return self.production(product,*bkwrdNodes)
    def mill(self,product,*bkwrdNodes): return self.production(product,*bkwrdNodes)
    
    def _manuf_production(self,supplier,product,*bkwrdNodes): return self.add(supplier,product,*bkwrdNodes)
        
    def add(self, supplier, material=None, *bkwrdNodes):   #  Node() wird zurückgeliefert
          
        def _add_alltypes(name, *bkwrdNodes):  #  Node() wird zurückgeliefert
            def addList(name, backwardNodes=[] ): # Node() wird zurückgeliefert
                newNode = Node(name, backwardNodes)
                self._allNodes.append(newNode)
                return newNode
            bkwrdNodeList = []
            for node in bkwrdNodes: 
                if not node in  bkwrdNodeList: # ist Node schon in Liste enthalten?  ==> eliminiert Mehrfachangaben
                    bkwrdNodeList.append(node)
            return addList(name,bkwrdNodeList)
        
        def createBackwardMaterialList(*bkwrdNodes):
            bkwrdMatList = []
            for node in bkwrdNodes: 
                if node.cat() != cat_node: return None # Sicherstellen, dass nur Daten vom Typ Node übergeben wurden
                mat = node.material()
                if not mat in bkwrdMatList: # ist Mat schon in Liste enthalten?  ==> eliminiert Mehrfachangaben
                    bkwrdMatList.append(mat)
            return bkwrdMatList
        
        def areMatListEntriesIdentical(mat_list):
            if len(mat_list) == 0: return False,None
            _mat = None
            for mat in mat_list:
                if _mat == None: _mat = mat # init
                else:
                    #print('* gesucht={}  aus liste={}'.format(mat.name(),_mat.name()))
                    mat_orig = mat.original()
                    if not _mat.isIdentical(mat_orig): return False,mat
                    #if not _mat.isIdentical(mat): return False,mat
            
            # das Original Material und nicht ein Substitut wird vererbt
            return True,_mat.original()  # _mat kann Original oder Substitut sein 
        
        def showMatList(text,matlist):
            s = text
            for mat in matlist: s += '{} '.format(mat.name())
            print(s)
            
        def getMatListString(text,matlist):
            s = text+'[ '
            for mat in matlist: s += '{}, '.format(mat.name())
            return s+' ]'
        
        # ------------- lokal code ----------------
        
        activity = activity_unknown
        if bkwrdNodes != ():
            backwrdMatList = createBackwardMaterialList(*bkwrdNodes)
            if backwrdMatList == None:
                print('SupplyNet.add(): inbound data not of type Node!')
                return None
                
            if material != None:    # material=Material/Product und backward Nodes sind gegeben
                
                cat = material.cat()
                #
                # Fall: material = Material ==> ein Material soll hinzugefügt werden
                #
                if cat == cat_material:     
                    # die Materialien aller backwardNodes müssen mit material identisch sein
                   
                    identical,mat = areMatListEntriesIdentical(backwrdMatList)
                    if not identical: 
                        s = getMatListString('',backwrdMatList)
                        print('SupplyNet.add(): {} inbound materials {} are not identical!'.format(mat.name(),s))
                        return None
                    activity = activity_distribution
                #
                # Fall: material = Product ==> ein Produkt mit Rezeptur soll hinzugefügt werden
                #
                elif cat == cat_product: 
                    #print('production von mat=',material.name())
                    # 
                    # Fall: die Inbounds sind alle vom gleichen Product ==> dann keine Rezeptur nötig,
                    #       da von den Vorgängern vererbt wird.
                    #
                    #       Prüfung, ob alle Inbound identisch sind
                    
                    #showMatList('   1)backwardMatList=',backwrdMatList)
                    
                    identical,mat = areMatListEntriesIdentical(backwrdMatList)
                    if identical: # inbounds identisch => dann wird material = mat gefordert
                        #print('+++',mat.name(),material.name())
                        if mat == material: 
                            #print('++++ VERERBUNG: mat=material')
                            pass
                        else:
                            #print('++++ ERROR  mat=material')
                            s = getMatListString('',backwrdMatList)
                            print('SupplyNet.add(): at least one material of recipe of product {} not in inbound list {}'.format(material.name(),s))
                            return None
                        activity = activity_distribution
                    
                    #
                    # Inbounds sind nicht identisch, dann muss es eine Rezeptur geben
                    #
                    else: 
                        #showMatList('   2)backwardMatList=',backwrdMatList)
                        #print('   nicht identical=',identical,' ',mat.name())
                        # 
                        # gibt es eine ingredient-Liste?
                        #
                        if len(material.ingredients()) == 0:
                            s = getMatListString('',backwrdMatList)
                            print('SupplyNet.add(): inbounds {} not identical, but missing recipe for product {}'.format(s,material.name()))
                            material.show()
                            return None
                    
                        # 1) Prüfung, ob alle ingredients der Rezeptur in backwardNode-Materialienenthalten sind
                        #showMatList('   3)ings der Rezeptur=',material.ingredients())
                        
                        backwMatListOfOrigs = []
                        for backw_mat in backwrdMatList:
                            backwMatListOfOrigs.append(backw_mat.original()); #print(backw_mat.name(),' ==> ',backw_mat.original().name())
                        
                        for ingr in material.ingredients():
                            
                            # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                            
                            if not ingr in backwMatListOfOrigs: 
                            #if not ingr in backwrdMatList: 
                                s = getMatListString('',backwrdMatList)
                                print('SupplyNet.add(): ingredient "{}" of product "{}" not in inbound list: "{}"'.format(ingr.name(),material.name(),s))
                                material.show()
                                return None
                        #showMatList('   4)alle ings der Rezeptur in backwardMatList enthalten=',backwrdMatList)
                        
                        # Prüfung, ob es backwardNode-Materialien gibt, die nicht in der Rezeptur enthalten oder keine Substitute sind
                        for mat in backwrdMatList:
                            is_ingredient,isSubstitute = material.isIngredient(mat) # Prüfung auf Identität und Substitute
                            #print(' mat = {}  Product = {}   ingredient:{}'.format(mat.name(),material.name(),is_ingredient))
                            if not is_ingredient:
                                s = getMatListString('',backwrdMatList)
                                print('SupplyNet.add(): at least one ingredient of product "{}" not in inbounds {} or recipe:'.format(material.name(),s))
                                material.show('   ')
                                return None
                        #showMatList('   5)alle backwardMats sind in den ings der Rezeptur enthalten=',backwrdMatList)
                        
                        # Materialien der Rezeptur und der backward list passen nun exakt!
                        # das ist ein Manufacturing
                        activity = activity_manufacturing
                        
                #
                #
                # Fall: hier stimmt der Typ des übergebenen Objekts nicht
                #       Es sind nur Materialien zugelassen
                #
                else:
                    print('**** SupplyNet().add(): falscher Datentyp=',material.catName())
                    return None
            
            #
            # Fall: eine Node soll hinzugefügt werden, ohne dass ein Material- oder Product-Objekt angegeben war, sondern None
            #
            #       ==> dann wird das Material vererbt
            else: 
                #showMatList('   d1 )backwardMatList=',backwrdMatList)
                
                # 1) die Materialien aller backwardNodes müssen identisch sein
                # 2) das Material wird auf die neue Node vererbt
                
                # +++++ es sollte immer das Original des Substituts vererbt werden
                
                identical,mat = areMatListEntriesIdentical(backwrdMatList)
                if not identical: 
                        s = getMatListString('',backwrdMatList)
                        print('SupplyNet.add(): {} inbound materials "{}" for distritbution must be identical!'.format(mat.name(),s))
                        return None
                #print('   distrib: mat:{} wird vererbt'.format(mat.name()))
                    
                material = mat  # Vererben bzw. weiterreichen
                activity = activity_distribution
                
        else: # eine terminal node wird angefügt
            activity = activity_sourcing
            
        #print('++++Typ der anzuhängenden Node',activityDescr( activity),material.name(),supplier.name())
           
        newNode = _add_alltypes(supplier.name(),*bkwrdNodes)
        if newNode != None:
            newNode.supplier(supplier)
            newNode.activity(activity)
            if material != None: 
                newNode.material(material)
                newNode.net(self)
            #newNode.show()
                
            
        return newNode
    
    # ------------ showing functions --------------
        
    def show(self, node): node.walkAllVertices()
    def showNodeList(self,nodes,txt=''):
        s = txt+'['; sDelim = ', '; nDelim = len(sDelim)
        for node in nodes: s += '{}'.format(node.nameTitle())+sDelim
        if nodes != []: s = s[:len(s)-nDelim] if len(s)>0 else s
        s += ']'
        print(s)
        
    def showAllNodeLists(self):
        print('\nList all Nodes')
        self.showNodeList(self.endNodes(),txt='  endNodes      '); self.showNodeList(self.intermediates(),txt='  intermediates ')
        self.showNodeList(self.terminals(),txt='  terminals     '); self.showNodeList(self.allNodes(),txt='  allNodes      ')
        
    def showConstraintsL1(self):
        print('\nConstraints Level(0)')
        for k,constraint in enumerate(self.constraints()):
            s = '  [{:2}] '.format(k)
            for i,item in enumerate(constraint):
                if i==0: 
                    s += '{}'.format(item)
                else:
                    s += ' ({},{},{}), '.format(item[0],item[1].name(),item[2].name())
            print(s)
    
    # ------------ determine equations --------------
    
    # die endNodes müssen vor em Aufruf von collectIntermediatesAndTerminals() bekannt sein
    def collectIntermediatesAndTerminals(self):
        self._intermediates = []
        self._terminals = []
        for endNode in self._endNodes: 
            endNode.collectIntermediatesAndTerminals(self._intermediates,self._terminals)
            endNode.clearVisitedMarker()
            
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # close()
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   
    def compile(self,graph=False): self.close(graph=graph)
    def close(self,graph=False): 
        
        self._endNodes = []
        for node in self._allNodes:
            if (node.forward() == []) and (node.backward() != []): self._endNodes.append(node)
        self.collectIntermediatesAndTerminals()
        # Abschluss
        if self.display() or self.debug(): self.showAllNodeLists()
        #
        # baut die Links und Constraints als Array (Stufe L1) auf
        #
        self.equAll()
        if self.debug(): self.links().show()
        #
        # baut die Grafik auf
        #
    
        if self._autoGraph>0: 
            print('close() showGraph() ********** ')
            self.showGraph('model.'+self.name(),optimized=False, orient='LR')
            #self.createGraph('model.'+self.name(),optimized=False, orient='LR')
            if self._autoGraph>1: self.view()
        #
        # Erzeugung der Constraints eq und lt aus Stufe L1
        #
        self.buildConstraints()#self.debug())
        #
        # Erzeugung der Matrizen/Vektoren A_eq,b_eq,A_ub,b_ub
        #
        self.calcLinOpParams(self.debug())
      
    def _isEndNode(self,node): return True if node in self.endNodes() else False
    
    #
    # aus fromNode und toNode einen Dict für CompoundCapacitiy aufbauen
    # comp_capa_dict enthält das bisherige Dict und wird mit dem neuen Eintrag zurückgeliefert
    #
    def _incrementalBuildCompoundCapaDict(self, comp_capa_dict, from_node, to_node):
        #
        # gibt es eine compound capacity für die aktuelle from_node ?
        #
        if from_node.hasCompoundCapacity(): 
            from_ccapa = from_node.compoundCapacity()     # ccapa der from_node  'x1': from_capa = 'capa x'
            from_dict = comp_capa_dict.get(from_ccapa,{}) # lesen der bestehenden Einträge für from_capa: 
                                                          #    z.B. comp_capa_dict = {'capa x':{'x1':['y1']}}
            to_list = from_dict.get(from_node,[])         # lesen der to_node_list der from_capa: from_dict = {'x1':['y1']}     
                        
            if to_list != []:                             # to_list schon vorhanden?
                to_list.append(to_node)                   # ja, dann akt. toNode an die Liste anhängen
                from_dict.update( {from_node:to_list})    # und das from_dict mit der erweiterten to_list aktualisieren
                                                          #    to_list = ['y1','y2']
                    
            else:                                         # nein => erster Eintrag in to_list
                from_dict.update( {from_node:[to_node]} ) # {'x1':['y1']}
                           
            comp_capa_dict.update( {from_ccapa : from_dict} )  # comp_capa_dict aktualisieren: {'capa x':{'x1':['y1']}}
                                                               # comp_capa_dict aktualisieren: {'capa x':{'x1':['y1','y2']}}
        return comp_capa_dict
    # 
    # Prüfung, ob coumpound decls vorhanden sind
    # Falls ja, dann den Constraints hinzufügen
    #
    def _appendCompoundCapaDict(self,ccapa_dct,bShow):
        for ccapa,from_nodes in ccapa_dct.items():
            if len(from_nodes) > 1:
                capaCompoundConstr = []
                capaCompoundConstr.append((self.lt(),0)) # initialer Eintrag, der am Ende gesetzt wird
                sCapa = '  '
                for from_node, to_nodes_list in from_nodes.items():
                    for to_node in to_nodes_list:
                        sCapa += 'm({},{}) + '.format(from_node.title(),to_node.title())
                        capaCompoundConstr.append((1.0,from_node,to_node))
                sCapa = sCapa[:len(sCapa)-2]
                sCapa += "<= {} : compound capacity({})".format(ccapa.value(),ccapa.name())
                if bShow: print(sCapa)
                capaCompoundConstr[0] = (self.lt(),ccapa.value())
                self.constraints().append(capaCompoundConstr)
    
    
    
    # ok compoundCapa    
    def capaIntermediates(self): 
        bShow = self.display() or self.debug()
        if bShow: print('\nCapacities of intermediate nodes') 
            
        compcapa_dict = {}
        
        for imNode in self.intermediates():
            capaConstr = []
            capaConstr.append((self.lt(),0)) # initialer Eintrag, der am Ende gesetzt wird
            capacity = capacityValue( imNode.capacity() ); #print('    capaIntermediates():',capacity,imNode.compoundCapacity())
            
            if capacity >= 0:
                sCapa = '  '
                for forw in imNode.forward(): 
                    fromNode = imNode
                    toNode = forw
                    #
                    # collect compound capacity entries
                    #
                    compcapa_dict = self._incrementalBuildCompoundCapaDict( compcapa_dict, fromNode, toNode )
                    
                    sLink = 'm({},{}) + '.format(fromNode.nameTitle(),toNode.nameTitle())
                    sCapa += sLink
                    capaConstr.append((1.0,fromNode,toNode))
                  
                    self.links().add(fromNode,toNode)
                sCapa = sCapa[:len(sCapa)-2]
                sCapa += '<= {} : capacity({})'.format(capacity,imNode.nameTitle())
                capaConstr[0] = (self.lt(),capacity)
                
                if bShow: print(sCapa)
                self.constraints().append(capaConstr)
                #print('constraints=', self.constraints())
                if imNode.demand() != -1: print('*** Warning ==> unnecessary demand for node "{}"! '.format(imNode.nameTitle()))
        #
        # compound capacity den constraints hinzufügen
        #
        self._appendCompoundCapaDict(compcapa_dict, bShow)
        
    
    # ok L1
    def equEndNodes(self):
        bShow = self.display() or self.debug()
        if bShow: print('\nFlow equations of end nodes')     
        for endNode in self.endNodes():
            demand = endNode.demand()
            #print(f"endNode={endNode.name()}   demand={demand}")
            if demand >= 0:
                demandConstr = []
                demandConstr.append((self.eq(),0)) # initialer Eintrag, der am Ende gesetzt wird
                sBackw = '  '
                for backw in endNode.backward():
                    fromNode = backw
                    toNode = endNode
                    sBackw += 'm({},{}) + '.format(fromNode.nameTitle(),toNode.nameTitle())
                    demandConstr.append((1.0,fromNode,toNode))
                    self.links().add(fromNode,toNode)
                sBackw = sBackw[:len(sBackw)-2]
                sBackw += '= {} : Demand({})'.format(demand, endNode.nameTitle())
                demandConstr[0] = (self.eq(),demand)
                self.constraints().append(demandConstr)
                if bShow: print(sBackw)
            #else:
            #    print(f'*** Error ==> demand missing for node "{endNode.nameTitle()}"! => use .demand() instead of {demand}')#.format(endNode.nameTitle()))
    
    # ok L1
    def capaEndNodes(self):
        bShow = self.display() or self.debug()
        if bShow: print('\nCapacities of end nodes')
        for endNode in self.endNodes():
            capaConstr = []
            capaConstr.append((self.lt(),0)) # initialer Eintrag, der am Ende gesetzt wird
            capacity = capacityValue( endNode.capacity() )
            if capacity >= 0:
                sBackw = '  '
                for backw in endNode.backward():
                    fromNode = backw
                    toNode = endNode
                    sBackw += 'm({},{}) + '.format(fromNode.nameTitle(),toNode.nameTitle())
                    capaConstr.append((1.0,fromNode,toNode))
                    self.links().add(fromNode,toNode)
                sBackw = sBackw[:len(sBackw)-2]
                sBackw += '<= {} : capacity({})'.format(capacity,endNode.nameTitle())
                capaConstr[0] = (self.lt(),capacity)
                self.constraints().append(capaConstr)
                if bShow: print(sBackw)
    
    # ok compoundCapa  
    def capaTerminals(self): 
        bShow = self.display() or self.debug()
        if bShow: print('\nCapacities of Terminals')
        
        compcapa_dict = {}
            
        for termNode in self.terminals():
            capacity = capacityValue( termNode.capacity() )
            #
            # Does termNode got capacity decls ?
            #
            if capacity >= 0:
                capaConstr = []
                sCapa = ' '
                capaConstr.append((self.lt(),0)) # initialer Eintrag, der am Ende gesetzt wird
                for forw in termNode.forward(): 
                    fromNode = termNode
                    toNode = forw
                    #
                    # collect compound capacity entries
                    #
                    compcapa_dict = self._incrementalBuildCompoundCapaDict( compcapa_dict, fromNode, toNode )
                    
                    sLink = ' m({},{}) + '.format(fromNode.nameTitle(),toNode.nameTitle())
                    sCapa += sLink
                    capaConstr.append((1.0,fromNode,toNode))
                    
                sCapa = sCapa[:len(sCapa)-2]
                sCapa += '  <= {} : capacity({})'.format(capacity,fromNode.nameTitle())
                self.links().add(fromNode,toNode)
                capaConstr[0] = (self.lt(),capacity)
                self.constraints().append(capaConstr)
                if bShow: print(sCapa)
        #
        # compound capacity den constraints hinzufügen
        #
        self._appendCompoundCapaDict(compcapa_dict, bShow)
      
    
    # ok
    def equIntermediates(self):
        bShow = self.display() or self.debug()
        if bShow: print('\nFlow equations of intermediate nodes')
        for imNode in self.intermediates():
            #
            # Fall 1: Manufacturing => Code mit Rezeptur
            #
            if imNode.activity() == activity_manufacturing: 
                product = imNode.material()
                old_modus = True
                # **************************************************************************************
                # **************************************************************************************
                #print('*** activity =',activityDescr(imNode.activity()))
               
                if old_modus:
                    
                    # Berechnung einer MatListe rawMats aus eine Nodeliste imNode.backward()
                    rawMats = [] # enthält die Objekte type=Material ==> das sind die Einsatzmaterialien
                    for backw in imNode.backward(): 
                        material = backw.material()
                        if not material in rawMats: rawMats.append(material) 
                    ingsWithSubs,ingsWithSubsQnty = product.ingredientsWithSubstitutes(matList=rawMats, 
                                                                                       show=False)
                    # ------------------------
                    #
                    # loop über die Komponenten der Rezeptur
                    #
                    for i,raw_mat in enumerate(ingsWithSubs):
                        
                        eqnConstr = []
                        eqnConstr.append((self.eq(),0)) # initialer Eintrag, der am Ende gesetzt wird 
                        
                        # 
                        # die rechte Seite mit dem '=' und den empfangenden Nodes zuerst
                        #
                        raw_mat_qnty = product.quantity(raw_mat)
                        sForw = ''
                        for forw in imNode.forward(): 
                            fromNode = imNode
                            toNode = forw
                            sForw += '- {} * m({},{}) '.format(raw_mat_qnty,fromNode.nameTitle(),toNode.nameTitle())
                            eqnConstr.append((-raw_mat_qnty,fromNode,toNode))
                            self.links().add(fromNode,toNode)
                        sForw += ' = 0'
                       
                        # 
                        # nun die linke Seite mit den liefernden Nodes
                        #
                        ings_n_subs = ingsWithSubs[raw_mat]; #s_ing_list = self.getMatListString('ings_n_subs=',ings_n_subs); print(s_ing_list)
                        sBackw = '  '
                        #print('   ingredient=',raw_mat.name());#self.showNodeList(imNode.backward(),txt='      backward')
                        nodeMat_tuple_list = []
                        for backw in imNode.backward():
                            mat = backw.material()
                            if mat in ings_n_subs: nodeMat_tuple_list.append((backw,mat))
                            
                        for tpl in nodeMat_tuple_list:
                            #print('   {} , {}'.format(tpl[0].material().name(),tpl[1].name()))
                            fromNode = tpl[0]
                            toNode = imNode
                            sBackw += 'm({},{}) + '.format(fromNode.nameTitle(),toNode.nameTitle())
                            eqnConstr.append((1.0,fromNode,toNode))
                            self.links().add(fromNode,toNode)
                            
                        sBackw = sBackw[:len(sBackw)-3]
                        eqnConstr[0] = (self.eq(),0.0)
                        if bShow: print(sBackw,sForw)
                        self.constraints().append(eqnConstr)
                
                    #else:
                    #    print('\nNeuer Modus')
                #print('#'*20)
            #
            # Fall 2: Distribution => Code ohne Rezeptur
            #
            else: 
                #print('*** activity =',activityDescr(imNode.activity()))
                eqnConstr = []
                eqnConstr.append((self.eq(),0)) # initialer Eintrag, der am Ende gesetzt wird    
                sForw = ''
                for forw in imNode.forward(): 
                    fromNode = imNode
                    toNode = forw
                    sForw += '- m({},{}) '.format(fromNode.nameTitle(),toNode.nameTitle())
                    eqnConstr.append((-1.0,fromNode,toNode))
                sForw += ' = 0'
                sBackw = '  '
                for backw in imNode.backward(): 
                    fromNode = backw
                    toNode = imNode
                    sBackw += 'm({},{}) + '.format(fromNode.nameTitle(),toNode.nameTitle())
                    eqnConstr.append((1.0,fromNode,toNode))
                    self.links().add(fromNode,toNode)
                
                sBackw = sBackw[:len(sBackw)-3]
                eqnConstr[0] = (self.eq(),0.0)
                if bShow: print(sBackw,sForw)
                self.constraints().append(eqnConstr)
            
    def equAll(self):
        self.equIntermediates()
        self.equEndNodes()
        self.capaIntermediates()
        self.capaEndNodes()
        self.capaTerminals()
        
    # ----------- Constraints ---------------
    
    def buildConstraints(self,debug=False):
        
        def buildConstraintsL2(cmpCode,eqnCollector,debug=False):
            if debug: 
                s = ' equations' if cmpCode == 'eq' else ' upper limits'
                print('\nConstraints Level(1):'+s)
            links = self.links()
            for k,constraint in enumerate(self.constraints()):
                s = '  [{:2}] '.format(k)
                isEq = False
                eqn = []
                for i,item in enumerate(constraint):
                    if i==0: # immer eine neue Bedingung
                        isEq = True if item[0]==cmpCode else False
                        s += ' {}'.format(item)
                        eqn.append(item[1])
                    else:
                        varIndex = links.index(item[1],item[2])
                        if isEq: 
                            s += ' ({},{}), '.format(item[0],varIndex)
                            eqn.append((item[0],varIndex))
                if isEq:
                    if debug:
                        #print(s)
                        print('  [{:2}] '.format(k),eqn)
                    eqnCollector.append(eqn)
        
        if debug: self.showConstraintsL1()
        self._eqnEquals = []
        self._eqnUpperLimits = []
        buildConstraintsL2(self.eq(),self._eqnEquals,debug=debug)
        buildConstraintsL2('lt',self._eqnUpperLimits,debug=debug)
    
    # ----------- Cost calculation ---------------
        
    def calcLinOpParams(self,debug=False):
        
        def calcLinOpMatrixVec(constraintEqns):
            cols = self.links().count()
            lines = len(constraintEqns); #print('lines={} cols={}'.format(lines,cols))
            A = np.ones((lines,cols))*0
            b = np.ones(lines)*0
            for line,eqn in enumerate(constraintEqns):
                for col,item in enumerate(eqn):
                    if col==0:
                        b[line] = item
                    else:
                        value = item[0]
                        varIndex = item[1] 
                        A[line,varIndex] = value
            return A,b
        
        def showCostVec(txt,vec):
            n = len(vec)
            s = txt+'[ '
            for itm in vec: s += ' {:6.1f}'.format(itm)
            s += ' ]'
            print(s)
            
            
        def calcCosts():
            links = self.links()
            cols = links.count()
            costs = np.ones(cols)*0
            costs_var_freight = np.ones(cols)*0
            costs_var = np.ones(cols)*0
            costs_fix = np.ones(cols)*0
            costs_fix_not_absorbed = np.ones(cols)*0
            capacities = np.ones(cols)*0
            for i,link in enumerate(links): 
                fromNode = link[0]
                toNode = link[1]
                
                # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                # Fracht wird von fromNode und toNode bestimmt
                #freight = fromNode.findFreightx(fromNode,toNode, instance=False).price()
                (freight,inheritance) = fromNode.findFreight(fromNode,toNode)
                freight = freight.price() if isinstance(freight,Freight) else 0 #freight
                
                # varcost, fixcost und capacity werden nur von fromNode bestimmt
                vcFrom = fromNode.varcost(); vcFrom = vcFrom if vcFrom >= 0 else 0
                fcFrom = fromNode.fixcost(); fcFrom = fcFrom if fcFrom >= 0 else 0
               
                capaFrom = capacityValue( fromNode.capacity() )
                fcUnitFrom = fcFrom/capaFrom if capaFrom >0 else fcFrom
                #print('   i={}  capa={}  fcFrom={}   fcUnitFrom={}'.format(i,capaFrom,fcFrom,fcUnitFrom))
                
                
                not_absorbed_fixcosts = fcFrom-fcUnitFrom*capaFrom
               
                # Speicherung in Arrays
                capacities[i] = capaFrom
                costs_var_freight[i] = freight
                costs_var[i] = vcFrom
                costs_fix[i] = fcUnitFrom
                costs[i] = costs_var_freight[i] + costs_var[i] + costs_fix[i]
                costs_fix_not_absorbed[i] = not_absorbed_fixcosts
            #print('--- capa.          =',capacities)
            #print('--- absorbed FC    =',costs_fix)
            #print('--- not absorbed FC=',costs_fix_not_absorbed)
            return costs,costs_var_freight,costs_var,costs_fix,capacities
        #
        # Berechnung der Gleichungen und Ungleichungen: vor Optimierung
        #
        self._A_eq,self._b_eq = calcLinOpMatrixVec(self._eqnEquals)
        self._A_ub, self._b_ub = calcLinOpMatrixVec(self._eqnUpperLimits)
        #
        # Berechnung des Kostenvektors: vor Optimierung
        #
        self._c,self._c_freight,self._c_var,self._c_fix,self._capacities = calcCosts()
        
        if debug or self.display()>1:
            print('\nOptimization Parameters:')
            s = 'Flow Constraints = '+' {} equations with {} variables'.format(self._A_eq.shape[0],self._A_eq.shape[1]); print(s)
            print(self._A_eq)
            showCostVec('Flow Balance = ',self._b_eq)
            s = '\nUpper limit constraints = '+' {} equations for {} variables'.format(self._A_ub.shape[0],self._A_ub.shape[1]); print(s)
            print(self._A_ub)
            showCostVec('Upper limits = ',self._b_ub)
            n_cells = self._A_eq.shape[0]*self._A_eq.shape[1]+self._A_ub.shape[0]*self._A_ub.shape[1]
            s = '\nTotal number of constraints = {} for {} variables ==> {} cells to optimize'.format(self._A_eq.shape[0]+self._A_ub.shape[0],self._A_eq.shape[1],n_cells); print(s)
            showCostVec('\nTotal cost = ',self._c)
            showCostVec('   freight = ',self._c_freight)
            showCostVec('   var     = ',self._c_var)
            showCostVec('   fix     = ',self._c_fix)
            showCostVec('   capa    = ',self._capacities)
            
    # ----------- conduct optimization ---------------
    
    def execute(self): return self.optimize()
    def optimize(self):
        self._linprogResult = linprog(self._c, 
                               A_ub=self._A_ub, b_ub=self._b_ub,  # upper limit equations
                               A_eq=self._A_eq, b_eq=self._b_eq,  # balance equations
                               bounds=(0,None),                   # all node quantities >= 0: 0=lower bound, None=no upper bound
                               options={"disp": False})           # quiet mode
        self._result    = {opt_quantities: self._linprogResult.x,
                           opt_cost:       self._linprogResult.fun,
                           opt_iterations: self._linprogResult.nit,
                           opt_success:    True if self._linprogResult.success or self._linprogResult.status in [0,4] else False,    # ***HIER
                           opt_status:     self._linprogResult.status,
                           opt_capacities: self._capacities}
        self._optimized = Optimization(self,result=self._result)
        return self._optimized
       

# -----------------------------------------------
# Optimization
# -----------------------------------------------

class Optimization(Entity):
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self.name())  
    
    def buildParams(self):
        def appendLine(rc,n,line):
            newline = []
            for i in range(n): 
                newline.append(line[i])
            rc.append(line)
            
        nParams = len(self.net()._c)
        rec = [] 
       
        appendLine(rec,nParams,self._quantities)
        appendLine(rec,nParams,self.net()._c)
        appendLine(rec,nParams,self.net()._c_freight)
        appendLine(rec,nParams,self.net()._c_var)
        appendLine(rec,nParams,self.net()._c_fix)
        
        links = self.net().links()
        nLinks = 0
        for i,link in enumerate(links): nLinks += 1
        nLinks = min(nParams,nLinks)
            
        fromLink = []; fromTitle = []; fromSupplier = []; fromMaterial = []; fromCapa = []; fromDemand = []; fromActivity = []
        toLink = []; toTitle = []; toSupplier = []; toMaterial = []; toCapa = []; toDemand = []; toActivity = []
        for i,link in enumerate(links): 
            fromLink.append(link[0]); toLink.append(link[1])
            fromTitle.append(link[0].title()); toTitle.append(link[1].title())
            fromSupplier.append(link[0].source().supplier()); toSupplier.append(link[1].source().supplier())
            fromMaterial.append(link[0].source().material()); toMaterial.append(link[1].source().material())
            
            fromCapa.append(  capacityValue(link[0].source().capacity()) ); toCapa.append( capacityValue(link[1].source().capacity())  )
            
            fromDemand.append(link[0].source().demand()); toDemand.append(link[1].source().demand())
            fromActivity.append(link[0].source().activity()); toActivity.append(link[1].source().activity())
            
        appendLine(rec,nParams,fromLink); appendLine(rec,nParams,toLink)
        appendLine(rec,nParams,fromTitle); appendLine(rec,nParams,toTitle)
        appendLine(rec,nParams,fromSupplier); appendLine(rec,nParams,toSupplier)
        appendLine(rec,nParams,fromMaterial); appendLine(rec,nParams,toMaterial)
        appendLine(rec,nParams,fromCapa); appendLine(rec,nParams,toCapa)
        appendLine(rec,nParams,fromDemand); appendLine(rec,nParams,toDemand)
        appendLine(rec,nParams,fromActivity); appendLine(rec,nParams,toActivity)
        
        appendLine(rec,nParams,self._capacities)
        
        return rec
       
    def showParams(self):
        nStrLen = 8
        print('\nOptimization parameters:')
        params = self._params
        lofs = '  '
        ofs = '   '
        s = lofs+'from       '+ofs
        for colName in params[self.fromTitle()]: s += '{:8}  '.format(colName[:nStrLen])
        print(s)
        s = lofs+'to         '+ofs
        for colName in params[self.toTitle()]: s += '{:8}  '.format(colName[:nStrLen])
        print(s)
        
        s = lofs+'from       '+ofs
        for sup in params[self.fromSupplier()]: s += '{:8}  '.format(sup.name()[:nStrLen])
        print(s)
        s = lofs+'to         '+ofs
        for sup in params[self.toSupplier()]: s += '{:8}  '.format(sup.name()[:nStrLen])
        print(s)
        
        s_qnty = sum( params[self.quantities()])
        print('-'*80)
        s = lofs+'quantity '
        for qnty in params[self.quantities()]: s += '{:8.0f}  '.format(qnty)
        print(s)
        
        s_qnty = sum( params[self.quantities()])
        s = lofs+'freight  '
        for fr in params[self.freight()]: s += '{:8.0f}  '.format(fr)
        print(s)
        
        s = lofs+'varcost  '
        for vc in params[self.varcost()]: s += '{:8.0f}  '.format(vc)
        print(s)
        
        s = lofs+'fixcost  '
        for fc in params[self.fixcost()]: s += '{:8.0f}  '.format(fc)
        print(s)
        print('='*80)
        s = lofs+'total €/t'
        for tc in params[self.totalcost()]: s += '{:8.0f}  '.format(tc)
        print(s)
        s = lofs+'total T€ '
        for i,tc in enumerate(params[self.totalcost()]): 
            cost = tc*params[self.quantities()][i]/1000
            s += '{:8.0f}  '.format(cost)
        print(s)
        
    def show(self): 
        def statusText(stat):
            if stat==0: return 'Optimization terminated successfully'
            elif stat==1: return 'Iteration limit reached'
            elif stat==2: return 'Problem appears to be infeasible'
            elif stat==3: return 'Problem appears to be unbounded'
            elif stat==4: return 'Potential numerical difficulties encountered'  #'Serious numerical difficulties encountered'
            else: return 'failed due to unknown reason'
        print('\nOptimization {}'.format(self.name()))
        sSuccess = 'successful' if self.successful() else '***** not successful'
        
        sIter = '{:3} iterations'.format(self.iterations())
        sStatus = 'Status: {}:{}'.format(self.status(),statusText(self.status()))
        
        s = ''; sl = ''
        links = self.net().links()
        for i,link in enumerate(links): 
            qnty = self._quantities[i]
            sl += '{} => {} '.format(link[0].name(),link[1].name())
            s += '{}, '.format(qnty)
        
        if not self.successful():
            print('   Optimization result: {} with {}  {}'.format(sSuccess,sIter,sStatus))
        else:
            print('   {} with {}  {}'.format(sSuccess,sIter,sStatus))
            print('   cost      : {:8.0f} €'.format(self.cost()))
            print('   quantities:')
            links = self.net().links()
            for i,link in enumerate(links): 
                qnty = self._quantities[i]
                supplierFromName = link[0].source().supplier().name()
                supplierToName = link[0].source().supplier().name()
                fromLocName = link[0].source().supplier().location().name()
                toLocName = link[1].source().supplier().location().name()
                print('      [{:3}]:  {:8.3f}t   {:8}({:8}) ==> {:8}({:8})  '.format(i,qnty,supplierFromName,fromLocName,supplierToName,toLocName))
        
        self.showParams()
        return self
    
    def __init__(self, net=None, result=None ):  
        super().__init__(net.name() if net != None else 'Optimization')
        super().cat(cat_optimization)
        self._net = net
        if result != None:
            self._quantities = result[opt_quantities] 
            self._cost =       result[opt_cost]     
            self._iterations = result[opt_iterations]
            self._successful = result[opt_success]  
            self._status =     result[opt_status]     
            self._capacities = result[opt_capacities]
            self._params = self.buildParams()
        else:
            self._quantities = []
            self._capacities = []
            self._cost = -1
            self._iterations = 0
            self._successful = False
            self._status = 0
            self._params = []
            
        self.__quantities_ParamsOfs = 0
        self.__totalcost_ParamsOfs = 1
        self.__freight_ParamsOfs = 2
        self.__varcost_ParamsOfs = 3
        self.__fixcost_ParamsOfs = 4
        self.__fromNode_ParamsOfs = 5
        self.__toNode_ParamsOfs = 6
        self.__fromTitle_ParamsOfs = 7
        self.__toTitle_ParamsOfs = 8
        self.__fromSupplier_ParamsOfs = 9
        self.__toSupplier_ParamsOfs = 10
        self.__fromMaterial_ParamsOfs = 11
        self.__toMaterial_ParamsOfs = 12
        self.__fromCapacity_ParamsOfs = 13
        self.__toCapacity_ParamsOfs = 14
        self.__fromDemand_ParamsOfs = 15
        self.__toDemand_ParamsOfs = 16
        self.__fromActivity_ParamsOfs = 17
        self.__toActivity_ParamsOfs = 18
        self.__capacities_ParamsOfs = 18
        
        # create pandas data sheet
        self._sheet = self._createFrameFromOpt() if result != None else None
    
    def quantities(self): return self.__quantities_ParamsOfs
    def totalcost(self): return self.__totalcost_ParamsOfs
    def freight(self): return self.__freight_ParamsOfs
    def varcost(self): return self.__varcost_ParamsOfs
    def fixcost(self): return self.__fixcost_ParamsOfs
    def fromNode(self): return self.__fromNode_ParamsOfs
    def toNode(self): return self.__toNode_ParamsOfs
    def fromTitle(self): return self.__fromTitle_ParamsOfs
    def toTitle(self): return self.__toTitle_ParamsOfs
    def fromSupplier(self): return self.__fromSupplier_ParamsOfs
    def toSupplier(self): return self.__toSupplier_ParamsOfs
    def fromMaterial(self): return self.__fromMaterial_ParamsOfs
    def toMaterial(self): return self.__toMaterial_ParamsOfs
    def fromCapacity(self): return self.__fromCapacity_ParamsOfs
    def toCapacity(self): return self.__toCapacity_ParamsOfs
    def fromDemand(self): return self.__fromDemand_ParamsOfs
    def toDemand(self): return self.__toDemand_ParamsOfs
    def fromActivity(self): return self.__fromActivity_ParamsOfs
    def toActivity(self): return self.__toActivity_ParamsOfs
    def capacities(self): return self.__capacities_ParamsOfs
    
    def parameter(self): return self._params    # hält alle Parameter nach der Optimierung
    def sheet(self): return self._sheet         # das pandas data sheet
    def frame(self): return self._sheet         # das pandas data sheet
       
    def successful(self): return self._successful
    def iterations(self): return self._iterations
    def status(self): return self._status
    def cost(self): return self._cost
    def showGraph(self,flowOnly=False, orient='LR' ): return self._net.showGraph(optimized=True,showOptimizedFlowOnly=flowOnly, orient=orient)
    def net(self): return self._net
    def defaultFramePath(self): return System.frameDir()
    def defaultChartPath(self): return System.chartDir()
    
    #
    # create pandas data sheet
    #
    def _createFrameFromOpt(self):
        def switchColumns(frm):
            cols = frm.columns.tolist()
            cols = cols[-1:] + cols[:-1]
            return frm[cols]
        
        _opt = self
        params = self.parameter()
        rows = []
        rows.append([title for title in params[_opt.fromTitle()]])
        rows.append([title for title in params[_opt.toTitle()]])
        rows.append([node.name() for node in params[_opt.fromNode()]])
        rows.append([node.name() for node in params[_opt.toNode()]])
        rows.append([sup.name() for sup in params[_opt.fromSupplier()]])
        rows.append([sup.location().name() for sup in params[_opt.fromSupplier()]])
        rows.append([sup.location().name() for sup in params[_opt.toSupplier()]]) 
        rows.append([activityDescr(act) for act in params[_opt.fromActivity()]])
        rows.append([mat.name() for mat in params[_opt.fromMaterial()]])
        rows.append([qnty for qnty in params[_opt.quantities()]])
        rows.append([freight*params[_opt.quantities()][i] for i,freight in enumerate(params[_opt.freight()])])
        rows.append([freight for freight in params[_opt.freight()]])
        rows.append([vc*params[_opt.quantities()][i] for i,vc in enumerate(params[_opt.varcost()])])
        rows.append([vc for vc in params[_opt.varcost()]])
        rows.append([fc for fc in params[_opt.fixcost()]])
        
        rows.append([tc*params[_opt.quantities()][i] for i,tc in enumerate(params[_opt.totalcost()])])
        rows.append([tc for tc in params[_opt.totalcost()]])
        
        rows.append([capa for capa in params[_opt.fromCapacity()]])
        rows.append([dmd for dmd in params[_opt.toDemand()]])
        
    
        n = len(params[0])
        columns = ['m({})'.format(i) for i in range(n)]
        frm = pd.DataFrame(rows, columns=columns)
        frm['Decscription'] = ['Title from','to','Node from','to',
                               'Supplier', 
                               'Location from','to', 
                               'Activity',
                               'Material',
                               'Quantity [t]',
                               'Freight [€]', '[€/t]',
                               'Varcost [€]', '[€/t]',
                               'Fixcost [€]','Total [€]','[€/t]',
                               'Capacity [t]','Demand [t]']
        return switchColumns(frm) 
    
    #
    # save pandas data sheet as excel file
    #
    def save(self, filename='', path='', fformat='xls'):
        filename = (self.name() if filename=='' else filename) +'.xlsx'
        fpath = System.buildPath(filename=filename, path=path if path!='' else System.frameDir(), kind='frame')
        tabname = 'optimization'
        if fformat=='xls':
            writer = pd.ExcelWriter(fpath, engine='xlsxwriter')
            self._sheet.to_excel(writer, sheet_name=tabname)
            writer.save()
    
        
        
       
        
        

# ************************************************************************************************************
#
# Graphwizard Funktionen zur grafischen Darstellung von Supplynetworks (Graphen)
#
# ************************************************************************************************************

# -----------------------------------------------
# Graph
# -----------------------------------------------        
        
class Graph:
    def __str__(self): return "<Class '{}'|{}>".format(self.__class__.__name__,self.name())  
    def show(self): print('{}'.format(self.name())); return self
    
    def __init__(self, name, directory='', cleanup=True, size=10, rankdir='LR', optimized=False, showOptimizedFlowOnly=False ):    #r ankdir='LR', 'TB', 'BT', 'RL'
        self._name = name
        self._directory = directory if directory != '' else System.buildPath()
        
        self._filename = name
        self._graph =  Digraph(name, filename=self._filename)
        self._cleanup = cleanup
        self._graph.attr(rankdir=rankdir, size='{}'.format(size))
        
        self._fontsizeNode = '8'
        self._fontsizeEdgeActive = '6'
        self._fontsizeEdgeDeactive = '5'
        self._defPenWidth = 1
        self._defPenWidthNotOptimized = 0.5
        self._penwidthScale = 1
        self._edgeColor = 'blue'
        self._edgeColorDeactive = 'gray'
        self._edgeColorNotOptimized = 'black'
        self._fontColorActive = 'blue'
        self._fontColorDeactive = 'black'
        self._deactiveEdgesNotShown = True
        self._showOptimizedFlowOnly = showOptimizedFlowOnly
        
        self._capaText = '\ncapa '
        self._compoundCapaText = '\n'
        self._demandText = '\n '
        self._varText = '\nvc '
        self._varTextRaw = '\nprice '
        self._fixText = '\nfc '
        self._showVar = True
        self._showCapa = True
        self._showFix = True
        self._showFreightEdge = True
        
        self._descrShape = 'plaintext'
        self._descrFillcolor = 'white'
        self._descrColor = 'black'
        self._descrFontColor = 'black'
        self._descrFontsize = '10'
        
        self._rawShape = 'ellipse'
        self._rawFontsize = '8'
        self._rawFillcolor = 'white' #'orange'
        self._rawColor = 'gray'
        self._rawColorHasFlow = 'gray'
        self._rawFillcolorHasFlow = 'lightgray' #'white' #'orange'
        
        self._producerShape = 'box3d'
        self._producerFontsize = '8'
        self._producerFillcolor = 'white' #'lightgray'
        self._producerColor = 'gray'
        self._producerColorHasFlow = 'gray' #'blue'
        self._producerFillcolorHasFlow = 'lightgray'#'cyan'
        
        self._distributorShape = 'cylinder' if not isWindows() else 'box3d'
        self._distributorFontsize = '8'
        self._distributorFillcolor = 'white'#'orange'
        self._distributorColor = 'gray'
        self._distributorFillcolorEndNode = 'lightgray'#'cyan'
        self._distributorColorEndNode = 'gray' #'blue' 
        self._distributorFillcolorHasFlow = 'lightgray'#'cyan'
        self._distributorColorHasFlow = 'gray' #'blue'
        
        self._qntyUnit = 't'
        self._currency = '€'
        self._unitCost = self._currency+'/'+self._qntyUnit
        self._edgeIntNumberFormat = '{:6}'
        self._edgeFloatNumberFormat = '{}'
        
        self._optimized = optimized  # default=False: nur Darstellung des Flownets 
                                     # True: Darstellung eines Optimierungsergebnisses
        
        
    def optimized(self): return self._optimized   
    def name(self): return self._name
    def filename(self): return self._filename
    def directory(self,directory=None):
        if directory != None: 
            self._directory = directory
            return self
        else:
            return self._directory
    def view(self): self._graph.view(directory=self.directory(),cleanup=self._cleanup)
        
    def smartRound(self, number):
        vk = int(abs(number)); nk = abs(number)-abs(vk)
        r = 0.01
        isInt = False
        if nk>0:
            if vk > 0:
                f = abs(nk/vk)
                isInt = True if f<r else False
                val = int(number) if f<r else number
            else:
                val = nk if number>= 0 else -nk
        else:
            isInt = True
            val = vk if number>= 0 else -vk
        return isInt,val
    
    def fontsize(self,fontsize=None,category=''):
        if category == 'edge':
            if fontsize != None : self._fontsizeEdge = '{}'.format(fontsize); return self
            return int(self._fontsizeEdge)
        elif category == 'raw':
            if fontsize != None : self._rawFontsize = '{}'.format(fontsize); return self
            return int(self._rawFontsize)
        elif category == 'producer':
            if fontsize != None : self._producerFontsize = '{}'.format(fontsize); return self
            return int(self._producerFontsize)
        elif category == 'distributor':
            if fontsize != None : self._distributorFontsize = '{}'.format(fontsize); return self
            return int(self._distributorFontsize)
        elif category == 'descr':
            if fontsize != None : self._descrFontsize = '{}'.format(fontsize); return self
            return int(self._descrFontsize)
        else:
            if fontsize != None : self._fontsizeNode = '{}'.format(fontsize); return self
            return int(self._fontsizeNode)
        
    def shape(self,shape=None,category=''):
        if category == 'raw':
            if shape != None : self._rawShape = '{}'.format(shape); return self
            return int(self._rawShape)
        elif category == 'producer':
            if shape != None : self._producerShape = '{}'.format(shape); return self
            return int(self._producershape)
        else: 
            if shape != None : self._distributorsShape = '{}'.format(shape); return self
            return int(self._distributorShape)
        
        
    # -------- node and edge creation ------------
    
    #
    # Zeichnet die Objekte raw, production und distribution
    #
    def newNode(self,ident, shape='circle', label='', xlabel='', fillcolor='white', style='', color='gray', fontsize='', fontcolor='black'):
        self._graph.attr('node', shape=shape)
        label = ident if label == '' else label
        fontsize = self._fontsizeNode if fontsize == '' else fontsize
        self._graph.node(ident, 
                         xlabel=xlabel, # steht unten links neben der Node
                         label=label,   # der Nodetext
                         fontsize=fontsize, style='filled', fillcolor=fillcolor, color=color,fontcolor=fontcolor)
        return self
    
    # 
    # zeichnet und beschriftet die Verbindungslinien
    #
    def edge(self, fromNode, toNode, label='', arrowsize=1, headlabel='', taillabel='', penwidth=-1, quantity=0):
        penwidth = self._defPenWidth if penwidth == -1 else penwidth
        penwidth *= self._penwidthScale
        
        style = 'solid'
        edgeVisible = True
        if quantity > 0:
            color = self._edgeColor
            fontcolor = self._fontColorActive
            fontsize = self._fontsizeEdgeActive
        else:
            color = self._edgeColorDeactive if self.optimized() else self._edgeColorNotOptimized
            fontcolor = self._fontColorDeactive 
            fontsize = self._fontsizeEdgeDeactive
            if self._showOptimizedFlowOnly: edgeVisible = False
                
        # ***************
        # hier die penwidth in Abhängigkeit setzen z.B 1.3, wenn optimized() aber kein Flow (qnty=0)
        #  penwidth = 1.3 if ....
               
        if edgeVisible:
            self._graph.edge(fromNode, toNode, label=label, arrowsize='{}'.format(arrowsize), 
                         style=style, headlabel=headlabel,taillabel=taillabel, 
                         penwidth='{}'.format(penwidth), fontsize='{}'.format(fontsize),
                         color=color, fontcolor=fontcolor)
        return self
    
    # -------- category specific node creation ------------
    
    def appendNodeParamsToLabel(self,label='',capa=-1,demand=-1,vc=-1,fc=-1,supplier='',ident='',material='',typ='', ccapa_val=-1, ccapa_name=''):
        if supplier != '':
            label += '\n{}'.format(supplier)
        if capa >= 0 and self._showCapa:
            isInt,capa = self.smartRound(capa)
            label += self._compoundCapaText+'{} {} '.format(ccapa_name,ccapa_val)+self._qntyUnit if ccapa_val != -1 else ''
            label += self._capaText+'{} '.format(capa)+self._qntyUnit if capa != -1 else ''
        if demand > 0:
            isInt,demand = self.smartRound(demand)
            label += self._demandText+'{}'.format(demand)+self._qntyUnit if demand != -1 else ''
        if vc > 0 and self._showVar:
            isInt,vc = self.smartRound(vc)
            sVarText = self._varText if typ=='' else self._varTextRaw
            label += sVarText+'{} '.format(vc)+self._unitCost if vc != -1 else ''
        if fc > 0 and self._showFix:
            isInt,fc = self.smartRound(fc)
            label += self._fixText+'{} '.format(fc)+self._currency if fc != -1 else ''
        return label
        
    def description(self,ident, text=''):
        return self.newNode(ident, shape=self._descrShape, 
                            label=text, 
                            xlabel='', 
                            fontsize=self._descrFontsize,
                            color=self._descrColor,
                            fontcolor=self._descrFontColor,
                            fillcolor=self._descrFillcolor, 
                            style='filled,rounded')
    
    def raw(self,ident, material='', supplier='',capa=-1,demand=-1,vc=-1,fc=-1, location='', hasFlow=False, ccapa_val=-1, ccapa_name=''):
        label = ident if material == '' else material
        label = self.appendNodeParamsToLabel(label,capa,demand,vc,fc,supplier=supplier, ident=ident, material=material,typ='raw',ccapa_val=ccapa_val, ccapa_name=ccapa_name)
        #label += 'kein Flow1' if not hasFlow else ''
        color = self._rawColor
        fillcolor = self._rawFillcolor
        if self.optimized():
            if hasFlow: 
                color = self._rawColorHasFlow   
                fillcolor = self._rawFillcolorHasFlow  
        return self.newNode(ident, shape=self._rawShape, 
                            label=label, 
                            xlabel=location, 
                            fontsize=self._rawFontsize,
                            fillcolor=fillcolor, #self._rawFillcolor, 
                            style='filled', 
                            color=color)
                            #color=self._rawColor)
    
    def producer(self,ident, material='', supplier='',capa=-1,demand=-1,vc=-1,fc=-1, location='', hasFlow=False, ccapa_val=-1, ccapa_name=''):
        label = ident if material == '' else material
        label = self.appendNodeParamsToLabel(label,capa,demand,vc,fc,supplier=supplier, ident=ident, material=material,ccapa_val=ccapa_val, ccapa_name=ccapa_name)
        #label += 'kein Flow2' if not hasFlow else ''
        color = self._producerColor
        fillcolor = self._producerFillcolor
        if self.optimized():
            if hasFlow: 
                color = self._producerColorHasFlow   
                fillcolor = self._producerFillcolorHasFlow  
        
        return self.newNode(ident, shape=self._producerShape, 
                            label=label,     # Nodetext
                            xlabel=location, # links unter der Node
                            fontsize=self._producerFontsize,
                            fillcolor=fillcolor,
                            color=color)
                            #fillcolor=self._producerFillcolor, style='filled', 
                            #color='red' if hasFlow and self.optimized() else self._producerColor)
    
    def distributor(self,ident, material='', supplier='',capa=-1,demand=-1,vc=-1,fc=-1, location='',isEndNode=False, hasFlow=False, ccapa_val=-1, ccapa_name=''):
        label = ident if material == '' else material
        label = self.appendNodeParamsToLabel(label,capa,demand,vc,fc,supplier=supplier, ident=ident, material=material,ccapa_val=ccapa_val, ccapa_name=ccapa_name)
        #label += 'kein Flow3' if not hasFlow else ''
        color = self._distributorColor
        fillcolor = self._distributorFillcolor
        if self.optimized():
            if hasFlow or isEndNode: 
                color = self._distributorColorEndNode if isEndNode else self._distributorColorHasFlow 
                fillcolor = self._distributorFillcolorEndNode if isEndNode else self._distributorFillcolorHasFlow 
       
        return self.newNode(ident, shape=self._distributorShape, 
                            label=label, 
                            xlabel=location, 
                            fontsize=self._distributorFontsize,
                            fillcolor=fillcolor,
                            #fillcolor=self._distributorFillcolorEndNode if isEndNode and self.optimized() else self._distributorFillcolor, 
                            style='filled', 
                            color=color)
                            #color=self._distributorColorEndNode if isEndNode and self.optimized() else ('red' if hasFlow and self.optimized() else self._distributorColor))
    
    # -------- edge creation ------------
    
    def link(self,fromNode, toNode, quantity=-1, freight=-1):
        
        def calcPenwidth(qnty):
            if qnty < 5: qnty = 4
            else:
                if qnty > 50_000: qnty = 50_000
            return (np.log10(qnty)-0.5) * self._penwidthScale
        
        if quantity > 0:
            isInt,quantity = self.smartRound(quantity)
            if isInt:
                label = self._edgeIntNumberFormat.format(quantity)+self._qntyUnit if quantity != -1 else ''
            else:
                label = self._edgeFloatNumberFormat.format(quantity)+self._qntyUnit if quantity != -1 else ''
        else:
            label = ''
        if freight > 0 and self._showFreightEdge:
            label += '\n{}'.format(int(freight))+self._unitCost if freight != -1 else ''
       
        penwidth = calcPenwidth(quantity) if self.optimized() else self._defPenWidthNotOptimized
        return self.edge(fromNode, toNode, label=label, arrowsize=1, headlabel='', taillabel='', penwidth=penwidth,quantity=quantity)
        
        
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# System Init
#
# nachdem alles andere initialisiert ist
#
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def SunFlow(showVersion=False, charts='', data='', frame=''): 
    return InitSunflow(charts=charts, data=data, frame=frame, showVersion=showVersion)
def InitSunflow(charts='', data='', frame='', showVersion=False): 
    if showVersion: print(version())
        
    global sunFlowChartPath
    global sunFlowFramePath
    global sunFlowDataPath
    sunFlowChartPath = sunFlowChartPath if charts=='' else charts
    sunFlowFramePath = sunFlowFramePath if frame=='' else frame 
    sunFlowDataPath  = sunFlowDataPath  if data==''  else data
    
    return System.init().chartDir(sunFlowChartPath).dataDir(sunFlowDataPath).frameDir(sunFlowFramePath)