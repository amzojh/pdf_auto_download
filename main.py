import sys
import datetime
import argparse

from crawler.default_crawler import defaultCrawler
from logger.deafult_logger import defaultLogger
from util.web_util import webUtil
from util.excel_util import excelHandler
from util.pdf_util import pdfHandler

"""
    월보 다운로드 자동화 프로그램 개요
    util.web_util.webutil : GET, POST, DELETE, PUT등 웹에 request를 보내고 session관리를 위한 클래스
    util.excel_util.excelHandler : input file 및 output file을 핸들링하기 위한 클래스
    util.pdf_util.pdfHandler : PDF file을 핸들링하기 위한 클래스 (pdf merge)
    logger.deafult_logger.defaultLogger : logging을 위한 클래스
    crawler.default_crawler.defaultCrawler : 신용공여사이트를 크롤링하는 로직이 구현되어 있는 클래스

    PARAMATER 설명
    -p --excelpath : 사업자번호가 저장된 엑셀파일의 경로
    -d --date : 월보를 조회할 기준연월일(형식 : YYYYMMDD 예 : 20180101)
    -m --merge : 다운로드 받은 pdf file merge여부

    사용법
    $)월보다운로드.exe -p excel_path -d date --merge

    예시
    $)월보다운로드.exe -p C:/OJH/RPA/Project/RPA-Project-inquiry-credit-exposure/월보조회리스트_TEST_20190109.xlsx -d 20180101 --merge

"""

def main():
    logger_credit_exposure = defaultLogger()
    
    arg_num = len(sys.argv[1:])

    excel_file_path = None
    base_date = None
    isMerge = None
    
    if arg_num == 0:
        raise ValueError("엑셀파일 경로를 입력해주세요.")
    elif arg_num == 1:
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year

        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        
        base_date = f'{year}{month:02}01'
        logger_credit_exposure.logger.warning(f"기준일자가 입력되지 않아 자동으로 전월도인 {year}/{month:02}기준 월보를 다운로드합니다.")
    elif arg_num == 2:
        base_date = sys.argv[2]
    
    elif arg_num == 3:
        isMerge = sys.argv[3]
        base_date = sys.argv[2]
    else:
        raise ValueError("너무 많은 인수를 입력하셨습니다.")


    excel_file_path = sys.argv[1] 

    excel_handler = excelHandler(excel_file_path, logger_credit_exposure)
    tasks = excel_handler.get_task_list()

    crawler_credit_exposure = defaultCrawler(base_date,logger_credit_exposure)
    result_data = crawler_credit_exposure.get_pdf_file(tasks)
    excel_handler.write_result_to_excel_sheet(result_data)

    if isMerge is not None:
        pdf_handler = pdfHandler(logger_credit_exposure)
        pdf_handler.merge_pdf(result_data, base_date)

if __name__ == "__main__":
    main()