import uncompyle2
import marshal

file = open("D:/rcode/func.marshal","rb")
outputfile = open("D:/rcode/func.py","wb")
func = marshal.load(file)

uncompyle2.uncompyle("2.7",func,out=outputfile)

file.close()
outputfile.close()