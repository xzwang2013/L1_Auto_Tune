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
    if PortSrc == "":
        return "L1AutoTune - PortSrc can't be empty" 
    elif PortDst == "":
        return "L1AutoTune - PortDst can't be empty" 

    return ''

def run(PortSrc, PortDst):
    return AutoTune(PortSrc, PortDst, "DAC")

def reset():
    Reset()
    return True
