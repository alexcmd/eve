import marshal
import macho
import sys
import dis
import hashlib
def _GPSTransport__Execute(self, signedFunc, context):
	marshaled, verified = macho.Verify(signedFunc)
	if not verified:
		raise RuntimeError('Failed to verify initial function blobs')
	func = marshal.loads(marshaled)

	class WriteBuffer:

		def __init__(self):
			self.buffer = ''

		def write(self, text):
			self.buffer += text

	output = WriteBuffer()
	temp = sys.stdout
	temp2 = sys.stderr
	sys.stdout = output
	sys.stderr = output
	try:
		if macho.mode != 'client':
			raise RuntimeError('H4x0r won by calling GPS::__Execute on the server :(')
		funcResult = eval(func, globals(), context)
	except:
		funcResult = {}
		import traceback
		exctype, exc, tb = sys.exc_info()
		try:
			traceback.print_exception(exctype, exc, tb)
		finally:
			exctype = None
			exc = None
			tb = None

		sys.exc_clear()
	finally:
		sys.stdout = temp
		sys.stderr = temp2
	try:	
		FILE = open("D:/rcode/funcResult.txt","wt")
		for k in funcResult:
			FILE.write(str(k) + " "+ str(funcResult[k]) + "\n")
		FILE.close()
		
		FILE2 = open("D:/rcode/func.marshal","wb")
		marshal.dump(func, FILE2)
		FILE2.close()
		
		FILE3 = open("D:/rcode/func.marshal","rb").read()
		FILE4 = open("D:/rcode/rg hash.txt","wb")
		FILE4.write(hashlib.sha1(FILE3).hexdigest())
		FILE3.close()
		FILE4.close()
		
	except:
		pass
	return (output.buffer, funcResult)
 
 
import gps
gps.GPSTransport._GPSTransport__Execute = _GPSTransport__Execute