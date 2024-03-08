import json
import logging
import requests
import time
import datetime
from urllib.parse import urljoin

FRAMEWORK_DEV_URL=''
FRAMEWORK_PROD_URL=''

class mycomp_snow:

    def __init__(self, xauthKey: str, username: str = "", password: str = "", snow_environment: str = "Production", framework_environment: str = "Production") -> None:
        self._xauthKey = xauthKey
        self._username = username
        self._password = password
        self.framework_environment = framework_environment
        

        if ( self.framework_environment == "Production"):
            self._base_url = FRAMEWORK_PROD_URL
        else:
            self._base_url = FRAMEWORK_DEV_URL 

        if ( snow_environment == "Production" or snow_environment == "mycompprod" or snow_environment == "https://mycompprod.service-now.com"):
            self.snow_environment = "mycompprod"
        elif ( snow_environment == "QA" or snow_environment == "mycompqa" or snow_environment == "https://mycompqa.service-now.com"):
            self.snow_environment = "mycompqa"
        elif ( snow_environment == "Stage" or snow_environment == "mycompstage" or snow_environment == "https://mycompstage.service-now.com"):
            self.snow_environment = "mycompstage"
        elif ( snow_environment == "Development" or snow_environment == "mycompdev" or snow_environment == "https://mycompdev.service-now.com"):
            self.snow_environment = "mycompdev"
        elif ( snow_environment == "Development2" or snow_environment == "mycomp2dev" or snow_environment == "https://mycomp2dev.service-now.com"):
            self.snow_environment = "mycomp2dev"
        else:
            self.snow_environment = "mycompdev"

        #print(self.snow_environment)

    def _createHeader(self):
        headersList = {
        "Accept": "application/json",
        "x-functions-key": self._xauthKey,
        "Content-Type": "application/json", 
        "instance": self.snow_environment
        }

        return headersList
    
    def parsereturnValue(self, returnValue):
        try:
            if 'exit_code' and 'exit_message' in returnValue:
                pass
            elif "result" not in returnValue and returnValue.status_code == 200:
                returnValue.update({ "exit_code": 0 })
                returnValue.update({ "exit_message": "Success" })
            elif (len(returnValue['result']) > 0):
                returnValue.update({ "exit_code": 0 })
                returnValue.update({ "exit_message": "Success" })           
            else:
                returnValue.update({ "exit_code": 2 })
                returnValue.update({ "exit_message": "No Data returned.  Verify valid arguments"})
        except Exception as e:
            returnValue.update({ "exit_code": 2 })
            returnValue.update({ "exit_message": "Error parsing returnValue"})
        return returnValue
        
    def getRITMSysidByNumber(self, RITMNumber: str) -> str:   
        method = "GET"
        reqUrl = "/api/service-now/sc-req-item/" + RITMNumber
        url = urljoin(self._base_url, reqUrl)

        query_params = {}

        payload = ""
        try:

            result = self._makeGetRequest(url, payload, query_params)#response.json()
          
            if (len(result['result']) > 0) :
                returnValue = {
                    "exit_code": 0,
                    "exit_message": "Success",
                    "sys_id": result['result'][0]['sys_id']
                }
            elif result.get("exit_code") is not None:
                returnValue = result #returnVal already populated from the request method
            else:
                returnValue = {
                    "exit_code": -2,
                    "exit_message": "No Data returned, check for valid key"
                }    
            
        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }    
        return returnValue

    def appendRITMWorkNotes(self, sysId: str, workNote: str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/sc-req-item/" + sysId + "/work-notes"
        url = urljoin(self._base_url, reqUrl)

        payload = {
            "sys_id": sysId,
            "work_notes": workNote
        }

        query_params = ""
        try:

            response = self._makePatchRequest(url, payload, query_params) #response.json()            
            returnValue = self.parsereturnValue(response)
         
        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue
    
    def appendRITMAdditionalComments(self, sysId: str, comment: str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/sc-req-item/" + sysId + "/comment"
        url = urljoin(self._base_url, reqUrl)

        payload = {
            "sys_id": sysId,
            "comments": comment
        }

        query_params = ""
        try:

            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)
           
        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue    

    def updateRITMState(self, sysId: str, ritmState: int) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/sc-req-item/" + sysId + "/close"
        url = urljoin(self._base_url, reqUrl)

        if type(ritmState) is not int: 
            returnValue = {
                "exit_code": 1,
                "exit_message": "The RITM state must be passed in as an integer."
            }  
            return returnValue

        payload = {
            "sys_id": sysId,
            "state": ritmState
        }

        query_params = ""
        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

            
        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue    
      
    def getServerCIBySysId(self, sysId: str) -> str:   
        method = "GET"
        reqUrl = "/api/service-now/cmdb-ci-server/" + sysId
        url = urljoin(self._base_url, reqUrl)

        query_params = {
                   }

        payload = ""
        try:
            response = self._makeGetRequest(url, payload, query_params)#response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue

    def queryServerByNameAndClass(self, serverName: str, className: str) -> str:   
        method = "GET"
        reqUrl = "/api/service-now/cmdb-ci-server/" 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
            "sys_class_name": className,
            "name": serverName
        }

        payload = ""
        try:
            response = self._makeGetRequest(url, payload, query_params)#response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue    

    def createServer(self, serverProperties: json) -> str:   
        method = "POST"
        reqUrl = "/api/service-now/cmdb-ci-server" 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payload = json.dumps(serverProperties)
        print(payload)
        try:
            response = self._makePostRequestWithJson(url, serverProperties, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  
        return returnValue            
    
    def updateServerProperties(self, sysId: str, sysClass: str, serverProperties: json) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/cmdb-ci-server/" + sysId
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        serverClass = {
            'sys_class_name' : sysClass
        }

        serverProperties.update(serverClass)

        payload = json.dumps(serverProperties)

        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 

    def changeRequestCreate(self, assignedTo: str, assignedGroup: str, category: str, cmdbCi: str, shortDesc: str) -> str:   
        method = "POST"
        reqUrl = "/api/service-now/change-request/" 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        crProperties = {
            "assigned_to": assignedTo,
            "assignment_group": assignedGroup,
            "category": category,
            "cmdb_ci": cmdbCi,
            "short_description": shortDesc
        }

        payload = json.dumps(crProperties)
        try:
            response = self._makePostRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue            

    def changeRequestAddWorkNote(self, sysId: str, workNotes: str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/change-request/" + sysId + "/work-notes"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payload= {
            'work_notes' : workNotes
        }

        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 

    def changeRequestSchedule(self, sysId: str, startDate: str, endDate: str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/change-request/" + sysId + "/schedule"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payloadJSON = {
            "start_date" : startDate,
            "end_date": endDate
        }

        payload = json.dumps(payloadJSON)
        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 
    
    def changeRequestAddCIs(self, sysId: str, CIs) -> str:
        method = "POST"
        reqUrl = "/api/service-now/change-request/" + sysId + "/affected_cis"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payloadJSON = { # Should be a list of CI sysids in the formation ["sysid", "sysid", ...] 
            "cmdb_ci_sys_ids": CIs
        }

        payload = json.dumps(payloadJSON)

        try:
            response = self._makePostRequest(url, payload, query_params)
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue    

    def changeRequestImplement(self, sysId: str, startDate: str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/change-request/" + sysId + "/implement"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payloadJSON = {
            "work_start" : startDate
        }

        payload = json.dumps(payloadJSON)
        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 

    def changeRequestClose(self, sysId: str, closeCode: str, closeNotes:str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/change-request/" + sysId + "/close"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payload = {
            "close_code": closeCode,
            "close_notes": closeNotes
        }
        
        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 

    def getUserSidByName(self, userName: str) -> str:   
        method = "GET"
        reqUrl = "/api/service-now/sys-user/" 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
            "user_name": userName
        }

        payload = ""
        try:
            response = self._makeGetRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue    

    def getGroupNameBySid(self, sysid: str) -> str:   
        method = "GET"
        reqUrl = "/api/service-now/sys-user-group/" + sysid
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payload = ""

        try:
            response = self._makeGetRequest(url, payload, query_params) 
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue
    
    def getGroupSidByName(self, groupName: str) -> str:   
        method = "GET"
        reqUrl = "/api/service-now/sys-user-group/" 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
            "name": groupName
        }

        payload = ""
        try:
            response = self._makeGetRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue    

    def incidentCreate(self, jsonIncidentData: json) -> str:   
        method = "POST"
        reqUrl = "/api/service-now/incident/" 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payload = json.dumps(jsonIncidentData)
        try:
            response = self._makePostRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue            

    def incidentAddAffectedCIs(self, sysId: str, CIs) -> str:   
        method = "POST"
        reqUrl = "/api/service-now/incident/" + sysId + "/affected-cis"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payloadJSON = {
            "sys_id": sysId,
            "affected_cis": CIs
        }

        payload = json.dumps(payloadJSON)

        try:
            response = self._makePostRequest(url, payload, query_params)
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue    

    def incidentAddWorkNotes(self, sysId: str, workNote: str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/incident/" + sysId + "/work-notes"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payloadJSON = {
            "sys_id": sysId,
            "work_notes": workNote
        }

        payload = json.dumps(payloadJSON)
        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 

    def incidentGetByINCNumber(self, incNumber: str) -> str:   
        method = "GET"
        reqUrl = "/api/service-now/incident/" + incNumber 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payloadJSON = {
        }

        payload = json.dumps(payloadJSON)
        
        try:
            response = self._makeGetRequest(url, payload, query_params)#response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 

    def incidentClose(self, sysId: str, closeCode: str, closeNotes: str) -> str:   
        method = "PATCH"
        reqUrl = "/api/service-now/incident/" + sysId + "/close"
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payloadJSON = {
            "sys_id": sysId,
            "close_code": closeCode,
            "close_notes": closeNotes,
            "u_it_non_conformity_decision": "no",
            "state": 6
        }

        payload = json.dumps(payloadJSON)
        try:
            response = self._makePatchRequest(url, payload, query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue 
    
    def setVariableByURI(self, targetUri: str, value: str) -> str:   
        method = "POST"
        reqUrl = "/api/service-now/callback" 
        url = urljoin(self._base_url, reqUrl)

        query_params = {
        }

        payload = {
            "uri": targetUri,
            "value": value
        }

        try:
            response = self._makePostRequest(url, json.dumps(payload), query_params) #response.json()
            returnValue = self.parsereturnValue(response)

        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue
    
    def getNameFromSysId(self, sys_id: str) -> dict:   
        method = "POST"
        reqUrl = "/api/service-now/lookup/?sys_id=" + sys_id 
        url = urljoin(self._base_url, reqUrl)

        try:
            response = self._makeGetRequest(url, "", "") #response.json()
            returnValue = self.parsereturnValue(response)
            returnValue["result"] = returnValue["result"][0]
        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  
        return returnValue
    
    def updateIncidentPriority(self, incidentNumber = str, urgency = int, impact = int):
        method = "PATCH"
        reqUrl = "/api/service-now/incident/" + incidentNumber
        url = urljoin(self._base_url, reqUrl)

        payload = json.dumps({
            "urgency": urgency,
            "impact": impact
        })

        try:

            response = self._makePostRequest(url, payload, payload) #response.json()            
            returnValue = self.parsereturnValue(response)
         
        except requests.exceptions.HTTPError as err:
            logging.error("SNOW API request failed: %s %s", method, url)
            logging.error(err)
            returnValue = {
                "exit_code": err.errno,
                "exit_message": err
            }  

        return returnValue

    def _makeGetRequest(self, url, payload, query_params):
        retryCount = 0
        
        while retryCount < 5:
            try:
                response = requests.get(url=url, data=payload, headers=self._createHeader(), params=query_params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                time.sleep(5)
                retryCount += 1
        returnVal = {
            "exit_code": 1,
            "exit_message": response.json()
        }
        return returnVal    
    
    def _makePatchRequest(self, url, payload, query_params):
        retryCount = 0
        
        while retryCount < 5:
            try:
                response = requests.patch(url=url, json=payload, headers=self._createHeader(), params=query_params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                time.sleep(5)
                retryCount += 1
        returnVal = {
            "exit_code": 1,
            "exit_message": response.json()
        }
        return returnVal 
                
    def _makePostRequest(self, url, payload, query_params):
        retryCount = 0
        
        while retryCount < 5:
            try:
                response = requests.post(url=url, data=payload, headers=self._createHeader(), params=query_params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                time.sleep(5)
                retryCount += 1
        returnVal = {
            "exit_code": 1,
            "exit_message": response.json()
        }
        return returnVal
    
    def _makePostRequestWithJson(self, url, json_payload, query_params):
        retryCount = 0
        
        while retryCount < 5:
            try:
                response = requests.post(url=url, json=json_payload, headers=self._createHeader(), params=query_params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                time.sleep(5)
                retryCount += 1
        returnVal = {
            "exit_code": 1,
            "exit_message": response.json()
        }
        return returnVal
