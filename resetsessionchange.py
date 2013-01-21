# Credits to ferox2552@gmail.com
# Resets local session change ~ still useful sometimes
from log import LogError
from eve import eve
try:
    eve.session.nextSessionChange = blue.os.GetTime()
except:   
    LogError("Failed")