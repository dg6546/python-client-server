Dev env:
Windows PowerShell
Python 3.8.1

Usage:
Gameserver.py:
python3 GameServer.py <Server_port> \"<filepathToUserInfo.txt>\"

e.g.
py GameServer.py 12000 "."
py GameServer.py 12000 "C:\Users\abc\Desktop\COMP3234_2A_2019\A1\code"

Caution: Quotation is needed in file path (" "). It can be both relative and absolute path. UserInfo.txt is not included in the path.


GameClient.py
python3 GameClient.py <Server_addr> <Server_port>

e.g.
python3 GameClient.py localhost 12000