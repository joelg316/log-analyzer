#!python
# Used to get all log lines related to a specific message ID from IMSx product logs
# Author: Joel Ginsberg joel_ginsberg@trendmicro.com
# Date: 10/29/21
# Version 1.0

import os
import subprocess
import linecache
from datetime import datetime
import logging
from pprint import pprint

# os.path.normpath() if needed for forward slashes on windows, but also works on Windows without
workingDir = "/Users/joelg/Downloads/test/"
# Script logging file
logging.basicConfig(filename=workingDir + 'log_analyzer.log', level=logging.DEBUG)

CDTname = "CDT-20211028-121205.zip"
CDTfolder = CDTname[:-4] + "/"
# print(CDTfolder)
IMSSLogDir = "IMSVA/LogFile/Event3/"
IMSSLogFile = "log.imss.20211028.0043"

messageID = "20211028141353.A12EBDE048@mx2.sat.gob.mx"

IMSS_log_files = []
maillog_files = []

class Message(object):
    start_scan_time = ""
    end_scan_time = ""
    IMSSprocID = ""
    externalID = ""
    internalIDs = []

    '''
    # The class "constructor" - It's actually an initializer
    def __init__(self, date_time, IMSSprocID, externalID):
        self.date_time = datetime
        self.IMSSprocID = IMSSprocID
        self.externalID = externalID
    '''

def make_message(IMSSprocID, externalID):
    message = Message()
    message.IMSSprocID = IMSSprocID
    message.externalID = externalID
    # Note: I didn't need to create a variable in the class definition before doing this.
    message.internalIDs = []
    return message

def unzip_CDT():
    if not workingDir + CDTfolder:
        # in CMD prompt: "C:/Program Files/7-Zip/7z.exe" x /Users/joelg/Downloads/test/CDT-20211028-121205.zip -p"trend" -o"/Users/joelg/Downloads/test/CDT-20211028-121205/" -aoa
        # -aoa will overwrite any conflicts
        print(f"Unzipping CDT to {CDTfolder}...")
        cmd = ["C:/Program Files/7-Zip/7z.exe", "x", workingDir + CDTname, "-ptrend", f"-o{workingDir + CDTfolder}", "-aoa"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        process.wait()
        for line in process.stdout:
            print(line)
    else:
        print(f"CDT unzip destination folder {CDTfolder} already exists")

def getIMSSLogs(file, msgID, IMSSprocID):
    '''Returns all the related process lines in a file for a given external message ID and process ID'''
    os.chdir(workingDir + CDTfolder + IMSSLogDir)

    # Lists of line numbers containing message starts, IDs, and ends.
    message_starts = []
    message_ends = []
    message_IDs = []

    # Will contain all relevant process logs in current file
    result = []

    def getProcessLogsInFile(file, IMSSprocID):
        lines = []
        with open(file, "r", encoding="latin-1") as f: # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
            hit_count = 0
            for line in f:
                if IMSSprocID in line:
                    lines.append(line)
                    hit_count += 1
            if hit_count == 0:
                logging.warning(f"Process ID {IMSSprocID} not found in {file}")
            logging.info(f"{hit_count} lines with process ID found in file {file}")
        for i, line in enumerate(lines):
            if "Info: Accept connection from client [127.0.0.1]" in line:
                message_starts.append(i)
            if "Scan finished for" in line:
                message_ends.append(i)
            if msgID in line:
                message_IDs.append(i)
        return lines

    result = getProcessLogsInFile(file, IMSSprocID)

    prev_IMSS_file = IMSSLogFile[:-4] + str(int(IMSSLogFile[-4:]) - 1).zfill(4)
    next_IMSS_file = IMSSLogFile[:-4] + str(int(IMSSLogFile[-4:]) + 1).zfill(4)
    print(prev_IMSS_file)
    print(next_IMSS_file)


    #TODO: test this logic
    with open("___processID___.txt", "w", encoding="latin-1") as fo:
        if message_starts[0] < message_IDs[0] and message_IDs[0] < message_ends[0]:
            # Message ID is found between first message start and first message end
            # What if it's not in the first message start? Mqybe need a for loop
            print("Message starts and ends in this file")
            result = result[message_starts[0]:(message_ends[0]+1)]
            fo.write("".join(result))
        if message_starts[0] < message_IDs[0] and message_IDs[0] > message_ends[0]:
            print("Message ends in the next file")
            result = result[message_starts[-1]:]
            fo.write("".join(result))
        else:
            # Message starts on previous file
            # Must assign result before prev_result to keep message_starts indexes correct
            # Get everything from beginning of file to first message end
            result = result[:(message_ends[0]+1)]
            print(result)
            print(f"Message starts in previous log file, getting last scan ran on this process from file {prev_IMSS_file}")
            prev_result = getProcessLogsInFile(prev_IMSS_file, IMSSprocID)
            # Using most recent message_starts since we want the last message start in previous file
            prev_result = prev_result[message_starts[-1]:]
            print(prev_result)
            result = prev_result + result

            # Set message.start_scan_time based on first log line where process ID is found
            # Convert String ( ‘YYYY/MM/DD HH:MM:SS ‘) to datetime object
            message.start_scan_time = datetime.strptime(' '.join(result[0].split()[:2]), '%Y/%m/%d %H:%M:%S')
            # Ditto for end scan time
            message.end_scan_time = datetime.strptime(' '.join(result[-1].split()[:2]), '%Y/%m/%d %H:%M:%S')
            print(message.start_scan_time)
            print(message.end_scan_time)

            fo.write("".join(result))
    print(message_starts, message_IDs, message_ends)

    return result

def getInternalIDs(loglines):
    IDs = []
    if loglines:
        if "Scan finished for" in loglines[-1]:
            IDs.append(loglines[-1].split()[7].strip(","))
        else:
            print("Internal message ID not found in log.imss")
    return IDs

def findMessagesByID(file, msgID):

    os.chdir(workingDir + CDTfolder + IMSSLogDir)
    result = []
    with open(file, "r", encoding="latin-1") as f: # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
        for line in f:
            if msgID in line:
                result.append(line)
                IMSS_log_files.append(f.name)
                print(IMSS_log_files)
        if result == []:
            print("Not found!")
    print(f"{len(result)} line(s) found containing message ID '{messageID}' in file(s) {', '.join(IMSS_log_files)}")

    # Create array of message objects from lines where message ID was found
    for line in result:
        # print(line.split())
        IMSSprocID = line.split()[3]
        externalID = line.split()[7]
        # Create new message object
        messages.append(make_message(IMSSprocID, externalID))
    return messages

if __name__ == "__main__":
    #unzip_CDT()
    messages = []
    findMessagesByID(IMSSLogFile, messageID)
    print(messages)
    for message in messages:
        print(message.start_scan_time, message.IMSSprocID, message.externalID)
        for file in IMSS_log_files:
            message.IMSSLogs = getIMSSLogs(file, message.externalID, message.IMSSprocID)
            print(message.IMSSLogs)
        #for file in maillog_files:
        #    message.maillogs = getMaillogs()
        message.internalIDs = getInternalIDs(message.IMSSLogs)

        pprint(message.__dict__, indent=2)

