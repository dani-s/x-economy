from XPLMMenus import *
from XPLMNavigation import *
from XPWidgetDefs import *
from XPWidgets import *
from XPStandardWidgets import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *
from XPLMPlanes import *
from httplib import *
from xml.dom import minidom
from re import *
from math import *
import urllib2
import hashlib
import os
import sys
from urllib import urlopen
from XPLMDisplay import *
from XPLMGraphics import *

class engine:
	def __init__(self,cht,runtime,chtDamage,mixDamage,engineNumber):
		self.defaultcht=cht
		self.runtime=runtime
		self.chtDamage=chtDamage
		self.engineNumber=engineNumber
		self.mixtureDamage=mixDamage
		self.numberOfEngines=XPLMGetDatai(XPLMFindDataRef("sim/aircraft/engine/acf_num_engines"))
		print "Engine created #"+str(engineNumber)

	def clearEng(self):
		print "Clearing engine"
		self.runtime=0
		self.chtDamage=0
		self.mixtureDamage=0

	def engineType(self):
		_engineType=[]
		XPLMGetDatavi(XPLMFindDataRef("sim/aircraft/prop/acf_prop_type"), _engineType, 0, self.numberOfEngines)
		return _engineType[self.engineNumber]

	def currentRPM(self):
		_currentRPM=[]
		XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_"), _currentRPM, 0, self.numberOfEngines)
		return _currentRPM[self.engineNumber]

	def currentCHT(self):
		_currentCHT=[]
		XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/engine/ENGN_CHT_c"), _currentCHT, 0, self.numberOfEngines)
		return _currentCHT[self.engineNumber]

	def currentMIX(self):
		_currentMIX=[]
		XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/engine/ENGN_mixt"), _currentMIX, 0, self.numberOfEngines)
		return _currentMIX[self.engineNumber]*100

	def planeALT(self):
		_planeALT=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/position/y_agl"))
		return _planeALT*float(3.33)

	def feed(self,sec,rpm,mix,cht,altitude):
		if rpm>0:
			self.runtime+=sec
		if self.defaultcht>0:
			_diff=abs(cht-self.defaultcht)/float(sec)
			if _diff>0:
				self.chtDamage+=_diff
		self.defaultcht=cht
		if (mix > 95 and altitude > 1000):
			self.mixtureDamage += sec

	def getData(self):
		return "&mixture"+str(self.engineNumber+1)+"="+str(self.mixtureDamage)+"&heat"+str(self.engineNumber+1)+"="+str(self.chtDamage)+"&time"+str(self.engineNumber+1)+"="+str(self.runtime)

	def isEngRun(self):
		_engrun = []
		XPLMGetDatavi(XPLMFindDataRef("sim/flightmodel/engine/ENGN_running"), _engrun, 0, self.numberOfEngines)
		return _engrun[self.engineNumber]
		


class PythonInterface:

	def XPluginStart(self):
		self.Name = "X-Economy"
		self.Sig =  "ksgy.Python.XFSEconomy"
		self.Desc = "X-Economy - plugin for FSEconomy (www.fseconomy.com)"
		self.VERSION="1.64"
		self.MenuItem1 = 0
		self.MenuItem2 = 0
		self.flying = 0
		self.flightTime = 0
		self.rentalTick = 0
		self.leaseTime = 0
		self.errormessage = 10
		self.CurrentTimeCaption=""
		self.LeaseCaption = 0
		self.Arrived = 0
		self.CurrentAircraft=""
		self.isTacho = 0
		self.FuelTanks=[]
		self.stPayload=0
		self.stEq=0
		self.gsCheat=0
		self.globalX=0
		self.globalY=0
		self.checkfuel=0
		self.err1=""
		self.err2=""
		self.ACEngine=[]
		Item = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "X-Economy", 0, 1)
		self.XFSEMenuHandlerCB = self.XFSEMenuHandler
		self.Id = XPLMCreateMenu(self, "X-Economy" , XPLMFindPluginsMenu(), Item, self.XFSEMenuHandlerCB,	0)
		XPLMAppendMenuItem(self.Id, "Open X-Economy", 1, 1)
		XPLMAppendMenuItem(self.Id, "-", 3, 1)
		XPLMAppendMenuItem(self.Id, "Set aircraft alias", 2, 1)
		self.checkACStateCB = self.checkACState
		XPLMRegisterFlightLoopCallback(self, self.checkACStateCB, 1.0, 0)

		self.DrawWindowCB = self.DrawWindowCallback
		self.KeyCB = self.KeyCallback
		self.MouseClickCB = self.MouseClickCallback
		self.WindowId = XPLMCreateWindow(self, 50, 600, 300, 400, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def DrawWindowCallback(self, inWindowID, inRefcon):

		if(self.err1 != "" and self.errormessage > 0):
			lLeft = [];	lTop = []; lRight = [];	lBottom = []
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left = int(lLeft[0]); top = int(lTop[0]); right = int(lRight[0]); bottom = int(lBottom[0])
			gResult = XPLMDrawTranslucentDarkBox(left,top+150,right+200,bottom+300)
			color = 1.0, 1.0, 1.0
			gResult = XPLMDrawString(color, left+5, top+132, self.err1, 0, xplmFont_Basic)
			gResult2 = XPLMDrawString(color, left+5, top+117, self.err2, 0, xplmFont_Basic)


	def XPluginStop(self):
		if (self.MenuItem1 == 1):
			XPDestroyWidget(self, self.XFSEWidget, 1)
			self.MenuItem1 = 0

		XPLMDestroyMenu(self, self.Id)
		XPLMUnregisterFlightLoopCallback(self, self.checkACStateCB, 0)
		XPLMDestroyWindow(self, self.WindowId)
		pass


	def XPluginEnable(self):
		return 1


	def XPluginDisable(self):
		pass


	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass


	def XFSEMenuHandler(self, inMenuRef, inItemRef):
		# If menu selected create our widget dialog
		if (inItemRef == 1):
			if (self.MenuItem1 == 0):
				self.CreateXFSEWidget(221, 640, 480, 490)
				self.MenuItem1 = 1
			else:
				if(not XPIsWidgetVisible(self.XFSEWidget)):
					XPShowWidget(self.XFSEWidget)
		elif (inItemRef == 2):
			if (self.MenuItem2 == 0):
				self.CreateACAliasWidget(128, 480, 272, 87)
				self.MenuItem2 = 1
			else:
				if (not XPIsWidgetVisible(self.ACAliasWidget)):
					XPShowWidget(self.ACAliasWidget)

	def XFSEpost(self, query):
		f1 = open(os.path.join('Resources','plugins','PythonScripts','PI_xfse.py'), 'rb')
		filemd5sum = hashlib.md5(f1.read()).hexdigest()
		f1.close()

		stuff = urlopen('http://www.x-plane.hu/x-economy/x-economy.php?md5sum='+filemd5sum+'&'+query).read()
		stuff = stuff.replace('&',' and ')
		dom = minidom.parseString(stuff)
		return dom


	def isAllEngineStopped(self):
		_allenginestopped = True
		try:
			for ienga in range(self.NumberOfEngines):
				if self.ACEngine[ienga].isEngRun() > 0:
					_allenginestopped = False
		except Exception:
			_allenginestopped = True

		return _allenginestopped


	def chkBrk(self,h,b):
		if h == 1:
			return True
		if h == 0 and b < float(1.0):
			return True
		
		return False

	def checkACState(self, elapsedMe, elapsedSim, counter, refcon):
		self.errormessage = self.errormessage - 1
		_timecompression=XPLMGetDatai(XPLMFindDataRef("sim/time/sim_speed"))
		if _timecompression==0:
			_timecompression=1
		_groundcompression=XPLMGetDatai(XPLMFindDataRef("sim/time/ground_speed"))
		XPLMSetDatai(XPLMFindDataRef("sim/time/ground_speed"),1)
		_totalcompression=1/float(_timecompression)
		if self.flying==1:
			
			if _groundcompression>1:
				self.gsCheat+=1

			if self.gsCheat>10:
				self.cancelFlight("Excessive time compression used. Your flight has been cancelled")

			isBrake=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/controls/parkbrake"))
			airspeed=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/position/groundspeed"))

			if self.ACEngine[0].engineType() == 3 or self.ACEngine[0].engineType() == 5:
				isHeli = 1
			else:
				isHeli = 0
					  
			if _timecompression > 0: 
			
				#fuel change check
				_fueltotal=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total"))


				# converting values to integer for comparison.  values after decimal were unrelaiable for this purpose.
				if((int(_fueltotal) * 0.95) > int(self.checkfuel)):
					self.cancelFlight("Airborn refueling not allowed.  Flight cancelled","")

				self.checkfuel=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total"))


				if XPLMGetDataf(XPLMFindDataRef("sim/time/total_flight_time_sec"))<float(5) and airspeed<float(10):
					self.cancelFlight("Aircraft changed or repositioned. Your flight has been cancelled","")
				
				
				# lease time calc
				if self.leaseTime>0: 
					self.leaseTime=int(self.leaseTime)-1
				if self.LeaseCaption:
					_leasehours=self.leaseTime/3600
					_leasemins=(self.leaseTime-_leasehours*3600)/60

					XPSetWidgetDescriptor(self.LeaseCaption, "Lease time left: "+str(_leasehours)+" hours "+str(_leasemins)+" mins" )
					
					
				if(self.chkBrk(isHeli,isBrake) and self.ACEngine[0].currentRPM()>float(10.0) and airspeed>float(5) and self.ACEngine[0].planeALT()>10):

					self.flightTime=int(self.flightTime)+1
					if self.CurrentTimeCaption:
						_currhours=self.flightTime/3600
						_currmins=(self.flightTime-_currhours*3600)/60
						XPSetWidgetDescriptor(self.CurrentTimeCaption, "Current flight time: "+str(_currhours)+" hours "+str(_currmins)+" mins")
					# engine feed only when flying: pre-heat recommended on ground
					for iengfeed in range(self.NumberOfEngines):
						#sec,rpm,mix,cht,altitude):
						self.ACEngine[iengfeed].feed(1,self.ACEngine[iengfeed].currentRPM(),self.ACEngine[iengfeed].currentMIX(),self.ACEngine[iengfeed].currentCHT(),self.ACEngine[iengfeed].planeALT())

				# arrive
				else:
					if isHeli == 1:
						if(self.flightTime>60 and self.isAllEngineStopped() and self.ACEngine[0].planeALT()<50 and airspeed<float(5)):
							print "Heli arrived"
							self.arrive()
					else:
						if(self.flightTime>60 and self.isAllEngineStopped() and self.ACEngine[0].planeALT()<50 and isBrake==1.0 and airspeed<float(30)):
							print "Plane arrived"
							self.arrive()
							
					

				if self.isTacho==1:
					self.rentalTick+=(self.ACEngine[0].currentRPM()/float(3600.0))

			if(self.stEq=="0"):
				self.disableAP()
				self.disableGPS()
				self.disableIFR()

			if(self.stEq=="1"):
				self.disableAP()
				self.disableGPS()

			if(self.stEq=="2"):
				self.disableAP()
				self.disableIFR()

			if(self.stEq=="4"):
				self.disableGPS()
				self.disableIFR()

			if(self.stEq=="3"):
				self.disableAP()

			if(self.stEq=="5"):
				self.disableGPS()

			if(self.stEq=="6"):
				self.disableIFR()

			XPLMSetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fixed"),float(self.stPayload))

		return float(_totalcompression)

	def disableGPS(self):
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps1"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps2"),6)

	def disableAP(self):
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_otto"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_otto"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_fdir"),6)

	def disableIFR(self):
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs1"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs2"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad1"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad2"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gls"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_dme"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf1"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf2"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav1"),6)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav2"),6)


	def enableAllInstruments(self):
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps1"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps2"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_otto"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_otto"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_fdir"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs1"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs2"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad1"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad2"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gls"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_dme"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf1"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf2"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav1"),0)
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav2"),0)


	def arrive(self):
		print "Arrive()"
		if self.Arrived==0:
			self.Arrived=1
			if self.leaseTime>0:

				print "Flight has arrived"
				
				_PlaneLatdr = XPLMFindDataRef("sim/flightmodel/position/latitude")
				_PlaneLondr = XPLMFindDataRef("sim/flightmodel/position/longitude")
				_lat = XPLMGetDataf(_PlaneLatdr)
				_lon = XPLMGetDataf(_PlaneLondr)

				_totalfuel = 0

				_fueltanksQTY = []
				XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel"),_fueltanksQTY,0,XPLMGetDatai(XPLMFindDataRef("sim/aircraft/overflow/acf_num_tanks")))
				for _iTotFuel in range(XPLMGetDatai(XPLMFindDataRef("sim/aircraft/overflow/acf_num_tanks"))):
					_totalfuel = _totalfuel + _fueltanksQTY[_iTotFuel]/float(2.68735)

				print "Fuel at arrival: "+str(_totalfuel)
				
				_iFuel=0
				_actfueltanks=float(0)
				for _iFuel in range(len(self.FuelTanks)):
					if self.FuelTanks[_iFuel]==1:
						_actfueltanks=_actfueltanks+1
				_iFuel=0
				_fuelarray=[]
				_eachfuel=_totalfuel/float(_actfueltanks) # thx no2 jck :)
				for _iFuel in range(len(self.FuelTanks)):
					if self.FuelTanks[_iFuel]==0:
						_fuelarray.append(0)
					else:
						_fuelarray.append(_eachfuel)


				#print "arrived2"
				
				_c=_fuelarray[0]
				_lm=_fuelarray[1]
				_la=_fuelarray[2]
				_let=_fuelarray[3]
				_rm=_fuelarray[4]
				_ra=_fuelarray[5]
				_rt=_fuelarray[6]
				_c2=_fuelarray[7]
				_c3=_fuelarray[8]
				_x1=_fuelarray[9]
				_x2=_fuelarray[10]

				_engineStr=""
				for _ieng in range(self.NumberOfEngines):
					_engineStr=_engineStr+str(self.ACEngine[_ieng].getData())
					
				print "Engine conditions: "+_engineStr

				if self.isTacho==1:
					print "Flight was tacho"
					_finishflight=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=arrive&rentalTick="+str(int(self.rentalTick))+"&lat="+str(_lat)+"&lon="+str(_lon)+"&c="+str(_c)+"&lm="+str(_lm)+"&la="+str(_la)+"&let="+str(_let)+"&rm="+str(_rm)+"&ra="+str(_ra)+"&rt="+str(_rt)+"&c2="+str(_c2)+"&c3="+str(_c3)+"&x1="+str(_x1)+"&x2="+str(_x2)+_engineStr)
				else:
					print "Flight wasn't tacho"
					_finishflight=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=arrive&rentalTime="+str(self.flightTime)+"&lat="+str(_lat)+"&lon="+str(_lon)+"&c="+str(_c)+"&lm="+str(_lm)+"&la="+str(_la)+"&let="+str(_let)+"&rm="+str(_rm)+"&ra="+str(_ra)+"&rt="+str(_rt)+"&c2="+str(_c2)+"&c3="+str(_c3)+"&x1="+str(_x1)+"&x2="+str(_x2)+_engineStr)

				print "Your flight has been logged to the server"
				
				if len(_finishflight.getElementsByTagName('result'))>0:
					_err=_finishflight.getElementsByTagName('result')[0].firstChild.data
					_errA=_err.split('|')
					
					for ierr in range(len(_errA)):
						if _errA[ierr]>80:
							_terrA=_errA[ierr].split('.')
							XPSetWidgetDescriptor(self.ErrorCaption[ierr], _terrA[0])
							XPSetWidgetDescriptor(self.ErrorCaption[ierr+1], _terrA[1].lstrip())
						else:
							XPSetWidgetDescriptor(self.ErrorCaption[ierr], _errA[ierr])

					XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 1)
					XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 0)
					
				print "Flight logging complete.  Ready for the next flight"

			else:
				print "Lease time has ended, cancelling flight"
				self.cancelFlight("Lease time has ended. Your flight has been cancelled. Sorry, you will have to re-fly this trip","")
				
			print "Flight time reset. Enabling all instruments"
			
			self.flightTime=0
			self.enableAllInstruments()
			
			print "Flight time reset. All instruments enabled"


	def cancelFlight(self,message,message2):
		print "Cancel flight function"
		self.flying=0

		cancelflight=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=cancel")
		if (cancelflight.getElementsByTagName('response')[0].firstChild.nodeName=="ok"):
			XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 1)
			XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 0)
			XPSetWidgetDescriptor(self.ErrorCaption[0], message)
			XPSetWidgetDescriptor(self.ErrorCaption[1], message2)
			self.err1 = message
			self.err2 = message2
			self.errormessage = 10
			
		print "Cancel flight1: " + message
		print "Cancel flight2: " + message2


	def addAssignment(self,aIndex,aFrom,aTo,aCargo):
		print "Adding assignment #" + str(aIndex) +", From: "+ str(aFrom) +", To: "+ str(aTo) +", Cargo: "+ str(aCargo)
		_baseY1=(aIndex+1)*18+120
		_baseY2=(aIndex+1)*28+120
		oLeft=[]
		oTop=[]
		oRight=[]
		oBottom=[]
		XPGetWidgetGeometry(self.XFSEWidget,oLeft,oTop,oRight,oBottom)
		y=oTop[0]
		x=oLeft[0]
		_offset=10
		self.FromCaption.append(XPCreateWidget(x+20, 	y-_baseY1+_offset*aIndex, x+50, 	y-_baseY2+_offset*aIndex,1, "From: -", 0, self.XFSEWidget,xpWidgetClass_Caption))
		self.ToCaption.append(XPCreateWidget(x+140, 	y-_baseY1+_offset*aIndex, x+170, 	y-_baseY2+_offset*aIndex,1, "To: -", 0, self.XFSEWidget,xpWidgetClass_Caption))
		self.CargoCaption.append(XPCreateWidget(x+210, 	y-_baseY1+_offset*aIndex, x+240,	y-_baseY2+_offset*aIndex,1, "Cargo: -", 0, self.XFSEWidget,xpWidgetClass_Caption))
		XPSetWidgetDescriptor(self.FromCaption[aIndex], str(aFrom))
		XPSetWidgetDescriptor(self.ToCaption[aIndex], str(aTo))
		XPSetWidgetDescriptor(self.CargoCaption[aIndex], str(aCargo))

		if(aIndex>4):
			# set scrollbar
			XPSetWidgetProperty(self.XFSEScrollbar,xpProperty_ScrollBarMin, 0)
			XPSetWidgetProperty(self.XFSEScrollbar,xpProperty_ScrollBarMax, aIndex+1)
			XPSetWidgetProperty(self.XFSEScrollbar,xpProperty_ScrollBarSliderPosition, aIndex+1)

			#TODO hide the invisible assignemnts
			#XPHideWidget(self.CargoCaption[aIndex])
		print "Assignment added #"+str(aIndex)

	def CreateXFSEWidget(self, x, y, w, h):
		#read ini file
		try:
			_INIfile=open(os.path.join('Resources','plugins','PythonScripts','x-economy.ini'), 'r')
			_userINI=_INIfile.readline()
			_userINI=_userINI.replace('\n','')
			_passINI=_INIfile.readline()
			_INIfile.close()
			print "Init successfully completed"

		except IOError, (errno, strerror):
			_userINI=""
			_passINI=""
			#print "no ini file, creating an empty one"


		#print "creating window"
		self.globalX=x
		self.globalY=y
		x2 = x + w
		y2 = y - h
		Buffer = "X-Economy v"+str(self.VERSION)

		# Create the Main Widget window
		self.XFSEWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,	0, xpWidgetClass_MainWindow)



		# Add Close Box decorations to the Main Widget
		XPSetWidgetProperty(self.XFSEWidget, xpProperty_MainWindowHasCloseBoxes, 1)

		# Create the Sub Widget1 window
		# Added by Egor 'SanDmaN' Pastukhov 22.03.2010 - littile correction of window geometry (height)
		XFSEWindow1 = XPCreateWidget(x+10, y-30, x2-10, y2+400,
					     1,		# Visible
					     "",		# desc
					     0,		# root
					     self.XFSEWidget,
					     xpWidgetClass_SubWindow)

		# Set the style to sub window
		XPSetWidgetProperty(XFSEWindow1, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)


		# Create the Sub Widget2 window
		XFSEWindow2 = XPCreateWidget(x+10, y-100, x2-10, y2+10,
					     1,		# Visible
					     "",		# desc
					     0,		# root
					     self.XFSEWidget,
					     xpWidgetClass_SubWindow)

		# Set the style to sub window
		XPSetWidgetProperty(XFSEWindow2, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

		XFSEWindow3 = XPCreateWidget(x+15, y-130, x2-35, y2+150,
					     1,		# Visible
					     "",		# desc
					     0,		# root
					     self.XFSEWidget,
					     xpWidgetClass_SubWindow)

		# Set the style to sub window
		XPSetWidgetProperty(XFSEWindow2, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

		# Login user caption
		LoginUserCaption = XPCreateWidget(x+20, y-40, x+50, y-60,1, "Username:", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Login user field
		self.LoginUserEdit = XPCreateWidget(x+80, y-40, x+160, y-60,1, _userINI, 0, self.XFSEWidget,xpWidgetClass_TextField)
		XPSetWidgetProperty(self.LoginUserEdit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.LoginUserEdit, xpProperty_Enabled, 1)

		# Login pass caption
		LoginPassCaption = XPCreateWidget(x+20, y-60, x+50, y-80,1, "Password:", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Login user field
		self.LoginPassEdit = XPCreateWidget(x+80, y-60, x+160, y-80,1, _passINI, 0, self.XFSEWidget,xpWidgetClass_TextField)
		XPSetWidgetProperty(self.LoginPassEdit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.LoginPassEdit, xpProperty_Enabled, 1)
		XPSetWidgetProperty(self.LoginPassEdit, xpProperty_PasswordMode, 1)

		# Login button
		self.LoginButton = XPCreateWidget(x+180, y-40, x+260, y-60,1, "Log in", 0, self.XFSEWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.LoginButton, xpProperty_ButtonType, xpPushButton)

		# Server response text
		self.ServerResponseCaption = XPCreateWidget(x+180, y-60, x+260, y-80,1, "You are not logged in", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Assignments text
		self.AssignmentListCaption = XPCreateWidget(x+20, y-105, x+50, y-125,1, "Assignment info:", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Error text
		self.ErrorCaption=[]
		self.ErrorCaption.append(XPCreateWidget(x+20, y-410, x+50, y-430,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption))
		# Error2 text
		self.ErrorCaption.append(XPCreateWidget(x+20, y-420, x+50, y-440,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption))
		# Error3 text
		self.ErrorCaption.append(XPCreateWidget(x+20, y-430, x+50, y-450,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption))

		# From
		self.FromCaption=[]
		#self.FromCaption.append(XPCreateWidget(x+20, y-120, x+50, y-140,1, "From: -", 0, self.XFSEWidget,xpWidgetClass_Caption))

		# To
		self.ToCaption=[]
		#self.ToCaption.append(XPCreateWidget(x+140, y-120, x+170, y-140,1, "To: -", 0, self.XFSEWidget,xpWidgetClass_Caption))

		# Cargo
		self.CargoCaption=[]
		#self.CargoCaption.append(XPCreateWidget(x+210, y-120, x+240, y-140,1, "Cargo: -", 0, self.XFSEWidget,xpWidgetClass_Caption))

		# Comment
		#self.CommentCaption=[]
		#self.CommentCaption.append(XPCreateWidget(x+20, y-140, x+50, y-160,1, "Comment: -", 0, self.XFSEWidget,xpWidgetClass_Caption))

		# AC reg
		self.ACRegCaption = XPCreateWidget(x+20, y-340, x+50, y-360,1, "Aircraft registration: -", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Lease expires
		self.LeaseCaption = XPCreateWidget(x+20, y-360, x+50, y-380,1, "Lease time: -", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Current flight time
		self.CurrentTimeCaption = XPCreateWidget(x+20, y-330, x+50, y-450,1, "Current flight time: -", 0, self.XFSEWidget,xpWidgetClass_Caption)


		# Start fly button
		self.StartFlyButton = XPCreateWidget(x+360, y-40, x+450, y-60,
						     1, "Start flying", 0, self.XFSEWidget,
						     xpWidgetClass_Button)
		XPSetWidgetProperty(self.StartFlyButton, xpProperty_ButtonType, xpPushButton)
		XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 0)

		# cancel fly button
		self.CancelFlyButton = XPCreateWidget(x+360, y-60, x+450, y-80,
						      1, "Cancel flight", 0, self.XFSEWidget,
						      xpWidgetClass_Button)
		XPSetWidgetProperty(self.CancelFlyButton, xpProperty_ButtonType, xpPushButton)
		XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 0)

		# Register our widget handler
		self.XFSEHandlerCB = self.XFSEHandler
		XPAddWidgetCallback(self, self.XFSEWidget, self.XFSEHandlerCB)

		#scrollbar
		self.XFSEScrollbar = XPCreateWidget(x+445, y-130, x2-10, y2+150, 1, "", 0,	self.XFSEWidget, xpWidgetClass_ScrollBar)
		XPSetWidgetProperty(self.XFSEScrollbar,xpProperty_ScrollBarMin, 0)

		self.UpdateButton = XPCreateWidget(x+370, y-410, x+450, y-430,1, "Update client", 0, self.XFSEWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.UpdateButton, xpProperty_ButtonType, xpPushButton)
		XPSetWidgetProperty(self.UpdateButton, xpProperty_Enabled, 0)
		#print "window ready"

	def XFSEHandler(self, inMessage, inWidget,    inParam1, inParam2):
		if (inMessage == xpMessage_CloseButtonPushed):
			print "Client window closed"
			if (self.MenuItem1 == 1):
				XPHideWidget(self.XFSEWidget)
				return 1
			
			

		if(inMessage == xpMsg_ScrollBarSliderPositionChanged):
			if (inParam1 == self.XFSEScrollbar):
				_max_assignment = int(XPGetWidgetProperty(self.XFSEScrollbar,xpProperty_ScrollBarMax,0))
				_scrpos = _max_assignment - int(XPGetWidgetProperty(self.XFSEScrollbar,xpProperty_ScrollBarSliderPosition,0))
				#print str(_scrpos)
				#TODO scrolling 

				#XPHideWidget(self.FromCaption[_scrpos])
				#print str(scrpos) + " ---"


		if (inMessage == xpMsg_PushButtonPressed):
			print "GUI button pressed"
			if (inParam1 == self.LoginButton):
				print "BTN Login"
				Buffer = []
				XPGetWidgetDescriptor(self.LoginUserEdit,Buffer,256)
				XPGetWidgetDescriptor(self.LoginPassEdit,Buffer,256)
				self.userstr=Buffer[0]
				self.passstr=Buffer[1]
				logincheck=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=accountCheck")
				print "Logincheck"


				if (logincheck.getElementsByTagName('response')[0].firstChild.nodeName=="ok"):
					XPSetWidgetDescriptor(self.ServerResponseCaption, "Logged in!")
					XPSetWidgetProperty(self.LoginButton, xpProperty_Enabled, 0)
					XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 1)
					print "Login successful"
					
				else:
					print "Login was not successful"
					
					if(logincheck.getElementsByTagName('response')[0].firstChild.nodeName=="notok"):
						XPSetWidgetDescriptor(self.ServerResponseCaption, "New version available, see below...")
						XPSetWidgetDescriptor(self.ErrorCaption[0], "!!! New version is available: v"+str(logincheck.getElementsByTagName('notok')[0].firstChild.data))
						XPSetWidgetProperty(self.UpdateButton, xpProperty_Enabled, 1)
						print "New version avail"

					else:
						XPSetWidgetDescriptor(self.ServerResponseCaption, "Invalid account!")
						print "Invalid account"

				#logincheck.unlink()
				return 1

			if (inParam1 == self.StartFlyButton):
				print "BTN Start flying"
				_INIFileW=open(os.path.join('Resources','plugins','PythonScripts','x-economy.ini'), 'w')
				_INIFileW.write(self.userstr+'\n'+self.passstr)
				_INIFileW.close()
				
				# Added by Egor 'SanDmaN' Pastukhov - 22.03.2010
				self.CurrentAircraft = self.ReadACAliasFromFile()
				
				if (self.CurrentAircraft == ""):
					ByteVals = []
					XPLMGetDatab(XPLMFindDataRef("sim/aircraft/view/acf_descrip"), ByteVals, 0, 500)
					self.CurrentAircraft = ByteVals[0].replace(' ','%20')

				print "Current AC: " + self.CurrentAircraft

				#clear prev a/c's engines
				self.ACEngine = []

				# set up engines
				self.NumberOfEngines=int(XPLMGetDatai(XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")))
				print "Number of engines: " + str(self.NumberOfEngines)
				_OAT=XPLMGetDataf(XPLMFindDataRef("sim/weather/temperature_ambient_c"))

				for _iengApp in range(self.NumberOfEngines):
					self.ACEngine.append(engine(_OAT,0,0,0,_iengApp))

				#destroy captions
				for idestroy in range(len(self.FromCaption)):
					XPDestroyWidget(self,self.FromCaption[idestroy],1)
					XPDestroyWidget(self,self.ToCaption[idestroy],1)
					XPDestroyWidget(self,self.CargoCaption[idestroy],1)

				self.FromCaption=[]
				self.ToCaption=[]
				self.CargoCaption=[]

				#print _stmp2

				if self.CurrentAircraft=="":
					XPSetWidgetDescriptor(self.ErrorCaption[0], "Unknown aircraft: "+str(ByteVals[0])+". If you're sure this is an FSE compatible aircraft, please edit")
					XPSetWidgetDescriptor(self.ErrorCaption[1], "aircraft description in Plane Maker, eg.: King Air B200. If you're not sure, or it's a new")
					XPSetWidgetDescriptor(self.ErrorCaption[2], "plane to FSE, please email to templates@fseconomy.com including the plane specs")
				else:
					PlaneLatdr = XPLMFindDataRef("sim/flightmodel/position/latitude")
					PlaneLondr = XPLMFindDataRef("sim/flightmodel/position/longitude")
					Lat = XPLMGetDataf(PlaneLatdr)
					Lon = XPLMGetDataf(PlaneLondr)
					self.err1=""
					self.err2=""

					startFlight=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=startFlight&lat="+str(Lat)+"&lon="+str(Lon)+"&aircraft="+self.CurrentAircraft.replace(' ','%20'))
					if startFlight.getElementsByTagName('response')[0].firstChild.nodeName=="error":
						#print startFlight.getElementsByTagName('error')[0].firstChild.data
						XPSetWidgetDescriptor(self.ErrorCaption[0], startFlight.getElementsByTagName('error')[0].firstChild.data)
						XPSetWidgetDescriptor(self.ErrorCaption[1], "")
						XPSetWidgetDescriptor(self.ErrorCaption[2], "")
					else:

						XPSetWidgetDescriptor(self.ErrorCaption[0], "")
						XPSetWidgetDescriptor(self.ErrorCaption[1], "")
						XPSetWidgetDescriptor(self.ErrorCaption[2], "")
						stFrom="-"
						stTo="-"
						stCargo="-"

						for iAssignment in range(len(startFlight.getElementsByTagName('assignment'))):
							self.addAssignment(iAssignment,str(startFlight.getElementsByTagName('from')[iAssignment].firstChild.data),str(startFlight.getElementsByTagName('to')[iAssignment].firstChild.data),str(startFlight.getElementsByTagName('cargo')[iAssignment].firstChild.data))

						Accounting=startFlight.getElementsByTagName('accounting')[0].firstChild.data
						if Accounting=="tacho":
							self.isTacho=1

						self.stEq=startFlight.getElementsByTagName('equipment')[0].firstChild.data

						if(self.stEq=="0"):
							stEquipment=" (VFR)"
						if(self.stEq=="1"):
							stEquipment=" (IFR)"
						if(self.stEq=="2"):
							stEquipment=" (GPS)"
						if(self.stEq=="4"):
							stEquipment=" (AP)"
						if(self.stEq=="3"):
							stEquipment=" (IFR, GPS)"
						if(self.stEq=="5"):
							stEquipment=" (AP, IFR)"
						if(self.stEq=="6"):
							stEquipment=" (AP, GPS)"
						if(self.stEq=="7"):
							stEquipment=" (IFR, AP, GPS)"

						stACReg=startFlight.getElementsByTagName('registration')[0].firstChild.data
						stLE=startFlight.getElementsByTagName('leaseExpires')[0].firstChild.data
						XPSetWidgetDescriptor(self.ACRegCaption, "Aircraft registration: "+str(stACReg)+str(stEquipment))
						self.leaseTime = 0
						self.leaseTime=int(stLE)
						XPSetWidgetDescriptor(self.LeaseCaption, "Lease time: "+str(int(stLE)/3600)+" hours")

						# set weight and fuel
						self.stPayload=startFlight.getElementsByTagName('payloadWeight')[0].firstChild.data
						stFuel=startFlight.getElementsByTagName('fuel')[0].firstChild.data
						XPLMSetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fixed"),float(self.stPayload))
						astFuel=stFuel.split(' ')
						self.FuelTanks=[]

						totalFuel=float(0)
						for iFuel in range(len(astFuel)-1):
							totalFuel+=float(astFuel[iFuel])

							if float(astFuel[iFuel])>float(0):
								self.FuelTanks.append(1)
							else:
								self.FuelTanks.append(0)

						num_tanks = XPLMGetDatai(XPLMFindDataRef("sim/aircraft/overflow/acf_num_tanks")) # thx sandy barbour :)
						currentFuel = totalFuel*float(2.68735)
						_it=0
						_fuelPerTanks = []
						for _it in range(num_tanks):
							_currentRatio = []
							XPLMGetDatavf(XPLMFindDataRef("sim/aircraft/overflow/acf_tank_rat"),_currentRatio,0,num_tanks)
							_fuelPerTanks.append(currentFuel*_currentRatio[_it])								
						XPLMSetDatavf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel"),_fuelPerTanks,0,num_tanks)

						self.checkfuel=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total"))

						XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 0)
						XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 1)

						self.Arrived=0
						self.flightTime = 0
						self.flying=1 # start flight query
						self.rentalTick = 0
						self.gsCheat = 0

						for iengclear in range(self.NumberOfEngines):
							self.ACEngine[iengclear].clearEng()

					#startFlight.unlink()
					return 1

			if (inParam1 == self.CancelFlyButton):
				self.cancelFlight("Flight cancelled","")

			if (inParam1 == self.UpdateButton):
				_newClient = urlopen('http://x-plane.hu/x-economy/PI_xfse.py').read()
				_oldClient=open(os.path.join('Resources','plugins','PythonScripts','PI_xfse.py'), 'w')
				_oldClient.write(_newClient)
				_oldClient.close()
				XPSetWidgetDescriptor(self.ErrorCaption[0], "Your client is updated, please restart X-Plane,")
				XPSetWidgetDescriptor(self.ErrorCaption[1], "or reload plugins via Plugins / Python Interface / Control Panel")
				self.err1 = "Your client is updated, please restart X-Plane,"
				self.err2 = "or reload plugins via Plugins / Python Interface / Control Panel"

		return 0

	# Added by SanDmaN
	# Custom description workaround
	def ReadACAliasFromFile(self):
		raw_PlanePath = XPLMGetNthAircraftModel(0)
		planePath = os.path.dirname(raw_PlanePath[1])

		aliasFile = os.path.join(planePath, 'xfse_alias.txt')
		#print "debug: " + aliasFile

		if (os.path.exists(aliasFile) and os.path.isfile(aliasFile)):
			fd = open(aliasFile, 'r')
			alias = fd.readline()
			fd.close()
			alias = alias.replace('\r','')
			alias = alias.replace('\n','')

			#print "Alias from xfse_alias.txt: " + alias
			return alias

		#print "Can't find xfse_alias.txt"
		return ""

	def WriteACAliasToFile(self, alias):
		raw_PlanePath = XPLMGetNthAircraftModel(0)
		planePath = os.path.dirname(raw_PlanePath[1])

		aliasFile = os.path.join(planePath, 'xfse_alias.txt')
		#print "debug: " + aliasFile

		fd = open(aliasFile, 'wb')
		alias = fd.write(alias)
		fd.close()

	def ACAliasWidget_cb(self, inMessage, inWidget, inParam1, inParam2):
		if (inMessage == xpMessage_CloseButtonPushed):
				XPHideWidget(self.ACAliasWidget)
				return 1

		if (inMessage == xpMsg_PushButtonPressed):
			if (inParam1 == self.SetACAliasButton):
				ac_alias = []
				XPGetWidgetDescriptor(self.ACAliasEdit, ac_alias, 256)
				self.WriteACAliasToFile(ac_alias[0])
				XPHideWidget(self.ACAliasWidget)
				return 1

		if (inMessage == xpMsg_Shown):
			ac_alias = self.ReadACAliasFromFile()
			XPSetWidgetDescriptor(self.ACAliasEdit, ac_alias)
			return 1

		return 0

	def CreateACAliasWidget(self, x, y, w ,h):
		x2 = x + w
		y2 = y - h

		self.ACAliasWidget = XPCreateWidget(x, y, x2, y2, 1, "Enter custom alias", 1, 0, xpWidgetClass_MainWindow)
		XPSetWidgetProperty(self.ACAliasWidget, xpProperty_MainWindowHasCloseBoxes, 1)

		HintCaption = XPCreateWidget(x+7, y-17, x+248, y-37, 1, "Leave input field blank to use alias from .acf file", 0, self.ACAliasWidget, xpWidgetClass_Caption)

		# Alias field
		ac_alias = self.ReadACAliasFromFile()
		self.ACAliasEdit = XPCreateWidget(x+7, y-40, x+265, y-60, 1, ac_alias, 0, self.ACAliasWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.ACAliasEdit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.ACAliasEdit, xpProperty_Enabled, 1)

		# SET button
		self.SetACAliasButton = XPCreateWidget(x+96, y-62, x+176, y-82, 1, "Set", 0, self.ACAliasWidget, xpWidgetClass_Button)
		XPSetWidgetProperty(self.SetACAliasButton, xpProperty_ButtonType, xpPushButton)

		# callback
		self.ACAliasWidgetCB = self.ACAliasWidget_cb
		XPAddWidgetCallback(self, self.ACAliasWidget, self.ACAliasWidgetCB)
	# end of addition