import json
import pandas as pd
# import pyodboc
import os
import fitz
import requests
# import psycopg2.extras as extras
import io
import os
# import psycopg2
from pypdf import PdfWriter, PdfReader
import PyPDF2
import string
import sys
import numpy as np
import shutil
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
# from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
import time


#def pdf_forgery(current_folder_path, pdf_input_folder, pdf_output_folder, pdf_process_folder, excel_output_folder):
def pdf_forgery():
    # Load config
    if len(sys.argv) < 2:
        print("Usage: python script.py '<json_string>'")
        sys.exit(1)
    print(sys.argv[1])
    try:
        config = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON input: {e}")
        sys.exit(1)

    # current_dir_pdf = config["current_dir_pdf"]
    # current_folder_path = config["current_folder_path"]
    Current_data_folder = config["current_folder"]
    pdf_for_path_input = config["input_folder"]
    pdf_for_path_output = config["output_folder"]
    pdf_for_path_process = config["process_folder"]
    excel_path_pdf_forgery = config["output_excel"]
#def pdf_forgery(current_folder_path):
#    current_dir_pdf = r"C:\PDF Edit Forgery\NEW"
#    Current_data_folder=r"C:\PDF Edit Forgery\NEW\Current Data"
#    pdf_for_path_output = r"C:\PDF Edit Forgery\NEW\oucurrent_foldertput"
#    pdf_for_path_input = r"C:\PDF Edit Forgery\NEW\input"
#    pdf_for_path_process = r"C:\PDF Edit Forgery\NEW\Process"

    def reset_folder(path):
        try:
            shutil.rmtree(path, ignore_errors=True)
            if not os.path.isdir(path):
                os.makedirs(path)
        except Exception as e:
            print(f"Error creating folder {path}: {e}")
            raise
    reset_folder(pdf_for_path_input)
    reset_folder(pdf_for_path_output)
    reset_folder(pdf_for_path_process)
        
    # Add files from 'Current data' folder to the target folder
    # Add files from 'Current data' folder to the target folder
    try:
        for file in os.listdir(Current_data_folder):
            src_file_path = os.path.join(Current_data_folder, file)

            # Check if the current item is a file
            if os.path.isfile(src_file_path) and file.lower().endswith('.pdf'):
                # Check if file is empty (size = 0)
                if os.path.getsize(src_file_path) == 0:
                    print(f"[SKIPPED] Empty PDF file: {file}")
                    continue
                
                # Check for corruption using PyMuPDF
                try:
                    with fitz.open(src_file_path) as doc:
                        if len(doc) == 0:
                            print(f"[SKIPPED] PDF has 0 pages: {file}")
                            continue
                except Exception as e:
                    print(f"[SKIPPED] Corrupted or unreadable PDF: {file} | Error: {e}")
                    continue
                dest_file_path = os.path.join(pdf_for_path_input, file)
                try:
                    shutil.copy(src_file_path, dest_file_path)
                except Exception as e:
                    print(f"[ERROR] Failed to copy '{file}': {e}")
                print(f"Moved: {file}")
            else:
                print(f"Skipped folder: {file}")

    except Exception as e:
        print(f"Error during file moving: {e}")
    for filename in os.listdir(pdf_for_path_input):
        file_path = os.path.join(pdf_for_path_input, filename)

        # Check if the file is a .zip file
        if filename.endswith(".zip") and os.path.isfile(file_path):
            # Remove the .zip file
            os.remove(file_path)
    # excel_path_pdf_forgery = excel_path_pdf_forgery

    inputpath = pdf_for_path_input
    outputpath = pdf_for_path_output
    path = pdf_for_path_process

    # List of allowed image file extensions
    image_extensions = ('.jpg', '.jpeg', '.gif', '.png', '.jfif')

    # Initialize list to hold error report
    error_report = []

    # Get list of all files in the directory
    file_names = os.listdir(inputpath)

    # Variables to track if PDFs and images are found
    pdf_found = False
    only_images_found = True

    # Loop through the files
    for fnm in file_names:
        file_name = os.path.join(inputpath, fnm)

        # Check if the file is an image
        if file_name.lower().endswith(image_extensions):
            # It's an image, so we mark the image found, but continue
            continue
        # elif os.path.getsize(file_name) == 0:
        #     print(f"[SKIPPED] Empty file: {file_path}")
        #     continue
        elif file_name.lower().endswith('.pdf'):
            # If a PDF is found, we change the flag
            pdf_found = True
            only_images_found = False
        else:
            # If any file is not an image or PDF, we continue without any issue
            file_name=[file for file in file_names if file.endswith(image_extensions)]
            


    # If only images are found and no PDFs, generate an Excel file with error messages
    if only_images_found:
            result = {
                "status": "done",
                "message": "No PDF document is found by the tool."
            }
            cols = ['File_Name', 'Edited_Flag', 'Edited_File_Name', 'Edited_Text']
            base_data = pd.DataFrame(columns=cols)
            base_data.to_pickle(excel_path_pdf_forgery+"/"+"PDF_Edit_Output.pkl")
            print(json.dumps(result))
            sys.exit(0)
        # for fnm in file_names:
        #     if fnm.lower().endswith(image_extensions):

        #         error_report.append(
        #             {"Filename": fnm, "Error": "This module runs on PDFs only, so load at least 1 PDF to run."})

        # base_data = pd.DataFrame(error_report,columns=['Error'])
        # base_data.to_pickle(excel_path_pdf_forgery+'//'+"PDF_Edit_Output.pkl")
        # base_data.to_excel(excel_path_pdf_forgery+'//'+"PDF_Edit_Output.xlsx",index=False)
        #output_excel = os.path.join(inputpath, 'error_report.xlsx')
        #df_error.to_excel(output_excel, index=False)
        #print(f"Error report generated at: {output_excel}")
    else:


        def get_text_percentage(file_name: str) -> float:
            """
            Calculate the percentage of document that is covered by (searchable) text.
            If the returned percentage of text is very low, the document is
            most likely a scanned PDF
            """
            total_page_area = 0.0
            total_text_area = 0.0
            
            try:
                # Open the PDF
                doc = fitz.open(file_name)
            except Exception as e:
                print(f"Error opening file: {e}")

            for page_num, page in enumerate(doc):
                total_page_area = total_page_area + abs(page.rect)
                text_area = 0.0
                for b in page.get_text("blocks"):
                    r = fitz.Rect(b[:4])  # rectangle text appears
                    text_area = text_area + abs(r)
                total_text_area = total_text_area + text_area
            doc.close()
            return total_text_area / total_page_area


        get_text_percentage(file_name)

        def edit_at_end(file_name):
            try:
                # Attempt to open the PDF file
                pdfFileObj = open(file_name, 'rb')
            except FileNotFoundError as e:
                print(f"File not found: {e}")
                return ""
            except Exception as e:
                print(f"Error opening file: {e}")
                return ""

            try:
                # Read the PDF file
                import PyPDF2
                pdfReader = PyPDF2.PdfReader(pdfFileObj)
                pageObj = pdfReader.pages[0]
                string1 = pageObj.extract_text()
            except IndexError as e:
                print(f"Error accessing the first page of the PDF: {e}")
                pdfFileObj.close()
                return ""
            except Exception as e:
                print(f"Error reading or extracting text from PDF: {e}")
                pdfFileObj.close()
                return ""

            # Close the PDF file object
            pdfFileObj.close()

            try:
                # Modify the string by removing specific characters
                string1 = string1.replace("Ix0e", '')

                # Define the output file name
                output_file_name = os.path.join(pdf_for_path_process,os.path.basename(file_name).replace(".pdf", "") + "_aFirst_pypdf.txt")

                # Write the modified string to a text file
                with open(output_file_name, "w", encoding='utf-8') as file1:
                    print(f"PyPDF2 output saved as {output_file_name}")
                    file1.write(string1)
            except Exception as e:
                print(f"Error processing or saving the output text file: {e}")
                return ""

            return string1

        def pure_text(file_name):
            import pandas as pd
            import fitz  # PyMuPDF

            try:
                # Open the PDF
                doc = fitz.open(file_name)
            except Exception as e:
                print(f"Error opening file: {e}")
                return ""

            x1, x2, y1, y2, content = [], [], [], [], []

            try:
                # Extract text blocks and their coordinates
                for page in doc:
                    blocks = page.get_text("blocks")
                    for block in blocks:
                        x1.append(round(block[0], 0))
                        y1.append(round(block[1], 0))
                        x2.append(round(block[2], 0))
                        y2.append(round(block[3], 0))
                        content.append(block[4])
            except Exception as e:
                print(f"Error extracting text from the PDF: {e}")
                return ""

            try:
                # Create a DataFrame with the extracted information
                ndf = pd.DataFrame({
                    'content': content,
                    'x1': x1,
                    'y1': y1,
                    'x2': x2,
                    'y2': y2
                })

                # Filter only string content and remove NaN values
                ndf1 = ndf[ndf['content'].apply(lambda x: isinstance(x, str))]  # Keep only string content
                ndf1 = ndf1[~ndf1['content'].str.contains('<image: ', na=False)]  # Filter out rows with images
                ndf1 = ndf1.reset_index(drop=True)
            except AttributeError as e:
                print(f"Attribute error during DataFrame processing: {e}")
                return ""
            except Exception as e:
                print(f"General error during DataFrame processing: {e}")
                return ""

            try:
                # Sort and concatenate text content for further processing
                return ''.join(ndf1.sort_values(by=['y1', 'x1']).content.tolist())
            except Exception as e:
                print(f"Error sorting or concatenating text: {e}")
                return ""

        pure_text(file_name)


        def high_line_finder(file_name):
            # file_name="C:/Users/Administrator/Documents/img_forgery/PDF Files/degree_26.pdf"
            string1 = edit_at_end(file_name)
            string2 = pure_text(file_name)
            string1 = string1.replace("\n\n", "\n")
            string2 = string2.replace("\n\n", "\n")
            string1 = string1.replace('\t', '\n')
            ##print('string1', string1)
            lines_to_high = []
            ###############edits occur in last line #########################
            editatend = string1
            puretext = string2
            nstring = editatend.replace('\n', '').replace(' ', '')

            for line in puretext.split('\n'):
                if line.replace(' ', '') != '':
                    pos = nstring.find(line.replace(' ', ''))
                    # nstring.insert(pos,'m')
                    if pos != -1:
                        nstring = nstring[:pos] + '~~' + nstring[pos:]
            #            print('\nnstring\n',nstring)
            # 11 - string1.split('\n')
            l1 = nstring.split('~~')
            l2 = string2.split('\n')
            ##print(11)
            ##print(12)
            list1 = []
            list2 = []
            list1 = []
            list2 = []
            for line in l1:
                if len(line) > 0 and line != ' ':
                    list1.append(line)
            for line in l2:
                if len(line) > 0 and line != ' ':
                    list2.append(line)
            print('list1 ', list1)
            print('list2 ', list2)
            ind = len(list2) - int(len(list2) * (85 / 100) - 1)
            if len(list2) < 1:
                ind = len(list2) - int(len(list2) * (85 / 100) - 1)
            if ind > 3:
                tmplist2_90 = list2[:int(len(list2) * (85 / 100) - 1)]
                tmplist2_last10 = list2[int(len(list2) * (85 / 100)):]
            else:
                tmplist2_90 = list2[:3]
                tmplist2_last10 = list2[3:]
            tmp1 = []
            for line in tmplist2_90:
                tmp1.append(''.join(line.split()))
            fullstring2_90 = ''.join(tmp1)
            tmp2 = []
            for line in tmplist2_last10:
                tmp2.append(''.join(line.split()))
            fullstring2_last10 = ''.join(tmp2)

            new_list1 = list1[-3:]  # making list of words > len(4)
            ##print('\n new_list1',new_list1)
            strings_to_find = []
            for i in new_list1:
                line = ''.join(i.split())
                if len(line) > 0:
                    strings_to_find.append(i)
            ##print('\n strings to find "strings_to_find)
            strings_to_high = []  # finding strings to highlight
            ##print('strings_to_find', strings_to_find)
            for string in reversed(strings_to_find):
                # strings_to_high.append(string)
                try:
                    ##print(fullstring2_90.index(string))
                    # print(fullstring2_last10)
                    if string not in fullstring2_last10:
                        strings_to_high.append(string)
                    else:
                        break
                except:
                    a = 1
            # break
            # print('\n strings to high ",strings_to_high)
            # finding lines to highlight in list2
            # break
            # print('\n strings to high ',strings_to_high)
            # finding lines to highlight in list2
            for line in list2:
                for string in strings_to_high:
                    if string in ''.join(line.split()):
                        lines_to_high.append(line)
            print('\nlist2', list2)
            # print('\nlines to high,lines_to_high)
            # ___________________________________________________________________

            return lines_to_high


        # list(set(lines_to_high))
        high_line_finder(file_name)


        def high_n_save(file_name, lines_to_high):
            try:
                # Open the PDF
                doc = fitz.open(file_name)
            except Exception as e:
                print(f"Error opening file: {e}")
            
            

            def highlighter(line):
                for page in doc:
                    ### SEARCH
                    line = line.strip()
                    text_instances = page.search_for(line, quads=True)
                    ### HIGHLIGHT
                    for inst in text_instances:
                        highlight = page.add_highlight_annot(inst)
                        highlight.update()

            ##print(lines_to_high)
            lines_to_high = high_line_finder(file_name)
            for line in lines_to_high:
                highlighter(line)
            # name = file.replace('F:\janjunehighlight\single\l', ")
            doc.save(pdf_for_path_process + '\\' + fnm.replace('._pdf', '') + '_aHighlighted.pdf', garbage=4, deflate=True, clean=True)

            return doc.save(path + '\\' + fnm.replace('._pdf', '') + '_aHighlighted.pdf', garbage=4, deflate=True, clean=True)



        # pages = convert_from_path(r'static/uploads/aHighlighted.pdf')
        # pages[0].save(r'static/uploads/aHighlighted' +'.jpg', 'JPEG')
        # print("Highlighted File Saved as : aHighlighted.pdf")
        # high_n_save(file_name,high_line_finder(file_name))
        # 18
        high_n_save(file_name, high_line_finder(file_name))


        def get_page1(file_name):
            # split saved pdf into multiple pdfs
            ipdf = open(file_name, "rb")
            inputpdf = PdfReader(ipdf)
            file_list = []
            for i in range(len(inputpdf.pages)):
                output = PdfWriter()
                output.add_page(inputpdf.pages[i])
                new_file_name = file_name.replace('*.pdf', '') + '_page' + str(i + 1) + '.pdf'
                with open(new_file_name, "wb") as outputStream:
                    output.write(new_file_name)
                file_list.append(new_file_name)
            return file_list


        get_page1(file_name)


        # get_page1(file_name)
        # 21
        def pdf_highlighter(file_name):
            # file_name get_page1(file_name)
            # file_name="C:/Users/Administrator/Documents/img_forgery/PDF Files/degree_26.pdf"
            lines_to_high = high_line_finder(file_name)
            # ishighlighted= 'no'

            if get_text_percentage(file_name) > 2:  # check if pdf is scanned image

                ishighlighted = 'NO'
                print(ishighlighted)

            if len(lines_to_high) > 0:
                ishighlighted = 'yes'
                print(lines_to_high)
                print(ishighlighted)
                ##print("\n !!!The file is highlighted!!!")
                high_n_save(file_name, lines_to_high)
                # if ishighlighted == 'no':
                #     ##print("\n !!! The file is not highlighted!!!")
                #    shutil.copy(file_name,r'aHighlighted.pdf')
                # print(ishighlighted)
                return [ishighlighted, lines_to_high]


        # pdf_highlighter('high_test.pdf')
        pdf_highlighter(file_name)

        from PyPDF2 import PdfMerger


        def multi_page(file_name):

            file_list = get_page1(file_name)
            ishigh_1st = []
            lines_highlighted = ''
            for file in file_list:
                try:
                    res = pdf_highlighter(file)
                    ishigh_1st.append(res[0])
                    print(res)
                    source_file = path + '\\' + fnm + '_' + 'aHighlighted.pdf'
                    dest_file = path + '\\' + os.path.basename(file).replace('.pdf', '_high.pdf')
                    shutil.copy(source_file, dest_file)

                    if res[1]:
                        stripped_list = [item.strip() for item in res[1]]
                        if lines_highlighted != '':
                            lines_highlighted += '|'
                        lines_highlighted += '|'.join(stripped_list)
                except:
                    ishigh_1st.append('no')
                    shutil.copy(file, path + '\\' + os.path.basename(file).replace('.pdf', '_high.pdf'))

            # Create and instance of PdfFileMerger() class
            merger = PdfMerger()
            for pdf_file in file_list:
                # Append PDF files
                merger.append(pdf_file)
                try:
                    if os.path.isfile(pdf_file.replace('.pdf', '') + '_high.pdf'):
                        os.remove(pdf_file.replace('.pdf', '') + '_high.pdf')
                        os.remove(pdf_file)
                except:
                    x = 1  # use date time library such that the ouput folder is max_loaddt
            # create folder in F: wherein download fldr passed-> output recorded + delete file
            # write out the merged PDF
            ##print('Saving to merged')
            # outfile=os.path.join(output_path,os.path.basename(file_name))
            ##one more change

            # 20

            merger.write(file_name)
            merger.close()
            ishighlighted = 'NO'
            ##print(ishigh_lst)
            if 'yes' in ishigh_1st:
                ishighlighted = 'YES'
                ##print(ishighlighted, outfile)
            return ishighlighted, "", lines_highlighted


        multi_page(file_name)

        os.chdir(pdf_for_path_input)

        files = os.listdir()

        base_data = pd.DataFrame(files, columns=["File_Name"])

        file_nm = list(base_data['File_Name'])

        def process(file_name):
            try:
                # Assuming `multi_page` returns a tuple or list where output[0] determines if the file should be processed
                output = multi_page(file_name)
                print(output[0])

                if output[0] == "YES":
                    pdf_groups = {}

                    # Combine grouping and merging into a single loop
                    for file in os.listdir(pdf_for_path_process):
                        if file.endswith("_high.pdf"):  # Check if the file ends with "_high.pdf"
                            # Get the prefix before "_high.pdf"
                            file_name_before_underscore = file.split('_high.pdf')[0]

                            # Initialize PdfMerger for this group if it's the first file in the group
                            if file_name_before_underscore not in pdf_groups:
                                pdf_groups[file_name_before_underscore] = PdfMerger()

                            # Append the file to the merger for this prefix group
                            full_file_path = os.path.join(pdf_for_path_process, file)
                            print(f"Appending file: {full_file_path}")
                            pdf_groups[file_name_before_underscore].append(full_file_path)

                    # After collecting all files, write each group's merged PDF to disk
                    for prefix, merger in pdf_groups.items():
                        # Define the destination file name
                        new_file_name = f"{prefix}.pdf"
                        dest = os.path.join(pdf_for_path_output, new_file_name)

                        # Write the merged PDF to the destination
                        with open(dest, 'wb') as output_pdf:
                            merger.write(output_pdf)

                        print(f"Merged PDF created: {dest}")

                        # Close the merger to free up resources after writing the output PDF
                        merger.close()

                    # After merging, remove all processed files from pdf_for_path_process
                    for file in os.listdir(pdf_for_path_process):
                        file_path = os.path.join(pdf_for_path_process, file)
                        if os.path.isfile(file_path) and file.endswith("_high.pdf"):
                            os.remove(file_path)
                            print(f"Removed processed file: {file}")

                    # Remove files having text after ".pdf" or files with ".txt" in pdf_for_path_input
                    for file in os.listdir(pdf_for_path_input):
                        # Check if file has text after ".pdf" or is a ".txt" file
                        if (file.endswith(".pdf") and not file == file.split(".pdf")[0] + ".pdf") or file.endswith(
                                ".txt"):
                            file_path = os.path.join(pdf_for_path_input, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                print(f"Removed file: {file}")

                return output[0], output[1], output[2]

            except FileNotFoundError as fnf_error:
                print(f"File not found error: {fnf_error}")
                return '', '', ''

            except PermissionError as perm_error:
                print(f"Permission error: {perm_error}")
                return '', '', ''

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return '', '', ''

        base_data["Edited_Flag"], base_data["Edited_File_Name"], base_data["Edited_Text"] = zip(
            *base_data["File_Name"].apply(process))
        base_data=base_data[(base_data['Edited_Flag']=="YES")]
        if base_data.empty:
            result = {
                "status": "done",
                "message": "No forged document has been identified by the tool."
            }
            cols = ['File_Name', 'Edited_Flag', 'Edited_File_Name', 'Edited_Text']
            base_data = pd.DataFrame(columns=cols)
            base_data.to_pickle(excel_path_pdf_forgery+"/"+"PDF_Edit_Output.pkl")
            base_data.to_excel(excel_path_pdf_forgery+"/"+"PDF_Edit_Output.xlsx")
            print(json.dumps(result))
            sys.exit(0)
            # print("No duplicates found. Creating a message DataFrame.")
            # message_df = pd.DataFrame({"message": ["There are not documents which are forged"]})
            # message_filepath = os.path.join(excel_path_pdf_forgery, "PDF_Edit_Output.xlsx")
            # message_df.to_excel(message_filepath, index=False)

        else:
            base_data.to_pickle(excel_path_pdf_forgery+'//'+"PDF_Edit_Output.pkl")
            base_data.to_excel(excel_path_pdf_forgery+'//'+"PDF_Edit_Output.xlsx")
            time.sleep(5)
            with open(excel_path_pdf_forgery + "//PDF_Edit_Output.pkl", "rb+") as f:
                f.flush()
                os.fsync(f.fileno()) 
            result = {
                "status": "done",
                "message": "Pickle file created successfully."
            }
            print(json.dumps(result))
            # Write the final combined output to Excel
            # Remove or replace illegal characters in string columns
            # def clean_cell(x):
            #     try:
            #         if isinstance(x, str):
            #             # First remove unprintable characters
            #             cleaned = ''.join(c for c in x if c.isprintable())
            #             # Then remove illegal characters (e.g. for Excel)
            #             cleaned = ILLEGAL_CHARACTERS_RE.sub('', cleaned)
            #             return cleaned
            #     except Exception as e:
            #         print(f"Error cleaning value {repr(x)}: {e}")
            #     return x  # Return as-is if not a string or if cleaning fails
            
            # # Apply cleaning function to entire DataFrame
            # base_data = base_data.applymap(clean_cell)
            # base_data.to_excel(excel_path_pdf_forgery+'//'+"PDF_Edit_Output.xlsx",index=False)
           
            valid_files=set(base_data['File_Name'].tolist())
            for file in os.listdir(pdf_for_path_output):
                if file not in valid_files:
                    file_to_delete = os.path.join(pdf_for_path_output, file)
                    try:
                        os.remove(file_to_delete)
                        print(f"Deleted: {file_to_delete}")
                    except Exception as e:
                        print(f"Failed to delete {file_to_delete}: {e}")
        return base_data

#if __name__ == "__main__":
#    pdf_forgery(r"C:\PDF Edit Forgery\NEW\Current Data")


if __name__ == "__main__":
    pdf_forgery()
    result = {
        "status": "done",
        "message": "Python script completed successfully."
    }
    print(json.dumps(result))  # Output JSON string

#if __name__ == "__main__":
#    # Load paths from config.json
#    with open("C:/PDF Edit Forgery/NEW/config.json", "r") as f:
#        config = json.load(f)

 #   pdf_forgery(
 #       current_folder_path=config["current_folder_path"],
  #      pdf_input_folder=config["pdf_input_folder"],
  #      pdf_output_folder=config["pdf_output_folder"],
  #      pdf_process_folder=config["pdf_process_folder"],
   #     excel_output_folder=config["excel_output_folder"]
#    )
#pdf_forgery(r'C:\Users\rahul.buttan\OneDrive - Protiviti Member Firm\Documents\Maruti\Dev\your_flask_app\Current data')


