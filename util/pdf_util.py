import os
from PyPDF2 import PdfFileMerger, PdfFileReader

class pdfHandler():

    file_list = [
        "종합신용공여 조회",
        "금융기관별 계정과목별 조회(잔액)",
        "금융기관별 계정과목별 조회(만기구조)",
    ]

    def __init__(self, logger_class):
        self.logger_class = logger_class
        self.logger = logger_class.get_logger()
        pass


    # "accounts_balance" : "금융기관별 계정과목별조회(잔액)",
    # "accounts_maturity" : "금융기관별 계정과목별 조회(만기구조)",
    # "credit_exposure" : "종합신용공여 조회"

    def merge_pdf(self, data, base_date):
        data_length = len(data[:, 0])

        for i in range(data_length):

            company_name = data[i, 0]
            bizno = data[i, 1]
            department = data[i, 2]
            director_name = data[i, 3]

            accounts_balance = data[i, 4]
            accounts_maturity = data[i, 5]
            credit_exposure = data[i, 6]

            action = f'\n{department}/{director_name}/{bizno}-{company_name}의 {base_date} pdf 병합'


            if accounts_balance != 'O' or accounts_maturity != 'O' or credit_exposure != 'O':
                log_str = action + "실패\n"
                self.logger.warning(log_str)
                continue

            file_location = os.path.join(os.getcwd() + "/pdf_file", department, base_date, director_name, company_name).replace(' ', '_')

            pdf_merger = PdfFileMerger()
            try:
                for file_name in self.file_list:
                    file_path = os.path.join(file_location, f'{company_name}_{base_date}_{file_name}.pdf').replace(' ', '_')
                    tmp_file_path = os.path.join(file_location, f'{company_name}_{base_date}_{file_name}_tmp.pdf').replace(' ', '_')
                    
                    pdf_file_object = open(file_path, 'rb')
                    pdf_file = PdfFileReader(pdf_file_object)
                    if pdf_file.isEncrypted:
                        try:
                            pdf_file.decrypt('')
                        except:
                            cmd_command = f"qpdf --decrypt \"{file_path}\" \"{tmp_file_path}\" "
                            os.system(cmd_command)
                            pdf_file_object.close()
                            pdf_file_object = open(tmp_file_path, 'rb')
                            pdf_file = PdfFileReader(pdf_file_object)
                    
                    pdf_merger.append(pdf_file)
                    pdf_file_object.close()
                    os.remove(tmp_file_path)

                output_file_path = os.path.join(file_location, f'{company_name}_{base_date}_종합.pdf')
                pdf_merger.write(output_file_path)
            except:
                self.logger.warning(f"\n{action} 병합실패\n")
                continue    
                
