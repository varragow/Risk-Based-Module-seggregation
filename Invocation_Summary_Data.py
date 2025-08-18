import os
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pickle
import shutil
import pandas as pd
module_time_consumed=dict()

def check_for_file(file):
    if os.path.isdir(file):
        # Remove the directory and all its contents
        shutil.rmtree(file)
    elif os.path.exists(os.path.join(os.getcwd(), file)):
        print(f"Removing : {os.path.join(os.getcwd(), file)}")
        os.remove(os.path.join(os.getcwd(), file))
def search_and_store_data(directory):
    # Initialize an empty list to store the data
    data = []

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        if "invocation_summary.txt" in files and "test_result.xml" in files :
            demo_module_time_consumed = []
            time_taken=[]
            suite=""
            for file in files:
                if file == "invocation_summary.txt":
                    # Construct the full file path
                    file_path = os.path.join(root, file)
                    print(">"*2,f"Accessing invocation Summary from :{file_path}")
                    # print(file_path)
                    # Read the content of the file
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    str=""
                    i=4
                    while(i<len(lines)):
                        if ( "Total aggregated tests run time" in  lines[i]):
                            break
                        module = lines[i].split(":")[0].strip().split()[1]
                        time_taken_before = lines[i].split(":")[1].strip()
                        time_taken_after=convert_to_milliseconds(time_taken_before)

                        demo_module_time_consumed.append(module)
                        time_taken.append(time_taken_after)
                        # print(module, ":", time_taken_before,"==>",time_taken_after)

                        # if module in module_time_consumed:
                        #     module_time_consumed[module]=max(module_time_consumed[module],time_taken_after)
                        # else:
                        #     module_time_consumed[module]=time_taken_after
                        i+=1
                elif file == 'test_result.xml':
                    path=os.path.join(root,file)
                    print(">"*2,f"Accessing {file} from :{path}")
                    root = ET.parse(path)
                    result = root.getroot()
                    suite = result.attrib['suite_plan'].upper()
                    print(">"*2,"Belongs to suite : ",suite)
                    print("*"*10)
            for i in range(len(demo_module_time_consumed)):
                demo_module_time_consumed[i]+=f">>{suite}"
            # for i in range(len(demo_module_time_consumed)):
            #     print(demo_module_time_consumed[i],":",time_taken[i])

            for i in range(len(demo_module_time_consumed)):
                if demo_module_time_consumed[i] in module_time_consumed:
                    # print("*"*2,f"Found duplicate - Module : {demo_module_time_consumed[i]} , max({time_taken[i]},{module_time_consumed[demo_module_time_consumed[i]]})")
                    module_time_consumed[demo_module_time_consumed[i]]=max(module_time_consumed[demo_module_time_consumed[i]],time_taken[i])
                else:
                    module_time_consumed[demo_module_time_consumed[i]]=time_taken[i]
    return module_time_consumed


def convert_to_milliseconds(time_str):
    # Split the time string into parts
    parts = time_str.split()
    # Initialize total milliseconds
    total_ms = 0

    # Conversion factors
    conversion_factors = {
        'h': 3600000,  # hours to milliseconds
        'm': 60000,  # minutes to milliseconds
        's': 1000,  # seconds to milliseconds
        'ms': 1  # milliseconds to milliseconds
    }

    # Iterate over each part and convert to milliseconds
    if "ms" in parts:
        total_ms+=int(parts[0])
    else:
        for part in parts:
            if part[-1] in conversion_factors:
                unit = part[-1]
                value = int(part[:-1])
                total_ms += value * conversion_factors[unit]
            else:
                raise ValueError(f"Unknown time unit in part: {part}")
    return total_ms

def main():
    excel_data=[]
    # directory=r"\\rover\cts\Reports\Android_V\Pakala.LA.1.0\AU383\CTS\2024.06.24_11.37.59_High"
    directory = r"\\rover\cts\Dumping_Ground\Gowtham\Pakala_results"
    search_and_store_data(directory)
    sorted_data=dict(sorted(module_time_consumed.items() , key=lambda item:item[1], reverse=True))
    try:
        check_for_file('time_consumption')
        time_consumption=open('time_consumption','wb')
        pickle.dump(sorted_data, time_consumption)
        time_consumption.close()
        print(">"*2,"pickle dump done successfully")

        with open("time_consumption",'rb') as f:
            loaded_data=pickle.load(f)
        f.close()
        print(">"*2,"Loading pickle data")

        print(loaded_data)
        print(len(loaded_data))
    except Exception as e:
        print(f"Exception occured while accesssing {time_consumption} file : {e}")

    for keys,values in sorted_data.items():
        excel_data.append([keys.split(">>")[0],keys.split(">>")[1],values])
    check_for_file("Time Consumption.xlsx")
    with pd.ExcelWriter("Time Consumption.xlsx", engine="openpyxl") as writer:
        df=pd.DataFrame(excel_data,columns=['Module Name','Suite','TImetaken'])
        df.to_excel(writer,index=False)
if __name__ == '__main__':
    main()