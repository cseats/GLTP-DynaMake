import Oasys.PRIMER
import time
import os
from dotenv import load_dotenv
load_dotenv()

def connect2Primer():
    p = 4000
    for i in range(10):
        p+=1
        try:
            print(f"Trying connection on port {p}")
            connection = Oasys.PRIMER.start(abspath=os.getenv('PRIMERCON'),batch=False,port=p)
            # connection = Oasys.PRIMER.start(abspath="C:\\Users\\camp.seats\\AppData\\Roaming\\Ove Arup\\v21.0_x64\\primer21_x64.exe",batch=True,port=p)
            print(f'Connection Success!!')
            return connection
        except:
            print(f'Connection failed on port {p}')
            # Oasys.PRIMER.terminate(connection)
    raise Exception("WERE NOT ABLE TO CONNECT")

def connect2THis():
    p = 5000
    for _ in range(10):
        p+=1
        try:
            print(f"Trying connection on port {p}")
            connection = Oasys.THIS.start(abspath=os.getenv('THISCON'),batch=True,port=p)
            # connection = Oasys.THIS.start(abspath="C:\\Users\\camp.seats\\AppData\\Roaming\\Ove Arup\\v21.0_x64\\this21_x64.exe",batch=True,port=p)
            
            print(f'Connection Success!!')
            return connection
        except:
            print(f'THIS Connection failed on port {p}')
            time.sleep(15)
            # Oasys.PRIMER.terminate(connection)
    raise Exception("WERE NOT ABLE TO CONNECT")

def endTHIS(connection): #Terminate dyna window based on user input
    # inpt = input("Press enter to terminate dyna window: ")
    Oasys.THIS.terminate(connection)
    # while inpt != "":
    #     inpt = input("Press enter to terminate dyna window: ")
    
    # try:
    #     print('>Connection terminated')
    # except:
    #     print(">Window already terminated")
        
        
        
def saveModel(savePath,m,):
    print(f'>Saving model to {savePath}')
    output = {
        "version": "R13.0",
        "compress": False,
    }
    
    m.Write(savePath,output)
    print('>Model Saved.')