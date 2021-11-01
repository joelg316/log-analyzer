#!python
# Used to get all log lines related to a specific message ID from IMSx product logs
# Author: Joel Ginsberg joel_ginsberg@trendmicro.com
# Date: 10/29/21
# Version 1.0

import os
import glob
import subprocess
import linecache
from datetime import datetime
import logging
from pprint import pprint

# os.path.normpath() if needed for forward slashes on windows, but also works on Windows without
workingDir = "/Users/joelg/Downloads/test/"
# Script logging file
logging.basicConfig(filename=workingDir + 'log_analyzer.log', level=logging.INFO)

CDTname = "CDT-20211028-121205.zip"
CDTfolder = CDTname[:-4] + "/"
# print(CDTfolder)
IMSSLogDir = "IMSVA/LogFile/Event3/"
IMSSLogFile = "log.imss.20211028.0043"

maillogDir = "IMSVA/Logfile/Event5"
maillogFile = "maillog"

messageID = "20211028141353.A12EBDE048@mx2.sat.gob.mx"


class Message(object):
    start_scan_time = ""
    end_scan_time = ""
    IMSSprocID = ""
    externalID = ""
    internalIDs = []
    IMSS_log_files = []
    maillogQueueIDs = []
    '''
    # The class "constructor" - It's actually an initializer
    def __init__(self, date_time, IMSSprocID, externalID):
        self.date_time = datetime
        self.IMSSprocID = IMSSprocID
        self.externalID = externalID
    '''
def make_message():
    message = Message()
    return message

def unzip_CDT():
    # If CDT folder does not already exist, then unzip CDT using 7zip.exe
    if not os.path.isdir(workingDir + CDTfolder):
        # in CMD prompt: "C:/Program Files/7-Zip/7z.exe" x /Users/joelg/Downloads/test/CDT-20211028-121205.zip -p"trend" -o"/Users/joelg/Downloads/test/CDT-20211028-121205/" -aoa
        # -aoa will overwrite any conflicts
        print(f"Unzipping CDT to {CDTfolder}...")
        cmd = ["C:/Program Files/7-Zip/7z.exe", "x", workingDir + CDTname, "-ptrend", f"-o{workingDir + CDTfolder}",
               "-aoa"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        process.wait()
        for line in process.stdout:
            print(line.decode("utf-8").strip("\n"))
    else:
        #TODO: figure out why this warning is only written to log file, not to console as expected
        logging.warning(f"{datetime.now()} CDT unzip destination folder {workingDir + CDTfolder} already exists")


def getMaillogs():
    os.chdir(workingDir + CDTfolder + maillogDir)
    result = []
    #print(message.maillogQueueIDs)

    def getLogsByQueueID(queue_id, file):
        # Will contain all relevant log lines for target queue IDs
        lines = []
        with open(file, "r") as f:  # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
            #print(queue_id)
            hit_count = 0
            for line in f:
                #"B8BD647FC"
                if queue_id in line:
                    lines.append(line)
                    hit_count += 1
            if hit_count == 0:
                logging.warning(f"Queue ID {queue_id} not found in {file}")
            logging.info(f"{hit_count} lines with queue ID {queue_id} found in file {file}")
        print("Maillogs found:")
        print("".join(lines))
        return lines

    if message.maillog_files:
        #print(message.maillogQueueIDs, message.maillog_files)
        for file in message.maillog_files:
            for queueID in message.maillogQueueIDs:
                result += getLogsByQueueID(queueID, file)
    else:
        logging.warning("No maillog files found")
    #print(f"Result {result}")
    if result:
        with open(workingDir + "___maillogs___.txt", "w", encoding="latin-1") as fo:
            fo.write("".join(result))
    return result


def getIMSSLogs():
    '''Returns all the related process lines in a file for a given external message ID and process ID'''
    os.chdir(workingDir + CDTfolder + IMSSLogDir)

    # Lists of line numbers containing message starts, IDs, and ends.
    message_starts = []
    message_ends = []
    message_IDs = []

    # Will contain all relevant process logs in current file
    result = []

    def getProcessLogsInFile(file, IMSSprocID, msgID):
        lines = []
        with open(file, "r",
                  encoding="latin-1") as f:  # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
            hit_count = 0
            for line in f:
                if IMSSprocID in line:
                    lines.append(line)
                    hit_count += 1
            if hit_count == 0:
                logging.warning(f"Process ID {IMSSprocID} not found in {file}")
            logging.info(f"{hit_count} lines with process ID {IMSSprocID} found in file {file}")
        for i, line in enumerate(lines):
            if "Info: Accept connection from client [127.0.0.1]" in line:
                message_starts.append(i)
            if "Scan finished for" in line:
                message_ends.append(i)
            if msgID in line:
                message_IDs.append(i)
        # print(lines)
        return lines

    for file in message.IMSS_log_files:
        result += getProcessLogsInFile(file, message.IMSSprocID, message.externalID)
        # print(result)
    # print(message.IMSS_log_files)

    prev_IMSS_file = IMSSLogFile[:-4] + str(int(IMSSLogFile[-4:]) - 1).zfill(4)
    next_IMSS_file = IMSSLogFile[:-4] + str(int(IMSSLogFile[-4:]) + 1).zfill(4)
    # print(prev_IMSS_file)
    # print(next_IMSS_file)

    if result:
        # TODO: test this logic
        with open(workingDir + "___log.imss___.txt", "w", encoding="latin-1") as fo:
            if message_starts[0] < message_IDs[0] and message_IDs[0] < message_ends[0]:
                # Message ID is found between first message start and first message end
                # What if it's not in the first message start? Mqybe need a for loop
                print("Message starts and ends in this file")
                result = result[message_starts[0]:(message_ends[0] + 1)]
                fo.write("".join(result))
            if message_starts[0] < message_IDs[0] and message_IDs[0] > message_ends[0]:
                #TODO: append results from next file like was done in previous file below
                print("Message ends in the next file")
                result = result[message_starts[-1]:]
                fo.write("".join(result))
            else:
                # Message starts on previous file
                # Must assign result before prev_result to keep message_starts indexes correct
                # Get everything from beginning of file to first message end
                result = result[:(message_ends[0] + 1)]
                # print(result)
                logging.info(
                    f"Did not find beginning of message in {file}, checking previous file {prev_IMSS_file}.")
                prev_result = getProcessLogsInFile(prev_IMSS_file, message.IMSSprocID, message.externalID)
                # Using most recent message_starts since we want the last message start in previous file
                prev_result = prev_result[message_starts[-1]:]
                # print(prev_result)
                result = prev_result + result

                # Set message.start_scan_time based on first log line where process ID is found
                # Convert String ( ‘YYYY/MM/DD HH:MM:SS ‘) to datetime object
                message.start_scan_time = datetime.strptime(' '.join(result[0].split()[:2]), '%Y/%m/%d %H:%M:%S')
                # Ditto for end scan time
                message.end_scan_time = datetime.strptime(' '.join(result[-1].split()[:2]), '%Y/%m/%d %H:%M:%S')
                logging.info(f"Message scan start time: {message.start_scan_time}")
                logging.info(f"Message scan end time: {message.end_scan_time}")

                fo.write("".join(result))
    else:
        logging.warning("No lines with process ID found in files")
    #print(message_starts, message_IDs, message_ends)

    return result


def getInternalIDs(loglines):
    IDs = []
    if loglines:
        if "Scan finished for" in loglines[-1]:
            IDs.append(loglines[-1].split()[7].strip(","))
        else:
            logging.warning("Internal message ID not found in log.imss")
    return IDs


def findMessageByExternalID(msgID):
    # Find relevant maillog files
    os.chdir(workingDir + CDTfolder + maillogDir)
    maillog_files = glob.glob("maillog*")
    maillog_result = []
    found_in_maillog_files = []
    for file in maillog_files:
        with open(file, "r",
                  encoding="latin-1") as f:  # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
            for line in f:
                if msgID in line:
                    maillog_result.append(line)
                    found_in_maillog_files.append(f.name)
                    # Keep unique entries only in case message was scanned more than once in same file
                    found_in_maillog_files = [*{*found_in_maillog_files}]
                    #print(line)
    if maillog_result == []:
        logging.warning("Message ID not found in Postfix maillogs!")
    else:
        #print(maillog_result)
        if len(maillog_result) > 1:
            for line in maillog_result:
                #print(line.split())
                message.maillogQueueIDs.append(line.split()[5].strip(":"))
        else:
            # Make sure to use 'maillog_result[0]' NOT 'line' which is using value from line 209
            #print(maillog_result[0].split()[5].strip(":"))
            message.maillogQueueIDs.append(maillog_result[0].split()[5].strip(":"))
            logging.info(f"Maillog queue IDs: {message.maillogQueueIDs}")

        message.maillog_files = found_in_maillog_files
        print(f"{len(maillog_result)} line(s) found containing message ID '{msgID}' in file(s): {', '.join(message.maillog_files)}")
        logging.info(f"Maillog line(s): {maillog_result}")

    # Find relevant IMSS log files
    os.chdir(workingDir + CDTfolder + IMSSLogDir)
    IMSS_log_files = glob.glob("log.imss*")
    # print(IMSS_log_files)
    result = []  # temp list to store log lines
    found_in_log_files = []  # store relevant log files
    for file in IMSS_log_files:
        with open(file, "r",
                  encoding="latin-1") as f:  # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
            for line in f:
                if msgID in line:
                    result.append(line)
                    found_in_log_files.append(f.name)
                    # Keep unique entries only in case message was scanned more than once in same file
                    found_in_log_files = [*{*found_in_log_files}]
    if result == []:
        logging.warning("Message ID not found in IMSS logs!")
    else:
        message.IMSSprocID = result[0].split()[3]
        message.IMSS_log_files = found_in_log_files
        print(
            f"{len(result)} line(s) found containing message ID '{msgID}' in file(s): {', '.join(message.IMSS_log_files)}")
        logging.info(f"IMSS log line(s): {result}")
    return maillog_result, result


if __name__ == "__main__":
    # Gotta unzip CDT before anything else, function will only run if destination folder does not already exist
    unzip_CDT()

    # Create new message object
    message = make_message()
    message.externalID = messageID

    findMessageByExternalID(message.externalID)
    logging.info(
        f"{datetime.now()} log.imss process ID: {message.IMSSprocID}, message external ID: {message.externalID}")
    message.maillogs = getMaillogs()
    message.IMSSLogs = getIMSSLogs()

    #logging.debug("".join(message.IMSSLogs))
    message.internalIDs = getInternalIDs(message.IMSSLogs)
    logging.info(f"Internal IDs: {''.join(message.internalIDs)}")
    with open(workingDir + "___message___.json", "w") as f:
        pprint(message.__dict__, indent=2, stream=f)
