import json
import logging
import requests
import time
from urllib.parse import urljoin
import urllib3
urllib3.disable_warnings()


ANSIBLE_DEV_URL=''
ANSIBLE_PROD_URL=''
#ansible ping template  id 244, 
#limit field is csv of server names
#instance is environment 

class mycmop_ansible:
    
    def __init__(self, xauthKey:str, environment= "development", username="", password=""):
        
        self.xuthKey = xauthKey
        self.environment = environment
        
        if self.environment == "production":
            self.base_url = ANSIBLE_PROD_URL
            self.instance = "production"
        else:
            self.base_url = ANSIBLE_DEV_URL
            self.instance = "Development"
        
        self.parameters = {}
        
    def _createHeader(self):
        header = {
            "Accept": "application/json",
            "x-functions-key": self.xuthKey,
            "Content-Type": "application/json",
            "instance": self.instance,            
        }
        
        return header
    
    def verifyPayload(self, payload):#1 success, 0 failure
        if not payload:
            return [0, "empty payload"]
        
        if payload.get("inventory") is not None:
            if type(payload["inventory"]) is not int:
                return [1, "inventory must be an integer"]
            
        if payload.get("limit") is not None:
            if type(payload["limit"]) is not str:
                return [1, "limit must be a string"]

        if payload.get("scm_branch") is not None:
            if type(payload["scm_branch"]) is not str:
                return [1, "scm_branch must be a string"]

        if payload.get("job_type") is not None:
            if type(payload["job_type"]) is not str:
                return [1, "job_type must be a string"]

        if payload.get("job_tags") is not None:
            if type(payload["job_tags"]) is not str:
                return [1, "job_tags must be a string"]

        if payload.get("verbose") is not None:
            if type(payload["verbose"]) is not int:
                return [1, "verbose must be an integer"]

        if payload.get("credential") is not None:
            if type(payload["credential"]) is not int:
                return [1, "credential must be an integer"]

        if payload.get("execution_environment") is not None:
            if type(payload["execution_environment"]) is not int:
                return [1, "execution_environment must be an integer"]

        if payload.get("labels") is not None:
            if type(payload["labels"]) is not str:
                return [1, "labels must be an string"]

        if payload.get("forks") is not None:
            if type(payload["forks"]) is not int:
                return [1, "forks must be an integer"]
        
        if payload.get("job_slice_count") is not None:
            if type(payload["job_slice_count"]) is not int:
                return [1, "job_slice_count must be an integer"]
        
        if payload.get("timeout") is not None:
            if type(payload["timeout"]) is not int:
                return [1, "timeout must be an integer"]
        
        if payload.get("instance_groups") is not None:
            if type(payload["instance_groups"]) is not int:
                return [1, "instance_groups must be an integer"]
        
        if payload.get("extra_vars") is not None:
            if type(payload["extra_vars"]) is not str:
                return [1, "extra_vars must be a string"]
            try:
                json_dict = json.loads(payload.get("extra_vars"))
            except:
                return [1, "extra_vars is not properly formatted JSON"]
            
        return [0, "passed"]
        

    def getTemplateId(self, template_name:str):
        url = "/api/ansible/job-templates/"
        url = urljoin(self.base_url, url)
        returnDict = {}
        method = "GET"
        data = {"name": template_name}
        try:
            response = requests.request(method, url, params=data, headers=self._createHeader())
            response.raise_for_status()
            if len(response.json().get('results', [])) < 1:
                returnDict["exit_code"] = 1
                returnDict["exit_message"] = "Ansible API returned empty results"
            elif response.json()['results'][0].get('id', None) is None:
                returnDict["exit_code"] = 1
                returnDict["exit_message"] = "No template id found on response data"
            else:
                returnDict["exit_code"] = 0
                returnDict["exit_message"] = response.json()['results'][0].get('id')                        
        except requests.exceptions.HTTPError as e:
            logging.error("Ansible API failed: %s %s", method, url)
            logging.error(e)
            returnDict["exit_code"] = 1
            returnDict["exit_message"] = e
        return returnDict

    def launchTemplate(self, template_id:int, payload:dict={}): #1 success, 0 fail
        returnDict = {}
        payloadResult = self.verifyPayload(payload)
        
        if payloadResult[0]:
            #fail
            returnDict["exit_code"] = 1
            returnDict["exit_message"] = payloadResult[1]
            return returnDict
        
        url = "/api/ansible/job-templates/"+ str(template_id) + "/launch"
        url = urljoin(self.base_url, url)
        method = "POST"
        try:
            response = self._makePostRequest(url, payload)#requests.request(method, url, headers=self._createHeader(), json=payload, verify=False)
            # response.raise_for_status()
            if response.get("exit_code") == 1:
                raise(response.get("exit_message"))
            else:
                response = response.get("exit_message")
            returnDict["exit_code"] = 0
            # print(response.json())
            returnDict["exit_message"] = response
        except Exception as e:
            logging.error("Ansible API failed: %s %s", method, url)
            returnDict["exit_code"] = 1
            returnDict["exit_message"] = e
            logging.error(e)
        time.sleep(2) #this is incase job_id is called before job data is populated in ansible
        return returnDict

    def launchTemplate_execute_and_wait(self, template_id:int, payload:dict={}):
        returnDict = {}
        payloadResult = self.verifyPayload(payload)
        
        if payloadResult[0]:
            #fail
            returnDict["exit_code"] = 1
            returnDict["exit_message"] = payloadResult[1]
            return returnDict
        
        url = "/api/ansible/job-templates/"+ str(template_id) + "/launch"
        url = urljoin(self.base_url, url)
        method = "POST"
        
        try:
            response = self._makePostRequest(url, payload)#requests.request(method, url, headers=self._createHeader(), json=payload , verify=False)
            # response.raise_for_status()
            # print(response)
            if response.get("exit_code") == 1:
                raise(response.get("exit_message"))
            else:
                result = response.get("exit_message")
            job_id = result.get("id")
            time.sleep(2)
            response = self.checkJobStatus(job_id)["exit_message"]
            # print(response)
            while(response["status"] == "running" or response["status"] == "pending" or response["status"] == "waiting"):
                # print(response["status"])
                time.sleep(10)
                response = self.checkJobStatus(job_id)["exit_message"]
            # print("finished: \n")  
            returnDict["exit_code"] = 0
            returnDict["exit_message"] = response
            result = returnDict
        except Exception as e:
            logging.error("Ansible API failed: %s %s", method, url)
            logging.error(e)
            returnDict["exit_code"] = 1
            returnDict["exit_message"] = e
            result = returnDict
        
        # time.sleep(2)
        return returnDict
    
    def checkJobStatus(self, job_id):
        returnDict = {}
        url = "/api/ansible/jobs/" + str(job_id) #+ "/stdout"
        url = urljoin(self.base_url, url)
        method = "GET"
        
        payload = {
            "job_id": job_id,
            "instance": self.environment
        }

        try:
            response = self._makeGetRequest(url)#requests.request(method, url, headers= self._createHeader())
            # response.raise_for_status()
            if response.get("exit_code") == 1:
                raise(response.get("exit_message"))
            else:
                response = response.get("exit_message")
            returnDict["exit_code"] = 0
            returnDict["exit_message"] = response
        except Exception as e:
            logging.error("Failed getting job status: %s %s", method, url)
            logging.error(e)
            returnDict["exit_code"] = 1
            returnDict["exit_message"] = e
        return returnDict

    def _makeGetRequest(self, url):
        retryCount = 0

        while retryCount < 5:
            try:
                response = requests.get(url=url,headers=self._createHeader())
                response.raise_for_status()
                # print(response.json())
                returnVal = {
                    "exit_code": 0,
                    "exit_message": response.json()
                }
                returnVal
                return returnVal
            except Exception as e:
                # print(e)
                time.sleep(5)
                retryCount += 1
                returnVal = {
                    "exit_code": 1,
                    "exit_message": e
                }
        return returnVal    

    def _makePostRequest(self, url, payload):
        retryCount = 0
        
        while retryCount < 5:
            try:
                response = requests.post(url=url,headers=self._createHeader(), json=payload, verify=False)
                response.raise_for_status()
                returnVal = {
                    "exit_code": 0,
                    "exit_message": response.json()
                }
                # print(response.json())
                return returnVal
            except Exception as e:
                # print(e)
                time.sleep(5)
                retryCount += 1
                returnVal = {
                    "exit_code": 1,
                    "exit_message": e
                }
        return returnVal
