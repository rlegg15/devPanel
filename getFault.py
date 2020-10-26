import argparse
import datetime
import json
import requests

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--linac", type=int, default=0,
                    help="enter the number of the linac 0-3 to show statistics for")
parser.add_argument("-s", "--start", default="2020-10-01",
                    help="enter the start time in YYYY-MM-DD")
parser.add_argument("-e", "--end",  default="2020-10-23",
                    help="enter the end time in YYYY-MM-DD")
parser.add_argument("-v", "--verbosity", action="store_true",
                    help="increase output verbosity")
args = parser.parse_args()
lin=args.linac
st = args.start
stop = args.end
linpv = "ACCL:L" + str(lin) + "B:"
startTime =  datetime.datetime.fromisoformat(st)
endTime = datetime.datetime.fromisoformat(stop)
j=1
n=1
pvList = []
if  lin == 0:
     for j in range(1,9):
       pvList.append(linpv + "01" + str(j) +"0:RFS:INTLK_FIRST")

     # print(pvList)
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

# The double braces are to allow for partial formatting

ARCHIVER_URL_FORMATTER = "http://{MACHINE}-archapp.slac.stanford.edu/retrieval/data/{{SUFFIX}}"
SINGLE_RESULT_SUFFIX = "getDataAtTime?at={TIME}-07:00&includeProxies=true"
RANGE_RESULT_SUFFIX = "getData.json"
TIMEOUT = 3
class Archiver(object):

    def __init__(self, machine):
        # type: (str) -> None
        self.url_formatter = ARCHIVER_URL_FORMATTER.format(MACHINE=machine)
    
    def getValuesOverTimeRange(self, pvList, startTime, endTime, timeInterval=None):
        # type: (List[str], datetime, datetime, int) -> Dict[str, Dict[str, List[Union[datetime, str]]]]    
        url = self.url_formatter.format(SUFFIX=RANGE_RESULT_SUFFIX)
        results = {}
        for pv in pvList:
               print(requests.get(url=url, timeout=TIMEOUT,params={"pv": pv,
                                           "from": startTime.isoformat()+"-07:00",
                                           "to" : endTime.isoformat()+"-07:00"}))
               response = requests.get(url=url, timeout=TIMEOUT,
                                    params={"pv": pv,
                                           "from": startTime.isoformat()+"-07:00",
                                           "to": endTime.isoformat()+"-07:00"})
               try:
                   jsonData = json.loads(response.text)
                   element =jsonData.pop()
                   result = {"times":[], "values":[]}
                   for datum in element[u'data']:
                        result["times"].append(datum[u'secs'])
                        result["values"].append(datum[u'val'])
                   results[pv] = result
               except ValueError:
                   print("JSON error with {PVS}".format(PVS=pvList))
         return results


if __name__ == "__main__":
    archiver = Archiver("lcls")
    testList = ["BEND:LTUH:220:BDES"]
    print(archiver.getDataAtTime(testList, datetime.now()))
    print(archiver.getValuesOverTimeRange(testList,
                                          datetime.now() - timedelta(hours=60),
                                          datetime.now()))
    
