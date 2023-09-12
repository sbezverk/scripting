#
#  September, 2023 Serguei Bezverkhi (sbezverk)
#
# Copyright (c) 2023 by Cisco Systems, Inc.
# All rights reserved.

"""
asics_reset_lpts_check_vX.Y.py is EEM script which gets invoked when a spitfire router is reporting
ASIC ERROR following by a HARD RESET of the ASCIS. The script verifies the condtion when after ASCIS's
HARD RESET, LPTS policer's meter value for LDP-UDP flow does not get reprogrammed into the forwarding ASCIS which causes
LPTS to drop all incoming LDP UDP Discovery packets. Once packets drops detected, the script will restart mpls_ldp process,
which will force reprogramming of the forwarding ASICS.
If after ASCIS HARD RESET no drops are detected during the time defined by detection_loop_timeout (seconds), the script
exit without any action.
"""

from iosxr.xrcli.xrcli_helper import *
from cisco.script_mgmt import xrlog
from iosxr import eem
import re
import os
import sys
import time

# Defines how long in seconds, the script will wait and check for LPTS drops
detection_loop_timeout = 300
process_restart_cmd = "process restart mpls_ldp location 0/RP0/CPU0"
lpts_cmd = "sh lpts pifib statistics hardware police location 0/RP0/CPU0 | inc LDP-UDP"
#
syslog = xrlog.getSysLogger("asics_reset_lpts_check_eem")
helper = XrcliHelper(debug = True)
separator = re.compile("\s+")


def output_cleanup(cmd_output):
    # The output structure is "command/nresult", need to remove everything before and including /n
    result = cmd_output.split("\n")
    if len(result) != 4 :
        syslog.info('unexpected number of strings' + "% s" % len(result))
        return "", 4
    clean_line = result[2].strip()

    return clean_line,0

def get_drops_count(clean_line):
    fields = separator.split(clean_line,0)
    # LDP-UDP     np             542            1000           615          0           default
    if len(fields) != 7 :
        syslog.info('unexpected number of fields' + "% s" % len(fields))
        return 0,5
    
    return int(fields[5],10),0

def process_restart(cmd):
    restart_cmd_output = helper.xrcli_exec(cmd)
    if restart_cmd_output['status'] != "success" :
        syslog.info("failed to restart mpls_ldp process, status: " + restart_cmd_output['status'])
        return 6
    
    return 0

def exec_cmd(cmd):
    cmd_output = helper.xrcli_exec(cmd)
    if cmd_output['status'] != "success":
        syslog.info('failed to execute cmd, status: ' + cmd_output['status'])
        return "",7
    if cmd_output['output'] == "" :
        syslog.info('Output is empty')
        return "",3

    return cmd_output['output'], 0

def drops_count(cmd):
    cmd_output, err = exec_cmd(cmd)
    if err != 0:
        return 0,err
    clean_line, err = output_cleanup(cmd_output)
    if err != 0:
        return 0,err      
    drops, err = get_drops_count(clean_line)
    if err != 0:
        return 0,err

    return drops,0
       
if __name__ == '__main__':
    initial_timestamp = time.time()
    err = 0
    initial_drops_count, err = drops_count(lpts_cmd)
    if err != 0 :
        syslog.info('failed to get initial drops count with error: '+ "% s" % err)
        sys.exit(err)
    syslog.info('initial drops count: ' + "% s" % initial_drops_count)   
    while True:
        # LPTS drops detection loop
        syslog.info('In the detection loop')
        current_drops_count, err = drops_count(lpts_cmd)
        if err != 0:
            syslog.info('failed to get current drop count' + "% s" % err)
            break
        if current_drops_count != initial_drops_count :
            syslog.info("detected LPTS packet drops, proceeding with the process restart")
            err = process_restart(process_restart_cmd)
            if err != 0:
                syslog.info('failed to restart process with error: ' + "% s" % err)
            break 
        time.sleep(5)
        current_time = time.time()
        if initial_timestamp + detection_loop_timeout <= current_time:
            break

    # After the script is completed removing the file to indicate that the script is not running
    if err  == 0:
        syslog.info('Exited detection loop')
    else:
        syslog.info('Exited detection loop with error: ' + "% s" % err)
    sys.exit(err)
