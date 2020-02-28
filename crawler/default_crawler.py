import logging
import os
import json
import time


import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from util.web_util import webUtil


class defaultCrawler():

    """
    accounts_balance_inquiry : 금융기관별 계정과목별조회(잔액) url
    accounts_maturity_inquiry : 금융기관별 계정과목별 조회(만기구조) url
    credit_exposure_inquiry : 종합신용공여 조회 url
    """

    base_url = "https://kicpa.kisline.com"
    login_page_url = "/cm/CM0100M002GE.nice"
    login_request_url = "/cm/CM0100M003PR.nice"
    pdf_post_url = "/cm/CM0300M003OZ.nice"
    accounts_balance_inquiry = "/gc/GC0200M006GE.nice"
    accounts_maturity_inquiry = "/gc/GC0200M007GE.nice"
    credit_exposure_inquiry = "/gc/GC0200M002GE.nice"

    inquiry_dict = {
        "accounts_balance" : accounts_balance_inquiry,
        "accounts_maturity" : accounts_maturity_inquiry,
        "credit_exposure" : credit_exposure_inquiry
    }

    mapping_inquiry_dict = {
        "accounts_balance" : "금융기관별 계정과목별 조회(잔액)",
        "accounts_maturity" : "금융기관별 계정과목별 조회(만기구조)",
        "credit_exposure" : "종합신용공여 조회"
    }


    # pandas column 순서를 위한 dictionary

    mapping_inquiry_index = {
        "accounts_balance" : 4,
        "accounts_maturity" : 5,
        "credit_exposure" : 6,
    }

    login_id = 'samil06'
    login_password = '!rlaeotlr1'
    user_agent = UserAgent()

    def __init__(self, base_date, logger_class=None):
        self.base_date = base_date
        self.web_util = webUtil(logger_class)
        self.logger = logger_class.get_logger()
        self.current_process_url = None
        self.session = None

    def _concatenate_url(self, url):
        return self.base_url + url


    def _set_default_header(self):
        header = {
            "User-Agent": str(self.user_agent.chrome),
            "Connection": "keep-alive",
            "Host" : "kicpa.kisline.com",
            "Accept-Encoding" : "gzip, deflate, br",
        }
        return header

    def _set_pdf_parameters(self, bizno=None, base_date=None, act_nm=None):
        if bizno is None or base_date is None or act_nm is None:
            raise ValueError("올바른 값을 입력해주세요") 

        # default 값 세팅
        parameters = {
            "rptDivCd" : "OZFBGC",
            "gctslctfrmdivcd" : "pdf",
        }

        parameters["bizno"] = bizno
        parameters["baseDate"] = base_date
        parameters["actNm"] = act_nm
        
        return parameters

    
    def _set_excel_parameters(self, bizno=None, base_date=None):
        if bizno is None or base_date is None:
            raise ValueError("올바른 값을 입력해주세요") 

        # default 값 세팅
        parameters = {
            "gctslctfrmdivcd" : "EXL",
        }

        parameters["bizno"] = bizno
        parameters["baseDate"] = base_date

        return parameters

    def _set_inquiry_parameters(self, bizno=None, base_date=None):
        parameters = {
            "selectCategory" : "Monthly"
        }

        parameters["bizno"] = bizno
        parameters["baseDate"] = base_date

        return parameters

    def _login(self):
        data = {
            "loginid" : self.login_id,
            "loginpwd" : self.login_password,
        }

        header = self._set_default_header()
        url = self._concatenate_url(self.login_request_url)
        session, response = self.web_util.no_exception_post(url=url,isReturnSession=True, data=data, headers=header)
        
        self._login_check(session, response)

        return session, response

    def _login_check(self, session, response):
        if session.cookies["JSESSIONID"][-5:] != "red01" and response.text.find("SUCCESS") == -1:
            self.logger.error("Login error")
            raise ValueError("incorrect login information")

    def _session_check(self):
        if self.session.cookies["JSESSIONID"][-5:] != "red01":
            self.logger.error("session error")
            return False
        else:
            return True

    def _information_inquiry(self, url, bizno):
        parameters = self._set_inquiry_parameters(bizno=bizno, base_date=self.base_date)
        headers = self._set_default_header()
        return self.web_util.no_exception_post(url=url, data=parameters, session=self.session, isReturnSession=True, headers=headers)

    def _check_information_valid(self, response, action):
        try:
            soup = bs(response.text, 'lxml')

            table_element = soup.find_all("table", class_='tablest_01')[1]

            td_list = table_element.find_all('td')
            
            company_name = td_list[0].text.strip()
            login_id = td_list[2].find('span').text.strip()
            updated_date = td_list[4].text.strip()
            inquiry_time = td_list[5].text.strip()

            if len(company_name) == 0:
                if  len(updated_date) == 0 or len(inquiry_time) == 0 or login_id != self.login_id:
                    return False
                else:
                    self.logger.warning(f"{action}\n존재하지만 조회된 내역은 없습니다.")
                    return True
            else:
                return True
        except IndexError:
            raise AttributeError
        
    def _parsing_action(self,url):
        return url[4:16]

    """
    Parameters
    
    """
    def get_excel_file(self, data):
        data_length = len(data[:, 0])
        
        self.session, _ = self._login() 
        url = self._concatenate_url(self.pdf_post_url)
        
        for i in range(data_length):

            company_name = data[i, 0]
            bizno = data[i, 1]
            department = data[i, 2]
            director_name = data[i, 3]


            for key in self.inquiry_dict.keys():
                current_process = self.mapping_inquiry_dict[key]
                self.current_process_url = self.inquiry_dict[key]

                action_index = self.mapping_inquiry_index[key]

                file_name = f'{company_name}_{self.base_date[:6]}_{current_process}.xls'
                file_location = os.path.join(os.getcwd() + "/excel_file", department, self.base_date[:6], director_name, company_name, file_name)
                self.current_process_url = self.inquiry_dict[key]
                action = f'{department}/{director_name}/{bizno}-{company_name}의 {self.base_date} {current_process} excel file download'
                
                # 현재 파일이 있음
                if os.path.exists(file_location):
                    log_str = action + "\n이미 존재하는 file으로 skip"
                    self.logger.info(log_str)
                    data[i,action_index] = 'O'
                    continue

                url = self._concatenate_url(self.current_process_url)
                parameters = self._set_excel_parameters(bizno=bizno, base_date=self.base_date)
                headers = self._set_default_header()
                headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
                headers["Content-Type"] = "application/x-www-form-urlencoded"

                self.session, response = self._information_inquiry(url, bizno)

                try:
                    if not self._check_information_valid(response, action):
                        if self._session_check():
                            raise AttributeError("데이터 에러")
                        else:
                            raise ConnectionError("로그인 에러")
                    
                    self.session, response = self.web_util.no_exception_post(url=url, data=parameters, session=self.session, isReturnSession=True, headers=headers, action=action)

                    if "text/html" in response.headers["Content-Type"]:
                        if self._session_check():
                            raise AttributeError("데이터 에러") 
                        else:
                            raise ConnectionError("로그인 에러")
                    
                    # 경로가 만들어졌는 지 여부 확인 및 생성
                    if not os.path.exists(os.path.dirname(file_location)):
                        os.makedirs(os.path.dirname(file_location))

                    with open(file_location, 'wb') as f:
                        f.write(response.content)
                        data[i,action_index] = 'O'

                except (ConnectionError, ConnectionResetError):
                    self.session.close()
                    log_str = action + f'실패\n로그인 재시도\n'
                    self.logger.error(log_str)
                    self.session, _ = self._login()
                    continue                
                except (AttributeError, IndexError):
                    if not self._session_check():
                        self.session.close()
                        log_str = action + f'실패\n로그인 재시도\n'
                        self.logger.error(log_str)
                        self.session, _ = self._login()
                    log_str = action + f'실패\nParameters를 확인하세요\n'
                    self.logger.critical(log_str)
                    continue

        self.session.close()
        return data
        

    """
    2번의 for-loop 

    1. input data로부터 필요한 정보를 얻는다. (사업자번호, 담당이사, 담당본부, 회사이름)
    2. input data에 대한 validation check(사업자번호 : 10자리 / 이외 데이터는 들어가 있으면 True) 
    3. 3가지 월보를 다운 받기위해 for-loop 
    4. 각 loop 당 download를 위해서 request를 보내고 validation check
        -> 사업자번호가 10자리라도 올바른 사업자번호가 아닐 경우가 있음. 
    5. 성공적으로 pdf downlaod

    """
    def get_pdf_file(self, data):
        data_length = len(data[:, 0])
        
        self.session, _ = self._login() 
        url = self._concatenate_url(self.pdf_post_url)
        
        for i in range(data_length):

            company_name = data[i, 0]
            bizno = data[i, 1]
            department = data[i, 2]
            director_name = data[i, 3]

            # parameter validation check : 사업자번호 10자리 / 나머지 값들은 len
            if  len(bizno) != 10 or len(company_name) <= 0 or len(director_name) <= 0 or len(department) <= 0:
                log_str = f'{department}/{director_name}/{bizno}-{company_name}의 {self.base_date} download 실패'
                self.logger.critical(log_str)
                continue

            for key in self.inquiry_dict.keys():

                action_index = self.mapping_inquiry_index[key]
                current_process = self.mapping_inquiry_dict[key]
                file_name = f'{company_name}_{self.base_date[:6]}_{current_process}.pdf'
                file_location = os.path.join(os.getcwd() + "/pdf_file", department, self.base_date[:6], director_name, company_name, file_name).replace(' ', '_')

                self.current_process_url = self.inquiry_dict[key]
                inquiry_url = self._concatenate_url(self.current_process_url) # 조회를 위한 url

                action = f'{department}/{director_name}/{bizno}-{company_name}의 {self.base_date} {current_process} pdf file download'


                # 현재 파일이 있음


                if os.path.exists(file_location):
                    log_str = action + "\n이미 존재하는 file으로 skip"
                    self.logger.info(log_str)
                    data[i,action_index] = 'O'
                    continue

                pdf_action = self._parsing_action(self.current_process_url)
                parameters = self._set_pdf_parameters(bizno, self.base_date, pdf_action)
                headers = self._set_default_header()


                self.session, response = self._information_inquiry(inquiry_url, bizno)

                try:
                    if not self._check_information_valid(response, action):
                        if self._session_check():
                            raise AttributeError("데이터 에러")
                        else:
                            raise ConnectionError("로그인 에러")
                        continue


                    self.session, response = self.web_util.no_exception_post(url=url, data=parameters, session=self.session, isReturnSession=True, headers=headers, action=action)

                    # login error 혹은 parameter validation error (날짜형식 or 사업자번호 10자리)
                    if "text/html" in response.headers["Content-Type"]:
                        if not self._session_check():
                            raise ConnectionError("로그인 에러")
                        else:
                            raise AttributeError("데이터 에러")
                    

                    # 경로가 만들어졌는 지 여부 확인 및 생성
                    if not os.path.exists(os.path.dirname(file_location)):
                        os.makedirs(os.path.dirname(file_location))

                    # 파일 write
                    with open(file_location, 'wb') as f:
                        f.write(response.content)
                        data[i,action_index] = 'O'
                # ConnectionError 
                # 재로그인 시도
                except (ConnectionError, ConnectionResetError):
                    self.session.close()
                    log_str = action + f'실패\n로그인 재시도\n'
                    self.logger.error(log_str)
                    self.session, _ = self._login()
                    continue                
                except (AttributeError, IndexError):
                    log_str = action + f'실패\nParameters를 확인하세요\n'
                    self.logger.critical(log_str)
                    continue

        self.session.close()

        return data