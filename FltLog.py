import argparse
import datetime
import json
import requests
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use("TkAgg")     # use the TkAgg backend with the WSL (Windows) installation

####################################################################
#
#   Code to get cammand line inputs for linac and start and stop dates
#   and generate the PV list, the times and  assemble the request for the archiver
#
###################################################################

ARCHIVER_URL_FORMATTER = "http://{MACHINE}-archapp.slac.stanford.edu/retrieval/data/{{SUFFIX}}"
SINGLE_RESULT_SUFFIX = "getDataAtTime?at={TIME}-07:00&includeProxies=true"
RANGE_RESULT_SUFFIX = "getData.json"
TIMEOUT = 3

#  This uses argparse module to get command line input for which linac
#  and the start and stop dates and returns the strings in parser variable
def  getInput():
     parser = argparse.ArgumentParser()
     parser.add_argument("linac", type=int,
                    help="enter the number of the linac 0-3 to show statistics for")
     parser.add_argument("-start", default="2020-10-01",
                    help="enter the start time in YYYY-MM-DD")
     parser.add_argument("-end",  default="2020-10-23",
                    help="enter the end time in YYYY-MM-DD")
     parser.add_argument("-v", "--verbosity", action="store_true",
                    help="increase output verbosity")
     return parser

############################################################################
#
#  this takes, "lin", the number of the linac, 0-3, and generates the PV names
#  for the rf first fault mask for all the cavities in the linac.
#  for L1B it also gets the faults from the 3.9 GHz cavities.
#  It returns the list of PVs
#
##############################################################################
def makList(lin):
     j=1
     n=1
     linpv = "ACCL:L" + str(lin) + "B:"

     pvList = []
     if  lin == 0:
        for j in range(1,9):
            pvList.append(linpv + "01" + str(j) +"0:RFS:INTLK_FIRST")

     if  lin == 1:
        for n in range(2,4):
           for j in range(1,9):
              pvList.append(linpv + "0"+str(n) + str(j) +"0:RFS:INTLK_FIRST")
        for n in range(1,3):
           for j in range(1, 9):
              pvList.append(linpv + "H" +str(n) +str(j) + "0:RFS:INTLK_FIRST")

     if  lin == 2:
        for n in range(4,16):
           if n < 10:
             for j in range(1,9):
                pvList.append(linpv + "0" + str(n) + str(j) +"0:RFS:INTLK_FIRST")
           else:
             for j in range(1,9):
                pvList.append(linpv + str(n) +str(j) + "0:RFS:INTLK_FIRST")

     if  lin == 3:
        for n in range(16,36):
           for j in range(1,9):
              pvList.append(linpv + str(n) + str(j) +"0:RFS:INTLK_FIRST")
     return pvList

##############################################################################
#
#   This is function used to allow the parser to be  a function call rather than
#   on the line when program executed
#   Still needs work, but now could call the parser a second time
#
###########################################################################
def cmdLine(args=None):
     parser = getInput()
     args =  parser.parse_args(args)
     Lin=args.linac
     st = args.start
     stop = args.end
     return Lin,st,stop


##############################################################################
#
#   This is the module that Lisa Z wrote to read data from the archiver
#   Works well but the archiver is kludgy and only returns data one PV
#   at a time. Since this is running off-site,without access to the archiver
#   and the archiver doesn't have any of these PVs in it yet anyway, the function
#   just prints the vars in the command.
#   Function was tested on RHEL6 with an existing PV to generate input files to
#   test with
#
#############################################################################

class Archiver(object):

    def __init__(self, machine):
        # type: (str) -> None
        self.url_formatter = ARCHIVER_URL_FORMATTER.format(MACHINE=machine)
        # Machine is LCLS for the archiver

    def getValuesOverTimeRange(self, pvList, startTime, endTime, timeInterval=None):

       # type: (List[str], datetime, datetime, int) -> Dict[str, Dict[str, List[Union[datetime, str]]]]
        url = self.url_formatter.format(SUFFIX=RANGE_RESULT_SUFFIX)
        results = {}
        with open("cavData3",'r') as f:     #  cavData3 is cobbled together file with fault values since
           for pv in pvList:
               # print the request without using the REQUESTS module
               print(url , TIMEOUT,"pv", pv,
                                           "from", datetime.datetime.fromisoformat(startTime +"-07:00"),
                                           "to" , datetime.datetime.fromisoformat(endTime + "-07:00"),end="\r\n")

               # response is web request.  Data comes back in JSON format

               #response = requests.get(url=url, timeout=TIMEOUT,
                                    #params={"pv": pv,
                                    #       "from": startTime.isoformat()+"-07:00",
                                    #       "to": endTime.isoformat()+"-07:00"})
               try:
                   response = f.readline()  #  this line gets changed out with  web request to archiver

                   jsonData = json.loads(response)
                   element =jsonData.pop()
                   result = { "values":[]}
                   for datum in element[u'data']:
                        result["values"].append(datum[u'val'])
#
#  bozo and clwn are variables to count the number for each type of fault in the dataset
#  fault code '1' is PLL lock, '2' is ioc watchdog, '4' is the Interlock Fault summary, '8' is Comm fault
#  '16' is an SSA fault and '32 is a cavity quench
#
                   bozo={ "PLLlock":[], "iocDog":[],"IntlkFlt":[],"CommFlt":[],"SSAFlt":[],"Quench":[]}
                   clwn=[]
                   clwn=result["values"]                #  read 'values' into clwn list
                   bozo["PLLlock"] = clwn.count(1)
                   bozo["iocDog"] = clwn.count(2)
                   bozo["IntlkFlt"] = clwn.count(4)
                   bozo["CommFlt"] = clwn.count(8)
                   bozo["SSAFlt"] = clwn.count(16)
                   bozo["Quench"]=clwn.count(32)

                   results[pv]= bozo

               except ValueError:
                   print("JSON error with {PVS}".format(PVS=pvList))
        return results

###########################################################################################

if __name__ == "__main__":

    r = {}   #define r as a dict for the PV's data
##################################################################################
#
#  bunch of lists to hold vaules since plt.bar will not accept an object with the bottom parameter
#
#################################################################################
    testList=[]
    Cavity=[]
    PLL=[]
    qnch=[]
    ioc=[]
    SSA=[]
    Intlk=[]
    com=[]
    twill=[]
    plaid =[]
    suede=[]
    gingham=[]


    test = cmdLine()
    testList = makList(test[0])
    archiver = Archiver("lcls")
    r=archiver.getValuesOverTimeRange(testList, test[1], test[2])

    #print(test[1],test[2])
##################################################################################
#  Since the  command line input code isn't in this
#  I use this to generate PVs for the linac being read
#  It gets replaced with a function call after integration
#################################################################################
#    for n in range(1,9):
#            testList.append("ACCL:L0B:01"+str(n)+"0:RFS:INTLK_FIRST")
#
#    r=getValuesOverTimeRange(testList)

    for testPV in testList:
        Cavity.append(testPV[5:13])           # strip out the linac and cavity number from PV for plot
        PLL.append(r[testPV]["PLLlock"])
        qnch.append(r[testPV]["Quench"])
        twill.append(r[testPV]["Quench"] + r[testPV]["PLLlock"])    #  plt.bar wants a list for the 'bottom' parameter
        ioc.append(r[testPV]["iocDog"])
        plaid.append(r[testPV]["Quench"] + r[testPV]["PLLlock"] +r[testPV]["IntlkFlt"])  # the fabric variables make the bars stack nice
        SSA.append( r[testPV]["SSAFlt"])
        suede.append(r[testPV]["Quench"] + r[testPV]["PLLlock"] +r[testPV]["IntlkFlt"] + r[testPV]["iocDog"])
        Intlk.append( r[testPV]["IntlkFlt"])
        gingham.append(r[testPV]["Quench"] + r[testPV]["PLLlock"] +r[testPV]["IntlkFlt"] + r[testPV]["iocDog"]+ r[testPV]["SSAFlt"])
        com.append( r[testPV]["CommFlt"])
    plt.figure(figsize=(9,4))
    plt.bar(Cavity,qnch, label='Quench')
    plt.bar(Cavity,PLL, bottom=qnch, label='PLL lock')
    plt.bar(Cavity,ioc, bottom=plaid,label='IOC Watchdog')
    plt.bar(Cavity,SSA, bottom=suede,label='SSA Flt')
    plt.bar(Cavity,Intlk, bottom=twill, label='Intlk Flt Sum')
    plt.bar(Cavity,com, bottom=gingham, label='Comm Fault')
    plt.legend()
    plt.xlabel('cavity')
    plt.ylabel('# of faults')
    plt.title("Faults per Cavity from "+test[1]+" to "+test[2])
    plt.grid()
    plt.show()
