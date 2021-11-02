#!python
# Used to get all log lines related to a specific message ID from IMSx product logs
# Author: Joel Ginsberg joel_ginsberg@trendmicro.com
# Date: 10/29/21
# Version 1.0

import os
import sys
import glob
import subprocess
import linecache
from datetime import datetime
import logging
import argparse
from pprint import pprint

# os.path.normpath() if needed for forward slashes on windows, but also works on Windows without
# workingDir = "/Users/joelg/Downloads/test/"
workingDir = "C:/Users/joelg/Documents/Cases/Banco Bradesco/3056068 - IMSVA deferred issue/"  # Make sure to end name with a /

# CDTname = "CDT-20211028-121205.zip"
CDTname = "CDT-20200311-101037.zip"
CDTfolder = CDTname[:-4] + "/"
# print(CDTfolder)

# !!! Do not mkdir() this path until after unzip function, because it runs based on whether CDTfolder exists
outputDir = workingDir + CDTfolder + "log_search_output/"

IMSSLogDir = "IMSVA/LogFile/Event3/"
#IMSSLogFile = "log.imss.20211028.0043"

maillogDir = "IMSVA/Logfile/Event5"
#maillogFile = "maillog"

# messageID = "20211028141353.A12EBDE048@mx2.sat.gob.mx" # Test for reading previous log.imss file
# messageID = "1635427594006111272.5604.5407009073664769857@satt.gob.mx" # Test for reading one log.imss file
messageID = "9v_5rM_GQYq8sRirj1ghJA@ismtpd0036p1iad1.sendgrid.net"  # Test for next file in log file 41 and 42 (in normal log level)

'''logging.basicConfig(filename=workingDir + 'unzip_CDT.log',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')'''

# Set log level from cmd line args
parser = argparse.ArgumentParser()
parser.add_argument(
    "-l",
    "--log",
    default="warning",
    help=(
        "Provide logging level, default='warning'"
        "Example: '--log debug'"),
)

options = parser.parse_args()
levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}

level = levels.get(options.log.lower())
#print(options.log.lower())
#print(level)

def loggerSetup(logLevel=level):
    if logLevel is None:
        raise ValueError(
            f"log level given: {options.log}"
            f" -- must be one of: {' | '.join(levels.keys())}")
    else:
        logging.basicConfig(filename=workingDir + 'unzip_CDT.log',
                        level=logLevel,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # print log messages to console also
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
#logger = logging.getLogger(__name__)
#print(logger)

class Message(object):
    start_scan_time = ""
    end_scan_time = ""
    IMSSprocID = ""
    externalID = ""
    internalIDs = []
    IMSS_log_files = []
    maillogQueueIDs = []
    maillog_files = []
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
    os.chdir(workingDir)
    # If CDT folder does not already exist, then unzip CDT using 7zip.exe
    if not os.path.isdir(CDTfolder):
        # in CMD prompt: "C:/Program Files/7-Zip/7z.exe" x /Users/joelg/Downloads/test/CDT-20211028-121205.zip -p"trend" -o"/Users/joelg/Downloads/test/CDT-20211028-121205/" -aoa
        # -aoa will overwrite any conflicts
        #print(f"Unzipping CDT file to {CDTfolder}...")
        logging.info(f"Unzipping CDT file to {CDTfolder}...")
        cmd = ["C:/Program Files/7-Zip/7z.exe", "x", workingDir + CDTname, "-ptrend", f"-o{workingDir + CDTfolder}",
               "-aoa"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        process.wait()
        for line in process.stdout:
            #print(line.decode("utf-8").rstrip())
            logging.info(line.decode("utf-8").rstrip())
    else:
        #print(f"{datetime.now()} CDT unzip destination folder {workingDir + CDTfolder} already exists, take no action")
        logging.info(
            f"{datetime.now()} CDT unzip destination folder {workingDir + CDTfolder} already exists, take no action")

def updateLogger():
    '''To update log output after CDT file is unzipped'''
    # Create and change output folder for logs and search results to CDTfolder/log_search_output/
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)

    # Create new log file handler
    fileh = logging.FileHandler(outputDir + 'log_search.log', 'a')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileh.setFormatter(formatter)
    fileh.setLevel(level=level)

    # Replace existing log handlers
    log = logging.getLogger()  # root logger
    for hdlr in log.handlers[:]:  # remove all old handlers
        log.removeHandler(hdlr)
    log.addHandler(fileh)  # set the new handler
    log.addHandler(logging.StreamHandler(sys.stdout)) # stream log output to console
    #logging.debug("Test")

def getMaillogs():
    os.chdir(workingDir + CDTfolder + maillogDir)
    result = []

    # print(message.maillogQueueIDs)

    def getLogsByQueueID(queue_id, file):
        # Will contain all relevant log lines for target queue IDs
        lines = []
        with open(file, "r") as f:  # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
            # print(queue_id)
            hit_count = 0
            for line in f:
                # "B8BD647FC"
                if queue_id in line:
                    lines.append(line)
                    hit_count += 1
            if hit_count == 0:
                logging.warning(f"Queue ID {queue_id} not found in {file}")
            logging.info(f"{hit_count} lines with queue ID {queue_id} found in file {file}")
        logging.debug("".join(lines))
        return lines

    if message.maillog_files:
        logging.debug("Maillogs found:")
        for file in message.maillog_files:
            for queueID in message.maillogQueueIDs:
                result += getLogsByQueueID(queueID, file)
    else:
        logging.warning("No maillog files found")
    # print(f"Result {result}")
    if result:
        with open(outputDir + "___maillogs___.txt", "w", encoding="latin-1") as fo:
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

    def getProcessLogsInFile(file, IMSSprocID, msgID, np=0):
        # np variable is next/previous. If 0, read current file. If -1, read previous file, if 1, read next file

        # log lines found
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
            if "Start Rule Set Retrieval spent" in line:
                message_starts.append(i)
            if "Scan finished for" in line:
                message_ends.append(i)
            if msgID in line:
                message_IDs.append(i)
        # print(lines)
        return lines, message_starts, message_IDs, message_ends

    for file in message.IMSS_log_files:
        result, message_starts, message_IDs, message_ends = getProcessLogsInFile(file, message.IMSSprocID,
                                                                                 message.externalID)
        # print(result)
    # print(message.IMSS_log_files)

    prev_IMSS_file = file[:-4] + str(int(file[-4:]) - 1).zfill(4)
    next_IMSS_file = file[:-4] + str(int(file[-4:]) + 1).zfill(4)
    # print(prev_IMSS_file)
    # print(next_IMSS_file)

    if result:
        logging.debug(f"Result before slicing: {''.join(result)}")
        # TODO: test this logic
        logging.debug(f"Lists of line numbers of all Message starts, Message IDs, and Message ends: {message_starts}, {message_IDs}, {message_ends}")
        with open(outputDir + "___log.imss___.txt", "w", encoding="latin-1") as fo:
            # If there are equal amount of starts and ends of messages,
            # and the message ID is before the end of last message in logs
            #print(len(message_starts), len(message_ends))
            if len(message_starts) == len(message_ends): #and message_IDs[-1] > message_starts[-1]:
                logging.info(f"Message found in {file}")
                # we already know message ID is less than the end of the last message,
                # so message will be the first (message start > message ID)
                # Get the message that starts before the message ID from process logs
                for i, value in enumerate(message_ends):
                    # print(message_starts[i],message_ends[i], value)
                    #print(i, value, message_ends[i])
                    # If end of message occurred after the message ID in logs
                    if message_IDs[0] < value:
                        print(i, message_starts[i], message_IDs[0], message_ends[i], value)

                        result = result[message_starts[i]:(message_ends[i] + 1)]
                        logging.debug(''.join(result))
                        return  # don't process more than the first result
                fo.write("".join(result))
            if message_IDs[-1] > message_ends[-1]:
                # Message ends in next file
                # Must assign result before next_result to keep message_starts indexes correct
                # Get everything from last message start to end of file
                next_message_ends = []
                result = result[message_starts[-1]:]
                logging.debug(f"Result after slicing: {result}")
                logging.info(
                    f"Did not find end of message in {file}, checking next file {next_IMSS_file}.")
                next_result, next_message_starts, next_message_IDs, next_message_ends = \
                    getProcessLogsInFile(next_IMSS_file, message.IMSSprocID, message.externalID)

                logging.debug(f"next_result after slicing: {next_result}")
                # Get process lines in next file from beginning of file to end of first message
                next_result = next_result[:next_message_ends[0]]
                logging.debug(f"next_result after slicing: {next_result}")
                result = result + next_result

                # Set message.start_scan_time based on first log line where process ID is found
                # Convert String ( ‘YYYY/MM/DD HH:MM:SS ‘) to datetime object
                message.start_scan_time = datetime.strptime(' '.join(result[0].split()[:2]), '%Y/%m/%d %H:%M:%S')
                # Ditto for end scan time
                message.end_scan_time = datetime.strptime(' '.join(result[-1].split()[:2]), '%Y/%m/%d %H:%M:%S')

                fo.write("".join(result))
            else:
                #TODO: remove this return
                return
                # Message starts on previous file
                # Must assign result before prev_result to keep message_starts indexes correct
                # Get everything from beginning of file to first message end
                result = result[:(message_ends[0] + 1)]
                logging.debug(f"Result: {result}")
                logging.info(
                    f"Did not find beginning of message in {file}, checking previous file {prev_IMSS_file}.")
                prev_result, prev_message_starts, prev_message_IDs, prev_message_ends = \
                    getProcessLogsInFile(prev_IMSS_file, message.IMSSprocID, message.externalID)

                # Using most recent message_starts since we want the last message start in previous file
                logging.debug(f"prev_result before slicing: {prev_result}")
                prev_result = prev_result[message_starts[-1]:]
                logging.debug(f"prev_result after slicing: {prev_result}")
                result = prev_result + result

                # Set message.start_scan_time based on first log line where process ID is found
                # Convert String ( ‘YYYY/MM/DD HH:MM:SS ‘) to datetime object
                message.start_scan_time = datetime.strptime(' '.join(result[0].split()[:2]), '%Y/%m/%d %H:%M:%S')
                # Ditto for end scan time
                message.end_scan_time = datetime.strptime(' '.join(result[-1].split()[:2]), '%Y/%m/%d %H:%M:%S')

                fo.write("".join(result))
            logging.info(f"Message scan start time: {message.start_scan_time}")
            logging.info(f"Message scan end time: {message.end_scan_time}")
    else:
        logging.warning("No lines with process ID found in files")
    # print(message_starts, message_IDs, message_ends)

    return result


def getInternalIDs(loglines):
    IDs = []
    if loglines:
        if "Scan finished for" in loglines[-1]:
            IDs.append(loglines[-1].split()[7].strip(","))
        else:
            logging.warning("Internal message ID not found in log.imss")
    else:
        logging.warning("No IMSS logs to search for internal ID")
    # TODO: search polevt logs as backup
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
                if f"message-id=<{msgID}" in line:
                    maillog_result.append(line)
                    found_in_maillog_files.append(f.name)
                    # Keep unique entries only in case message was scanned more than once in same file
                    found_in_maillog_files = [*{*found_in_maillog_files}]
                    # print(line)
    # print(maillog_result)
    if maillog_result == []:
        logging.warning("Message ID not found in Postfix maillogs!")
    else:
        # Get Postfix queue IDs from maillog lines where external ID is found

        if len(maillog_result) > 1:
            for line in maillog_result:
                # print(line.split())
                message.maillogQueueIDs.append(line.split()[5].strip(":"))
        else:
            # Make sure to use 'maillog_result[0]' NOT 'line' which is using value from line 209 instead of 289
            # print(maillog_result[0].split()[5].strip(":"))
            message.maillogQueueIDs.append(maillog_result[0].split()[5].strip(":"))

        message.maillog_files = found_in_maillog_files
        logging.info(
            f"{len(maillog_result)} line(s) found containing message ID '{msgID}' in file(s): {', '.join(message.maillog_files)}")
        logging.debug(f"Maillog line(s): {''.join(maillog_result)}")

        logging.info(f"Maillog queue IDs: {message.maillogQueueIDs}")

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
        logging.info(
            f"{len(result)} line(s) found containing message ID '{msgID}' in file(s): {', '.join(message.IMSS_log_files)}")
        #logging.debug(f"IMSS log line(s): {''.join(result)}")
    print(message.IMSSprocID)
    return maillog_result, result


if __name__ == "__main__":
    # Must initialize logger then unzip CDT first, unzip function will only run if destination folder does not already exist
    loggerSetup()
    logging.info("<---Begin unzip CDT--->")
    try:
        unzip_CDT()
    except Exception as e:
        logging.error(e)
    logging.info("<---End unzip CDT--->")
    # Update log output from workingDir to CDTfolder/log_search_output
    try:
        updateLogger()
    except Exception as e:
        logging.error(e)

    logging.info("<---Begin log search--->")
    # Create new message object
    try:
        message = make_message()
        message.externalID = messageID
    except Exception as e:
        logging.error(e)

    findMessageByExternalID(message.externalID)
    # logging.info(f"{datetime.now()} log.imss process ID: {message.IMSSprocID}, message external ID: {message.externalID}")

    message.maillogs = getMaillogs()
    message.IMSSLogs = getIMSSLogs()
    # logging.debug("".join(message.IMSSLogs))

    message.internalIDs = getInternalIDs(message.IMSSLogs)
    logging.info(f"Internal IDs: {''.join(message.internalIDs)}")

    # Print all message information to json
    with open(outputDir + "___message___.json", "w") as f:
        pprint(message.__dict__, indent=2, stream=f)

    logging.info("<---End log search--->")
