#
# AITPATH   version 1.0 / 14.6.20
#
# Copyright (c) 2019-2020, AI-Technologies - Rainer Wallwitz
# All rights reserved.
#
#
#
# This file is meant to be located inside the ipython extension folder, 
#
#     macos       : 'users/USERNAME/anaconda3/lib/python 3.7/site-packages/IPython/extensions'
#     win32       : C:\ProgramData\Anaconda3\lib\site-packages\IPython\extensions
#
# and sets the path ensuring the application libs are found by ipython for execution.
#

import sys

def operatingSystem(): 
    azure = False
    # windows=win32  macos=darwin
    return 'darwin' if sys.platform=='darwin' else ('azure' if azure else 'windows' )

def sysUser():
    platform = operatingSystem()
    if platform=='darwin':
        sys_user = 'USERNAME'
    else: # 'win32'
        sys_user = 'USERNAME'
    return sys_user
sys_user = sysUser()

sys.path.append('/users/'+sys_user+'/Py/SunFlowLibs')

