import os
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import sys
import pandas as pd
import statistics
import json
from datetime import datetime
from collections import Counter

no_risk_modules=[]
reference_modules=[]
zero_risk_modules=[]
total_modules_data=set()
directory=os.getcwd()
f_count=0
count=0
previous_count=0
current_count=0
my_dict = defaultdict(list)
final_list=[]
my_dict_to_list=[]
file_storage=[]
def count_occurrences_2d_list(lst):
    record_count = {}

    # Count occurrences of each record
    for record in lst:
        record_tuple = tuple(record)  # Convert list to tuple to make it hashable
        if record_tuple in record_count:
            record_count[record_tuple] += 1
        else:
            record_count[record_tuple] = 1
    return record_count
def add_to_dict(key, value,count):
    if len(my_dict[key]) < count-1:
        while(len(my_dict[key]) < count-1):
            my_dict[key].append(0)
    my_dict[key].append(value)
def calcuate_statistics(numbers):
    mean = round(statistics.mean(numbers),3)
    stdev = round(statistics.stdev(numbers),3)
    variance = round(statistics.variance(numbers),3)
    cv=round((stdev / mean if mean != 0 else 0),3)

    return [mean, stdev, variance,cv]


def get_file_count(path, f_count):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.html'):
                f_count+=1
    return f_count
# def validate_files(dir):
#     with open(state_file,'r') as f:
#         file_storage=json.load(f).get("List_of_Files")
#     print(file_storage)
#     flg=0
#     for root, dirs, files in os.walk(directory):
#         for file in files:
#             if file.endswith('.html') and file not in file_storage:
#                 file_storage.append(file)
#                 flg=1
#     update_json(dir,file_storage)
#     if flg==1:
#         return True
#     else :
#         return False
#
# def update_json(dir,file_storage):
#     with open(state_file,'w') as f:
#         json.dump({"List_of_Files":file_storage},f)
#     print(">> Json updated with File names")
#


def check_dir_for_new_entries(state_file):
    if os.path.exists(state_file) and os.path.getsize(state_file)>0:
        with open(state_file, "r") as f:
            previous_count=json.load(f).get('file_count',0)
            print(previous_count)
            current_count=get_file_count(os.path.join(os.getcwd(),"CBT_Dataset"),0)
            if(previous_count!= current_count):
                print(f"** Previous Count :{previous_count} || Current Count : {current_count}")
                print("** Proceeding with parsing and preprocessing the data")
                save_current_count(current_count,1)
                return True
            else:
                save_current_count(current_count,0)
                prompt=input("** There is no new snapshot added or change in files,Still want to continue parsing and preprocessing the existing dataset ?? (y/n) : ")
                return prompt

    else:
        print("** Issue with json file , either no file exists or no data in json exists !!!")
        save_current_count(get_file_count(os.path.join(os.getcwd(),"CBT_Dataset"),0),1)
        return True
def save_current_count(count,execution_status):
    data={"file_count":count , "execution_status":execution_status}
    with open(state_file,"w") as file:
        json.dump(data,file,indent=4)
        file.close()

    # with open(state_file, "w") as f:
    #     json.dump({"file_count": count}, f)
    #     print(">> json created")



state_file=os.path.join(os.getcwd(),"config.json")
flag=check_dir_for_new_entries(state_file)
# flag='y'
if (flag == True) or (flag == 'y') :
    
    if os.path.exists(os.path.join(os.getcwd(),"Final_TestCases_Data.xlsx")):
        os.path.join(os.getcwd(),"Final_TestCases_Data.xlsx")
        os.remove(os.path.join(os.getcwd(),"Final_TestCases_Data.xlsx"))
    with pd.ExcelWriter("Final_TestCases_Data.xlsx", engine="openpyxl") as writer:
        for root, dirs, files in os.walk(os.path.join(os.getcwd(),"CBT_Dataset")):
            for file in files:
                if file.endswith('.html'):
                    failures = []
                    count+=1
                    file_path = os.path.join(root, file)
                    html=open(file_path)
                    print(">>",f"Parsing {file_path}")
                    try:
                        soup = BeautifulSoup(html, 'html.parser')
                    # tables = soup.find('table').find_all('table')
                        tables=soup.find('table').find_all('table')
                    except Exception as e:
                        print(f"Exception Occured while parsing {file_path} : {e}")
                    for table in tables:
                        statistics_data = []
                        heading = table.find_all('tr', attrs={'style':'padding-top:10px;'})
                        html_data = table.find_all('table', attrs={'style': 'border: 1px solid #c0cad1; border-collapse: collapse;width:100%; table-layout: fixed;'})
                        if len(heading)!=0 and len(html_data)!=0:
                            if "Failed Results" in heading[0].text.strip():
                                suite=heading[0].text.split(" ")[0]
                                if suite != "VERIFIER" :
                                    for rows in html_data[0].find_all("tr"):
                                        r=[]
                                        for cells in rows.find_all("td"):
                                            r.append(cells.text.strip())

                                        if len(r)!=0:
                                            r.append(suite)
                                            failures.append([r[0]]+[r[-1]])
                            #Pulling all modules for Zero Risk modules Seggregation
                            elif "Package Summary" in heading[0].text.strip():
                                p_suite = heading[0].text.split("(")[1].split(")")[0]
                                if p_suite!="VERIFIER":
                                    for rows in html_data[0].find_all("tr"):
                                        r = []
                                        for cells in rows.find_all("td"):
                                            r.append(cells.text.strip())
                                        if len(r) != 0:
                                            total_modules_data.add(f"{r[0]}>>{p_suite}")
                    record_count=count_occurrences_2d_list(failures)
                    occurrences = [list(record) + [count] for record, count in record_count.items()]
                    for keys , values in record_count.items():
                        add_to_dict(keys,values,count)

                    for key, values in my_dict.items():
                        if len(my_dict[key]) <= count - 1:
                            while (len(my_dict[key]) <= count - 1):
                                my_dict[key].append(0)

                    print(f"Total testcases parsed :{len(failures)}")
        total_modules_data=list(total_modules_data)
        print(total_modules_data)
        final_total_module_data=[]
        for items in total_modules_data:
            final_total_module_data.append(items.split(">>"))
        print(final_total_module_data)

        for keys ,values in my_dict.items():
            if len(my_dict[keys]) != count:
                print("="*4,"Exception Occurred","="*4,"\n",keys , "==>" , values,"==>",len(my_dict[keys]))
            print(keys,"-->",values,"==>",len(my_dict[keys]))

            #Creating reference list for No risk modules seggregation

            reference_modules.append(f"{keys[0]}>>{keys[1]}")
            my_dict_to_list.append(list(keys)+my_dict[keys])
            try:
                final_list.append(list(keys)+calcuate_statistics(my_dict[keys]))
            except Exception as e:
                print("==> Exception occured : ",e)
        # Reference modules vs Total Modules Comparision
        for i in total_modules_data:
            if i not in reference_modules:
                zero_risk_modules.append(i.split(">>"))

        print("*"*10,"Final Statistical data ","*"*10)
        for items in final_list:
            print(items)
        print(count)
        # print("*" * 10, "Reference Modules Data ", "*" * 10)
        # print(i for i in reference_modules)
        # print("*" * 10, "Zero Risk Modules ", "*" * 10)
        # print(i for i in zero_risk_modules)



        file_names=[]
        file_names.append("Module")
        file_names.append("Suite")
        for i in range(1,count+1):
            file_names.append(f"File_{i}")

        df1=pd.DataFrame(my_dict_to_list,columns=file_names)
        df1.to_excel(writer,sheet_name="File_Wise_Module_Count",index=False)
        df2=pd.DataFrame(final_list,columns=["Module","Suite","mean","std_dev","variance","Coefficient of Variation"])
        df2.to_excel(writer,sheet_name="Statistics",index=False)
        df3=pd.DataFrame(final_total_module_data,columns=["Module","Suite"])
        df3.to_excel(writer,sheet_name="Overall Modules",index=False)
        df4 = pd.DataFrame(zero_risk_modules, columns=["Module", "Suite"])
        df4.to_excel(writer, sheet_name="Zero Risk Modules", index=False)
        print("\n>> Statistics sheet added")
        print("Zero risk modules : ", len(zero_risk_modules))
        print("final_total_modules:",len(final_total_module_data))
        print("Effected modules : ",len(my_dict_to_list))
    print(os.path.join(os.getcwd(),"Final_TestCases_Data.xlsx"),"is created successfully")


    # df1 = pd.DataFrame(final_failures_count, columns=["Module","Suite","count"])

    # Format the date and time as a string
    # file_name = now.strftime("%Y-%m-%d_%H-%M-%S")



    # with pd.ExcelWriter("Final_TestCases_Data.xlsx", engine="openpyxl") as writer:
    #     # Write each DataFrame to a different worksheet
    #     suites = df1['Suite'].unique()
    #     for suite in suites:
    #         suite_df = df1[df1['Suite'] == suite]
    #         suite_df.to_excel(writer, sheet_name=suite, index=False)

else :
    print("==> Data preprocessing aborted !!!! ")



