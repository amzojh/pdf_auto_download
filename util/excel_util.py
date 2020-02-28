import os
import fnmatch

import pandas as pd
 
class excelHandler():
    
    def __init__(self, file_location, log_class):
        file_name = os.path.basename(file_location)
        self.file_name = file_name
        self.file_dir = os.path.dirname(file_location)
        self.logger = log_class.get_logger()
        self.data_set = None
        if fnmatch.fnmatch(file_name, '*.xlsx') or fnmatch.fnmatch(file_name, '*.xls'):
            self.data_set = self._read_excel_data(file_location)

    def _read_excel_data(self, file_location):
        excel_data = pd.read_excel(io=file_location, sheet_name="신용공여정보", header=0)
        return excel_data

    def _parsing_parameters(self, data):
        return data.astype('str').str.strip().str.split().str.join('')

    def get_task_list(self):
        if self.data_set is None:
            raise EOFError("file read failure")

        data_set = self.data_set[["회사명", "사업자등록번호", "본부명", "담당이사", "금융기관별 계정과목별조회(잔액)", "금융기관별 계정과목별 조회(만기구조)", "종합신용공여 조회"]]
        data_set["사업자등록번호"] = data_set["사업자등록번호"].astype('str').str.replace('-', '')
        data_set["회사명"] = self._parsing_parameters(data_set["회사명"])
        data_set["사업자등록번호"] = self._parsing_parameters(data_set["사업자등록번호"])        
        data_set["담당이사"] = self._parsing_parameters(data_set["담당이사"])        
        data_set["본부명"] = self._parsing_parameters(data_set["본부명"])        
        data_set["금융기관별 계정과목별조회(잔액)"] = self._parsing_parameters(data_set["금융기관별 계정과목별조회(잔액)"])
        data_set["금융기관별 계정과목별 조회(만기구조)"] = self._parsing_parameters(data_set["금융기관별 계정과목별 조회(만기구조)"])
        data_set["종합신용공여 조회"] = self._parsing_parameters(data_set["종합신용공여 조회"])
        data_set["pdf병합여부"] = self._parsing_parameters(data_set["종합신용공여 조회"])

        return data_set.values

    def write_result_to_excel_sheet(self, result_data):

        self.data_set.loc[:,"금융기관별 계정과목별조회(잔액)"] = list(result_data[:,4])
        self.data_set.loc[:,"금융기관별 계정과목별 조회(만기구조)"] = list(result_data[:,5])
        self.data_set.loc[:,"종합신용공여 조회"] = list(result_data[:,6])


        file_path = os.path.join(self.file_dir, "result_" + self.file_name)
        with pd.ExcelWriter(file_path) as f:
            self.data_set.to_excel(f, 'Sheet1')
            f.save()
        