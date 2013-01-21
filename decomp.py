# Credits go to wibiti

from nasty import nasty, UnjumbleString
import cPickle 
import blue
import struct
import imp
import os
import zipfile
import uthread

store_path="C:/python27/uncompyle2/eve-%.2f.%s/" % (boot.version, nasty.GetAppDataCompiledCodePath().build or boot.build)
    
root_store_path = store_path + "eve/"
script_store_path = store_path + "eve/client/script/"

(fileData, fileInfo,) = blue.win32.AtomicFileRead(nasty.compiledCodeFile)
datain = cPickle.loads(fileData)
code = cPickle.loads(datain[1])["code"]
for (k, v,) in code:
    c = v[0]
    c = UnjumbleString(c, True)
    ksplit = k[0].split(':/')
    filename = script_store_path  if ksplit[0] == "script" else  root_store_path
    filename += ksplit[1] +"c"
    print filename
    (dir,file) = os.path.split(filename)
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(filename,"wb") as x:
        mtime = os.path.getmtime(filename)
        mtime = struct.pack('<i', mtime)
        x.write(imp.get_magic() + mtime)
        x.write(c)
    

for root, dirs, files in os.walk(blue.paths.ResolvePath(u'lib:/')):
        for libname in files:
            zf = zipfile.ZipFile(os.path.join(root, libname), 'r')
            out = store_path + "lib/" + libname[:-4] + "/"
            for path in zf.namelist():
                tgt = os.path.join(out, path)[:-1]+"c"
                print tgt
                tgtdir = os.path.dirname(tgt)
                if not os.path.exists(tgtdir):
                    os.makedirs(tgtdir)
                with open(tgt, 'wb') as fp:
                    fp.write(UnjumbleString(zf.read(path), True))
					
uthread.new(uicore.cmd.CmdQuitGame)