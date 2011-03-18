import os, sys

FILES = [
    'luz_user_manual.txt',
    'getting_started.txt',
]

RST_EXE = 'rst2html'


for txtfile in FILES:
    filename, ext = os.path.splitext(txtfile)
    htmlfile = os.path.join('..', filename + '.html')
    cmd = '%s %s > %s' % (RST_EXE, txtfile, htmlfile)
    print 'Running:', cmd
    
    try:
        os.system(cmd)
    except Exception, e:
        print type(e), str(e)




