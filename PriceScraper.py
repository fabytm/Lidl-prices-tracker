import os
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import requests
import urllib.request
import datetime
import json
import camelot
import spreadsheet


current_timestamp = datetime.datetime.now()

current_date = current_timestamp.strftime("%d-%m-%Y")


def get_html(url):  # gets html from url given
    html = requests.get(url)
    content = html.content
    return BeautifulSoup(content, "html.parser")


def get_column_range(nr_of_rows, nr_of_cols):
    if nr_of_cols <= 26 :
        return '{col_i}{row_i}:{col_f}{row_f}'.format(
            col_i = chr((nr_of_cols - 1) + ord('A')),  # converts number to letter
            col_f = chr((nr_of_cols - 1) + ord('A')),  # subtract 1 because of 0-indexing
            row_i = 1,
            row_f = nr_of_rows)
    elif nr_of_cols <= 676 :
        return '{col_i}{col_ii}{row_i}:{col_f}{col_ff}{row_f}'.format(
            col_i = chr(int((nr_of_cols - 1) / 26 - 1) + ord('A')),  # converts number to letter
            col_ii = chr(int((nr_of_cols - 1) % 26) + ord('A')),
            col_f = chr(int((nr_of_cols - 1)/ 26 - 1) + ord('A')),  # subtract 1 because of 0-indexing
            col_ff = chr(int((nr_of_cols - 1) % 26) + ord('A')),  # subtract 1 because of 0-indexing
            row_i = 1,
            row_f = nr_of_rows)


todays_url = "https://endpoints.lidl-flyer.com/v1/preturile-valabile-astazi-" + current_date + "/flyer.json"

print(todays_url)

lidl_page_json = get_html(todays_url)

pdf_url = json.loads(str(lidl_page_json))['flyer']['pdfUrl']

print(pdf_url)


header = urllib.request.Request(pdf_url, headers = {'User-Agent': 'Mozilla/5.0'})
pdf = requests.get(pdf_url)

if not os.path.exists("PDF"):
    os.mkdir("PDF")
    print("Folder PDF created.")

with open('PDF/currentPDF.pdf', "wb") as file:
    file.write(pdf.content)

tables = camelot.read_pdf('PDF/currentPDF.pdf', pages="all")
# tables.export("test.csv", f='csv')
sheet = spreadsheet.get_sheet('LidlPriceTracking.json','sheetID.txt')


sheet_data = sheet.get_all_values()
sheet_product_col = sheet.col_values(1)   # extract first column - product names
sheet_quantity_col = sheet.col_values(2)  # extract second column - quantity - for products that share the same name
sheet_date_row = sheet.row_values(1)

rows_populated = len(sheet_product_col)
cols_populated = len(sheet_date_row)

to_append_list = []
todays_prices = []

print(rows_populated)
print(cols_populated)
print(get_column_range(rows_populated,cols_populated))

if sheet.row_values(1)[cols_populated - 1] != current_date:
    cols_populated += 1
    sheet.update_cell(1, cols_populated, current_date)

prices_list = sheet.range(get_column_range(rows_populated, cols_populated))

for sublist in tables:
    for product in sublist.data:
        if product[0] != '':
            if sheet_product_col.count(product[0]) == 1:
                prices_list[sheet_product_col.index(product[0])].value = product[3]
            elif sheet_product_col.count(product[0]) > 1:
                same_product_list = [[product_name, quantity, index] for index, (product_name, quantity) in enumerate(zip(sheet_product_col, sheet_quantity_col)) if product_name == product[0]]
                for item in same_product_list:
                    if item[1] == product[1]:
                        prices_list[item[2]].value = product[3]
            else:
                formatted_list = []
                formatted_list.append(product[0])
                formatted_list.append(product[1])
                formatted_list.append(product[2])
                for _ in range(cols_populated - 4):
                    formatted_list.append("-")
                formatted_list.append(product[3])
                print(formatted_list)
                to_append_list.append(formatted_list)
print(prices_list)


sheet.append_rows(to_append_list)
sheet.update_cells(prices_list)
