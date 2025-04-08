# คู่มือปฏิบัติการ Model Context Protocol (MCP)

## วัตถุประสงค์
เรียนรู้วิธีการใช้งาน Model Context Protocol (MCP) เบื้องต้น โดยการสร้างและทดสอบเซิร์ฟเวอร์ MCP อย่างง่ายที่สามารถตรวจสอบจำนวนเฉพาะได้

## บทนำ
Model Context Protocol (MCP) คือโปรโตคอล (protocol) ที่พัฒนาโดย Anthropic เพื่อทำให้การเชื่อมต่อระหว่างโมเดลภาษาขนาดใหญ่ (Large Language Models หรือ LLMs) กับข้อมูลภายนอกเป็นมาตรฐานเดียวกัน 

MCP เป็นโปรโตคอลแบบโอเพนซอร์ส (open-source) ไม่ได้จำกัดเฉพาะ Claude เท่านั้น Anthropic ต้องการให้มีการนำไปใช้อย่างกว้างขวางและรับการสนับสนุนจากชุมชน

## ข้อกำหนดเบื้องต้น
- Python 3.8 หรือใหม่กว่า (แนะนำ Python 3.10 หรือ 3.11)
- Conda หรือ Miniconda

## ขั้นตอนที่ 1: การตั้งค่าสภาพแวดล้อม

1. เปิดเทอร์มินัล
2. สร้างและเปิดใช้งานสภาพแวดล้อม Conda ใหม่:

```bash
conda create -n mcp_env python=3.10
conda activate mcp_env
```

3. ติดตั้ง MCP SDK และเครื่องมือที่จำเป็น:

```bash
pip install uv
pip install mcp==1.3.0
pip install "mcp[cli]"
```

4. ตรวจสอบการติดตั้ง:

```bash
pip list | grep -E "mcp|uv"
```

คุณควรจะเห็นผลลัพธ์ประมาณนี้:
```
mcp            1.3.0
uv             0.6.5
uvicorn        0.34.0
```

## ขั้นตอนที่ 2: สร้างเซิร์ฟเวอร์ MCP แรกของคุณ

1. สร้างโฟลเดอร์ใหม่สำหรับโปรเจกต์:

```bash
mkdir mcp1
cd mcp1
```

2. สร้างไฟล์ `prime_checker.py` ด้วยโค้ดต่อไปนี้:

```python
#!/usr/bin/env python
"""
Prime Number Checker MCP Tool - ใช้ FastMCP ตามแนวทางที่แนะนำโดย Anthropic
"""
from typing import Optional
import logging
# Import FastMCP จาก MCP SDK
from mcp.server.fastmcp import FastMCP
# ตั้งค่า logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fastmcp-prime-checker")
# สร้าง FastMCP server instance
mcp = FastMCP("prime-checker")
@mcp.tool()
async def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
if __name__ == "__main__":
    logger.info("เริ่มต้น FastMCP Prime Number Checker Server...")
    
    # รัน MCP server ด้วย FastMCP
    mcp.run(transport='stdio')
```

โค้ดนี้จะสร้างเซิร์ฟเวอร์ MCP ที่มีเครื่องมือ (tool) สำหรับตรวจสอบว่าตัวเลขที่กำหนดเป็นจำนวนเฉพาะหรือไม่

## ขั้นตอนที่ 3: รันและทดสอบเซิร์ฟเวอร์ MCP ด้วย MCP Inspector

1. รันคำสั่งต่อไปนี้เพื่อเริ่ม MCP Inspector:

```bash
mcp dev prime_checker.py
```

2. เบราว์เซอร์จะเปิดขึ้นที่ http://localhost:5173 แสดง MCP Inspector
3. คลิกที่ปุ่ม "List Resources" ในแท็บ Resources

>[!NOTE]
>หากคุณไม่เห็นทรัพยากรใดๆ ปรากฏหลังจากกดปุ่ม "List Resources" (แสดงเป็น `"resources": []`) อาจเป็นเพราะปัญหาเวอร์ชันหรือการตั้งค่า ให้ลองวิธีที่ 4 แทน

## ขั้นตอนที่ 4: ทดสอบเซิร์ฟเวอร์ MCP แบบ JSON-RPC โดยตรง

1. เปิดเทอร์มินัลใหม่ เปิดใช้งานสภาพแวดล้อม และรันเซิร์ฟเวอร์โดยตรง:

```bash
conda activate mcp_env
cd mcp1
python prime_checker.py
```

คุณควรเห็นข้อความ "เริ่มต้น FastMCP Prime Number Checker Server..." แสดงว่าเซิร์ฟเวอร์เริ่มทำงานแล้ว

2. **การเริ่มต้นเซสชัน (Initialize Session)**:
พิมพ์ข้อความ JSON-RPC ต่อไปนี้เข้าไปในเทอร์มินัลเดียวกัน:
```
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"tinyclient","version":"1.0"}},"id":1}
```

**สิ่งที่เกิดขึ้น**: คำสั่งนี้แจ้งเซิร์ฟเวอร์ว่าคุณต้องการเริ่มเซสชันใหม่ เซิร์ฟเวอร์จะตอบกลับด้วยเวอร์ชัน ความสามารถ และข้อมูลอื่นๆ

3. **การยืนยันการเริ่มต้นเซสชัน (Complete Initialization)**:
หลังจากได้รับข้อความตอบกลับจากเซิร์ฟเวอร์ ให้พิมพ์:
```
{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}
```

**สิ่งที่เกิดขึ้น**: คำสั่งนี้แจ้งเซิร์ฟเวอร์ว่าการเริ่มต้นเซสชันเสร็จสมบูรณ์ และคุณพร้อมที่จะส่งคำขอไปยังทรัพยากรต่างๆ แล้ว

4. **ทดสอบเครื่องมือ (Tool)**:
ตรวจสอบว่า 17 เป็นจำนวนเฉพาะหรือไม่:
```
{"jsonrpc":"2.0","method":"tools/is_prime","params":{"n":17},"id":2}
```

**สิ่งที่เกิดขึ้น**: คำสั่งนี้ร้องขอให้เซิร์ฟเวอร์ตรวจสอบว่า 17 เป็นจำนวนเฉพาะหรือไม่ คุณควรได้รับผลลัพธ์ที่แสดงว่า 17 เป็นจำนวนเฉพาะ (true)

5. **ทดสอบเพิ่มเติม**:
ลองตรวจสอบตัวเลขที่ไม่ใช่จำนวนเฉพาะ:
```
{"jsonrpc":"2.0","method":"tools/is_prime","params":{"n":171},"id":3}
```

**สิ่งที่เกิดขึ้น**: ครั้งนี้ คุณควรได้รับผลลัพธ์ที่แสดงว่า 171 ไม่ใช่จำนวนเฉพาะ (false)

6. เมื่อเสร็จสิ้นการทดสอบ กด Ctrl+C เพื่อหยุดการทำงานของเซิร์ฟเวอร์

## ขั้นตอนที่ 5: ติดตั้งเซิร์ฟเวอร์ MCP กับ Claude Desktop

หากคุณมี Claude Desktop ติดตั้งอยู่ในเครื่อง คุณสามารถเชื่อมต่อเซิร์ฟเวอร์ MCP ของคุณกับ Claude ได้ดังนี้:

1. ใช้คำสั่ง mcp install:

```bash
mcp install prime_checker.py
```

2. จะมีข้อความยืนยันการติดตั้งสำเร็จปรากฏขึ้น:
```
INFO     Added server 'prime-checker' to Claude config
INFO     Successfully installed prime-checker in Claude app
```

3. เปิดหรือรีสตาร์ท Claude Desktop เพื่อใช้งาน Prime Number Checker

## แก้ไขปัญหาที่พบบ่อย

### ปัญหา: ไม่พบทรัพยากรหรือเครื่องมือใน MCP Inspector
- **สาเหตุที่เป็นไปได้**: เวอร์ชันไม่เข้ากัน, การตั้งค่าไม่ถูกต้อง, โค้ดมีข้อผิดพลาด
- **วิธีแก้ไข**: ลองทดสอบโดยตรงผ่าน JSON-RPC (ขั้นตอนที่ 4), ตรวจสอบโค้ดเพื่อหาข้อผิดพลาด

### ปัญหา: ข้อความ "command not found: mcp" 
- **สาเหตุที่เป็นไปได้**: สภาพแวดล้อม conda ไม่ได้เปิดใช้งาน
- **วิธีแก้ไข**: รัน `conda activate mcp_env` ก่อนใช้คำสั่ง mcp

### ปัญหา: ข้อความ if **name** == "__main__"
- **สาเหตุที่เป็นไปได้**: มีการพิมพ์ผิดในโค้ด Python
- **วิธีแก้ไข**: ตรวจสอบว่าใช้ `if __name__ == "__main__":` (มีขีดล่างสองตัวทั้งด้านหน้าและด้านหลัง)

## สรุป
ขณะนี้ คุณได้เรียนรู้วิธีการสร้างและทดสอบเซิร์ฟเวอร์ MCP อย่างง่าย โดยผ่านการใช้งาน MCP Inspector และการสื่อสารโดยตรงผ่าน JSON-RPC นี่เป็นพื้นฐานสำคัญที่จะช่วยให้คุณพัฒนาแอปพลิเคชัน MCP ที่ซับซ้อนมากขึ้นในอนาคต!

## คำศัพท์ที่สำคัญ
- **MCP (Model Context Protocol)**: โปรโตคอลที่ช่วยให้ LLMs เข้าถึงข้อมูลภายนอกและเครื่องมือต่างๆ
- **MCP Server**: โปรแกรมที่เปิดให้เข้าถึงทรัพยากรหรือเครื่องมือเฉพาะทาง
- **Tool**: เครื่องมือหรือฟังก์ชันที่ MCP Server เปิดให้ใช้งาน (เช่น is_prime)
- **JSON-RPC**: โปรโตคอลการเรียกใช้งานระยะไกลที่ใช้ JSON สำหรับการส่งข้อมูล
- **Transport**: วิธีการสื่อสารระหว่าง MCP Client กับ MCP Server (เช่น stdio, sse)