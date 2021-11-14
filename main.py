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
import bisect
import re

# os.path.normpath() if needed for forward slashes on windows, but also works on Windows without
# Make sure to end name with a /
#workingDir = "/Users/joelg/Downloads/test/"
#workingDir = "C:/Users/joelg/Documents/Cases/Banco Bradesco/3056068 - IMSVA deferred issue/"
workingDir = "C:/Users/joelg/Documents/Lab/"

#CDTname = "CDT-20211028-121205.zip"
#CDTname = "CDT-20200311-101037.zip"
CDTname = "lab_CDT-20211107-004446.zip"
CDTfolder = CDTname[:-4] + "/"
# print(CDTfolder)

# !!! Do not mkdir() this path until after unzip function, because it runs based on whether CDTfolder exists
outputDir = workingDir + CDTfolder + "log_search_output/"

IMSSLogDir = "IMSVA/LogFile/Event3/"
#IMSSLogFile = "log.imss.20211028.0043"

maillogDir = "IMSVA/Logfile/Event5"
#maillogFile = "maillog"

#messageID = "20211028141353.A12EBDE048@mx2.sat.gob.mx" # Test for reading previous log.imss file
# messageID = "1635427594006111272.5604.5407009073664769857@satt.gob.mx" # Test for reading one log.imss file
# messageID = "9v_5rM_GQYq8sRirj1ghJA@ismtpd0036p1iad1.sendgrid.net" # Test for multiple message IDs
#messageID = "ceb54dd543cc4ce8b2473a8e740c6d57@CRRJ01VS002.cra1.local" # Test for next file in log file 41 and 42 (in normal log level)
messageID = "@astound.net"  # test with multiple message IDs from lab CDT

messages = []  # list for holding all messages when there are multiple hits for message ID in log.imss
maillog_messages = []  # list for holding all maillog messages that do not have IMSS-related properties
total_result = []  # for holding all log.imss results when there are multiple hits for message IDs
total_maillog_result = [] # for holding all maillog results when there are multiple message IDs
merged_messages = []  # after combining related messages

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
    id = ""
    start_scan_time = ""
    end_scan_time = ""
    IMSSprocID = ""
    externalID = ""
    internalIDs = []
    IMSS_log_file = []
    maillogQueueIDs = []
    relatedQueueIDs = []
    maillog_file = []
    '''
    # The class "constructor" - It's actually an initializer
    def __init__(self, date_time, IMSSprocID, externalID):
        self.date_time = datetime
        self.IMSSprocID = IMSSprocID
        self.externalID = externalID
    '''

    def __init__(self):
        pass

    def addMaillogs(self, other):
        '''
        Related object "other" will be the one that occurs first
        :param other: message object with same message ID as self
        :return: None; add maillogs
        '''
        if self.externalID != other.externalID:
            raise ValueError("Message objects do not have the same external ID")
        else:
            self.maillogs = other.maillogs + list("----------- sent to IMSS ------------\n") + self.maillogs

class Maillog_Message(Message):
    def __init__(self, **kwargs):
        pass

class IMSS_Message(Message):
    def __init__(self):
        pass
#
# def make_message():
#     message = Message()
#     return message

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

def combineMaillogMessages():
    count = 0
    if maillog_messages:
        for message in maillog_messages:
            for i, line in enumerate(message.maillogs):
                if "relay=" in line and line.split()[5].strip(":") != message.maillogQueueIDs:
                    print(line.split()[5].strip(":"))
                    print(message.maillogQueueIDs)

                    # Example for related queue 935162C03E with primary queue D89812C044
                    # 'Nov  5 13:12:19 IMSVA9-1chile postfix/smtp[24767]: 935162C03E: to=<joelg@joelg.com>,
                    #    relay=localhost[127.0.0.1]:10025, delay=3.5, delays=0.86/0.2/0.37/2.1, dsn=2.0.0,
                    #    status=sent (250 2.0.0 Ok: queued as D89812C044)
                    # 'Nov  5 13:12:20 IMSVA9-1chile postfix/smtp[24794]: D89812C044: Used TLS for 192.168.1.21[192.168.1.21]:25

                    message.relatedQueueIDs = line.split()[5].strip(":")
                    logging.debug(f"Found related queue ID: {message.relatedQueueIDs}")
                    print(i, line)
                    message.maillogs.pop(i)

            for new_message in maillog_messages:
                if message.relatedQueueIDs == new_message.maillogQueueIDs:
                    count += 1
                    print("Yes")
                    # merged_messages.append()
                    message.addMaillogs(new_message)
                    message.id = count
                    merged_messages.append(message)
        return merged_messages
    else:
        logging.error("Could not find maillog messages to combine")
        return None

def getMaillogs(message):
    os.chdir(workingDir + CDTfolder + maillogDir)
    result = []
    global total_maillog_result  # initialized to [] near beginning of script
    # print(message.maillogQueueIDs)

    def getLogsByQueueID(queue_id, file):
        #logging.info("Starting maillog search by queue ID...")
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

    if message.maillogQueueIDs:
        logging.debug("Maillogs found:")
        result += getLogsByQueueID(message.maillogQueueIDs, message.maillog_file)
    else:
        logging.error("No maillog files found")
    # print(f"Result {result}")
    if result:
        total_maillog_result += [f"Message #{message.id}\n"]
        total_maillog_result += result

    else:
        logging.error(f"No maillog queue IDs found for message #{message.id} with external ID {message.externalID}")

    return result



def getIMSSLogs(message):
    '''Returns all the related process lines in a file for a given external message ID and process ID'''
    os.chdir(workingDir + CDTfolder + IMSSLogDir)

    # Lists of line numbers containing message starts, IDs, and ends.
    message_starts = []
    message_ends = []
    message_IDs = []

    result = []  # Will contain all relevant process logs in current file
    new_result = []  # result after extracting relevant time frame from process logs
    global total_result  # initialized to [] near beginning of script

    def getProcessLogsInFile(file, IMSSprocID, msgID):
        # np variable is next/previous. If 0, read current file. If -1, read previous file, if 1, read next file

        # log lines found
        lines = []

        # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
        with open(file, "r", encoding="latin-1") as f:
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
                # Convert log timestamp ( ‘YYYY/MM/DD HH:MM:SS GMT-00:00‘) to datetime object
                time = datetime.strptime(' '.join(line.split()[:3]), '%Y/%m/%d %H:%M:%S %Z%z')
                #print(time)
                message_starts.append([time, i])
                #print(line)

            if "Scan finished for" in line:
                # Convert log timestamp ( ‘YYYY/MM/DD HH:MM:SS GMT-00:00‘) to datetime object
                time = datetime.strptime(' '.join(line.split()[:3]), '%Y/%m/%d %H:%M:%S %Z%z')
                #print(time)
                message_ends.append([time, i])
                #print(line)

            if msgID in line:
                # Convert log timestamp ( ‘YYYY/MM/DD HH:MM:SS GMT-00:00‘) to datetime object
                time = datetime.strptime(' '.join(line.split()[:3]), '%Y/%m/%d %H:%M:%S %Z%z')
                #print(time)
                message_IDs.append([time, i])
                #print(line)
        # print(lines)
        return lines, message_starts, message_IDs, message_ends

    result, message_starts, message_IDs, message_ends = getProcessLogsInFile(message.IMSS_log_file, message.IMSSprocID,
                                                                             message.externalID)
    prev_IMSS_file = message.IMSS_log_file[:-4] + str(int(message.IMSS_log_file[-4:]) - 1).zfill(4)
    next_IMSS_file = message.IMSS_log_file[:-4] + str(int(message.IMSS_log_file[-4:]) + 1).zfill(4)

    # If there are multiple files where message ID is found,
    # getProcessLogsInFile may not find the message ID one or more files
    #if message_IDs == []:
     #   message_IDs.append()

    # print(result)
    # print(message.IMSS_log_file)
    print(prev_IMSS_file)
    print(next_IMSS_file)

    if result:
        '''The following logic checks if the message start and end is on the same log file, if not it gets the process
        logs from the next and previous files and combines them with original log file.
        Also creates result_start which is every log line from message start to message ID
        and result_end which is every log line from message ID to message end. 
        Creating start and end result lists was necessary because the logic uses line numbers from 
        getProcessLogsInFile() and trimming the original result to only start at relevant start will 
        modify the log lines before you can trim the end'''

        logging.debug(f"message starts: {message_starts}")
        logging.debug(f"message IDs: {message_IDs}")
        logging.debug(f"message ends: {message_ends}")

        # If there is no message start found or the first start occurs later than the first message ID
        logging.debug(f"Message starts[0][0]: {message_starts[0][0]}, message ID: {message_IDs[0][0]}")
        if not message_starts or message_starts[0][0] > message_IDs[0][0]:
            print("Check previous file")
            # print(result)
            # Trim result from beginning of file to message ID
            result_start = result[:message_IDs[0][1]]
            # print(result)

            prev_result, prev_message_starts, prev_message_IDs, prev_message_ends = \
                getProcessLogsInFile(prev_IMSS_file, message.IMSSprocID, message.externalID)
            print(prev_message_starts)

            message.start_scan_time = prev_message_starts[-1][0]

            logging.debug(f"prev_result before slicing: {prev_result}")

            # get all process ID logs from previous file from last message start until end
            prev_result = prev_result[prev_message_starts[-1][1]:]
            logging.debug(f"prev_result after slicing: {prev_result}")

            # result start is the first half of the message process logs up to the message ID
            result_start = prev_result + result_start

        else:
            # print(list(zip(*message_starts))[0])  # returns a list of the datetimes of all the message_starts
            # Find the insertion point where the message ID timestamp would be inserted after next message start time stamp.
            i = bisect.bisect(list(zip(*message_starts))[1], message_IDs[0][1])
            # changed i to i-1 because bisect returns the insertion point for message_ID which is in next position
            message.start_scan_time = message_starts[i-1][0]
            result_start = result[message_starts[i-1][1]:message_IDs[0][1]]

        # If there is no message end found or the last message end occurs before the last message ID
        if not message_ends or message_ends[-1][0] < message_IDs[-1][0]:
            print("Check next file")

            # print(result)
            # Trim result from last message ID to end of file
            result_end = result[message_IDs[-1][1]:]
            # print(result)

            next_result, next_message_starts, next_message_IDs, next_message_ends = \
                getProcessLogsInFile(next_IMSS_file, message.IMSSprocID, message.externalID)
            #print(next_message_ends)

            message.end_scan_time = next_message_ends[0][0]

            logging.debug(f"next_result before slicing: {next_result}")

            # get all process ID logs from next file up to and including the line of the first message end.
            next_result = next_result[:next_message_ends[0][1] + 1]
            logging.debug(f"next_result after slicing: {next_result}")

            result_end = result_end + next_result
        else:
            # print(list(zip(*message_ends))[0]) # returns a list of the datetimes of all the message_ends
            # Find the insertion point where the message ID timestamp would be inserted before next message end time stamp.
            #TODO: test this
            j = bisect.bisect_left(list(zip(*message_ends))[1], message_IDs[0][1])
            # print(j)
            message.end_scan_time = message_ends[j][0]
            print(message_ends[j][1])
            # print(result[message_ends[j][1] + 1])
            result_end = result[message_IDs[0][1]:message_ends[j][1] + 1]

        new_result = result_start + result_end
        total_result += [f"Message #{message.id}\n"]
        total_result += new_result

        logging.info(f"Message scan start time: {message.start_scan_time}")
        logging.info(f"Message scan end time: {message.end_scan_time}")

    else:
        logging.warning(f"No lines with process ID found in file {file}")

    # Don't return total result, return new_result which is per message
    return new_result


def getInternalIDs(loglines):
    IDs = []
    if loglines:
        print(loglines[-1])
        if "Scan finished for" in loglines[-1]:
            IDs.append(loglines[-1].split()[7].strip(","))
        else:
            logging.warning("Internal message ID not found in log.imss")
    else:
        logging.warning("No IMSS logs to search for internal ID")
    # TODO: search polevt logs as backup
    return IDs

def findMessagesinMaillogs(msgID):
    # Find relevant maillog files
    os.chdir(workingDir + CDTfolder + maillogDir)
    maillog_files = glob.glob("maillog*")
    global maillog_result
    maillog_result = []
    found_in_maillog_files = []
    exp = re.compile(f'message-id=<\S*{msgID}\S*', re.IGNORECASE)
    '''for i, line in enumerate(imss_result):
        message = make_message()
        message.id = i
        message.maillog_file = found_in_maillog_files'''
    for file in maillog_files:
        # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
        with open(file, "r", encoding="latin-1") as f:
            for line in f:
                if re.search(exp, line):
                    print(line)
                    maillog_result.append([line, f.name])
                    #found_in_maillog_files.append(f.name)
                    # Keep unique entries only in case message was scanned more than once in same file
                    #found_in_maillog_files = [*{*found_in_maillog_files}]
                # print(line)'''
    # print(maillog_result)
    if maillog_result == []:
        logging.warning("Message ID not found in Postfix maillogs!")
    else:
        # Get Postfix queue IDs from maillog lines where external ID is found
        #if messages == []:
        message_count = 0
        for line in maillog_result:
            message_count += 1
            message = Message()
            message.id = message_count
            message.externalID = line[0].split()[6].strip("message-id=<>")
            message.maillog_file = line[1]
            message.maillogQueueIDs = line[0].split()[5].strip(":")
            maillog_messages.append(message)


        '''if len(maillog_result) > 1:
            for line in maillog_result:
                # print(line.split())
                message.maillogQueueIDs.append(line.split()[5].strip(":"))
        else:
            # print(maillog_result[0].split()[5].strip(":"))
            message.maillogQueueIDs.append(maillog_result[0].split()[5].strip(":"))

        message.maillog_file = found_in_maillog_files
        logging.info(
            f"{len(maillog_result)} line(s) found containing message ID '{msgID}' in file(s): {', '.join(message.maillog_file)}")
        logging.debug(f"Maillog line(s): {''.join(maillog_result)}")

        logging.info(f"Maillog queue IDs: {message.maillogQueueIDs}")
        '''
    return maillog_result

def findMessagesinIMSSlogs(msgID):
    '''Find all occurrences of external message ID in both maillog and log.imss files'''
    if msgID != "":
        # Find relevant IMSS log files
        os.chdir(workingDir + CDTfolder + IMSSLogDir)
        IMSS_log_files = glob.glob("log.imss*")
        # print(IMSS_log_files)
        imss_result = []  # temp list to store log lines
        found_in_log_files = []  # store relevant log files

        exp = re.compile(f'>>> Message-ID : <\S*{msgID}\S*', re.IGNORECASE)
        message_count = 0
        for file in IMSS_log_files:
            with open(file, "r",
                      encoding="latin-1") as f:  # Use errors="surrogateescape" or encoding="latin-1" for unicode errors
                for line in f:
                    if re.search(exp, line):
                    #if msgID in line:
                        message_count += 1
                        imss_result.append(line)
                        # found_in_log_files.append(f.name)
                        # Keep unique entries only in case message was scanned more than once in same file
                        # found_in_log_files = [*{*found_in_log_files}]
                        message = Message()
                        message.id = message_count
                        message.externalID = line.split()[7].strip("<>")
                        message.IMSSprocID = line.split()[3]
                        message.IMSS_log_file = f.name
                        messages.append(message)
        if imss_result == []:
            logging.warning("Message ID not found in IMSS logs!")

        '''else:
            for i, line in enumerate(imss_result):
                message = make_message()
                message.id = i
                message.externalID = msgID
                message.IMSSprocID = line.split()[3]
                message.IMSS_log_file = found_in_log_files
                messages.append(message)'''
        ''' else:
            message.IMSSprocID = imss_result[0].split()[3]
            message.IMSS_log_file = found_in_log_files
            logging.info(
                f"{len(imss_result)} line(s) found containing message ID '{msgID}' in file(s): {', '.join(message.IMSS_log_file)}")
            #logging.debug(f"IMSS log line(s): {''.join(result)}")
        print(message.IMSSprocID)'''
    else:
        logging.error("Please enter message ID and try again")
        exit(2)
    return imss_result


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

    # Create message object each time message ID is found in log.imss
    findMessagesinIMSSlogs(messageID)

    # Create message object each time message ID is found in maillogs
    findMessagesinMaillogs(messageID)
    print(maillog_result)

    # Get all maillogs by queue ID for each maillog message found
    for m in maillog_messages:
        m.maillogs = getMaillogs(m)

    # Compare maillog_messages and combine the maillogs for the ones related by queue IDs
    # Example: postfix/smtp[28130]: 7E0072C049: to=<joelg@joelg.com>, relay=localhost[127.0.0.1]:10025,
    # delay=1.1, delays=0.38/0.02/0.06/0.61, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as B60FC2C04C)
    # Queue ID was originally 7E0072C049 then was queued as B60FC2C04C, so B60FC2C04C is related to 7E0072C049
    merged_messages = combineMaillogMessages()

    with open(outputDir + "___merged_messages___.json", "w") as f:
        for message in merged_messages:
            f.write(f"\n-------- Message #{message.id} --------\n\n")
            f.write("".join(message.maillogs))
            # pprint(message.__dict__, indent=2, stream=f)

    # TODO: Try to correlate maillog_messages with messages list, not really needed

    with open(outputDir + "___maillogs___.txt", "w", encoding="latin-1") as fo:
        fo.write("".join(total_maillog_result))

    with open(outputDir + "___maillog_messages___.json", "w") as f:
        for message in maillog_messages:
            f.write(f"--- Message #{message.id} ---\n")
            pprint(message.__dict__, indent=2, stream=f)



    for m in messages:
        m.IMSSLogs = getIMSSLogs(m)

    with open(outputDir + "___log.imss___.txt", "w", encoding="latin-1") as fo:
        '''Write relevant process logs to file'''
        fo.write("".join(total_result))


    #message.internalIDs = getInternalIDs(message.IMSSLogs)
    #logging.info(f"Internal IDs: {''.join(message.internalIDs)}")

    # Print all message information to json
    with open(outputDir + "___message___.json", "w") as f:
        for message in messages:
            f.write(f"--- Message #{message.id} ---\n")
            pprint(message.__dict__, indent=2, stream=f)

    logging.info("<---End log search--->")
