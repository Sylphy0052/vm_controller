#!/usr/bin/env python

import vmmodule as vm

info = vm.p()
print('Content-type: text/html; charset=UTF-8\r\n')
print('{0}'.format(info))
