##############################################################################
#                                                                            #
# STAK Command name: L1AutoTuneCommand                                       #
#                                                                            #
# Purpose: The purpose of this command is to find best transceiver parameters#
# automatically on ethernet ports like 50/100/200/400 gig                    #
#                                                                            #
# This command is used in command sequencer on GUI                           #
#                                                                            #
# Usage: Run this command by providing list of arguments which need to be    #
#        configured under L1Test                                             #
#                                                                            #
##############################################################################

from StcPython import StcPython
from l1_auto_tune import AutoTune, Reset

def validate(PortSrc, PortDst):
    if PortSrc == None or PortDst == None:
        return "Port can't be None." 
    return ''

def run(PortSrc, PortDst):
    AutoTune(PortSrc, PortDst, "DAC")
    return True


def reset():
    Reset()
    return True
