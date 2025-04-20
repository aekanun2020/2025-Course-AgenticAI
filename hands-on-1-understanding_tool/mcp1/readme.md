# คู่มือปฏิบัติการ Model Context Protocol (MCP)

## วัตถุประสงค์
เรียนรู้วิธีการใช้งาน Tool ของ Model Context Protocol (MCP) เบื้องต้น โดยการสร้างและทดสอบเซิร์ฟเวอร์ MCP อย่างง่ายที่สามารถตรวจสอบจำนวนเฉพาะได้

## ข้อกำหนดเบื้องต้น
- Python 3.10 หรือ 3.11
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
```

## ขั้นตอนที่ 2: สร้างเซิร์ฟเวอร์ MCP แรกของคุณ

1. สร้างโฟลเดอร์ใหม่สำหรับโปรเจกต์:

```bash
mkdir mcp1
cd mcp1
```

2. ดาวน์โหลด ทั้ง _prime_checker.py และ python prime_checker.py มาไว้ใน mcp1

## ขั้นตอนที่ 3: ทดสอบเซิร์ฟเวอร์ MCP แบบ JSON-RPC โดยตรง

1. เปิดเทอร์มินัลใหม่ เปิดใช้งานสภาพแวดล้อม และรันเซิร์ฟเวอร์โดยตรง:

```bash
conda activate mcp_env
cd mcp1
python _prime_checker.py
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
{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"prime://17"},"id":2}
```

**สิ่งที่เกิดขึ้น**: คำสั่งนี้ร้องขอให้เซิร์ฟเวอร์ตรวจสอบว่า 17 เป็นจำนวนเฉพาะหรือไม่ คุณควรได้รับผลลัพธ์ที่แสดงว่า 17 เป็นจำนวนเฉพาะ (true)

5. **ทดสอบเพิ่มเติม**:
ลองตรวจสอบตัวเลขที่ไม่ใช่จำนวนเฉพาะ:
```
{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"prime://171"},"id":3}
```

**สิ่งที่เกิดขึ้น**: ครั้งนี้ คุณควรได้รับผลลัพธ์ที่แสดงว่า 171 ไม่ใช่จำนวนเฉพาะ (false)

6. เมื่อเสร็จสิ้นการทดสอบ กด Ctrl+C เพื่อหยุดการทำงานของเซิร์ฟเวอร์

## ขั้นตอนที่ 5: ติดตั้งเซิร์ฟเวอร์ MCP กับ Claude Desktop

ก่อนการติดตั้ง โปรดสำรวจไฟล์ prime_checker.py ซึ่งเป็นไฟล์ใหม่ที่สร้างขึ้น โดยมี code ทั้งหมดตรงกับ _prime_checker.py ยกเว้น server object
หากคุณมี Claude Desktop ติดตั้งอยู่ในเครื่อง คุณสามารถเชื่อมต่อเซิร์ฟเวอร์ MCP (prime_checker.py) ของคุณกับ Claude ได้ดังนี้:

1. ใช้คำสั่ง mcp install:

```bash
mcp install prime_checker.py
```

2. จะมีข้อความยืนยันการติดตั้งสำเร็จปรากฏขึ้น:
```
INFO     Added server 'prime-checker' to Claude config
INFO     Successfully installed prime-checker in Claude app
```

3. แก้ไข configuration ให้เหมาะสมกับ environment ของท่าน
   (ตรวจสอบ environment ด้วยคำสั่ง which python แล้วนำผลลัพธ์ไปใส่แทนที่ /opt/anaconda3/envs/mcp_env/bin/python)
```
"prime-checker": {
      "command": "/opt/anaconda3/envs/mcp_env/bin/python",
      "args": [
        "/Users/grizzlymacbookpro/Desktop/mcp1/prime_checker.py"
      ]
    }
```
เค้าโครงของ configuration ที่เพิ่มเข้ามาจะเป็นแบบนี้ แต่จำเป็นต้องเปลี่ยนในส่วน "command" และ "args" ให้เหมาะสม
5. เปิดหรือรีสตาร์ท Claude Desktop เพื่อใช้งาน Prime Number Checker

## ขั้นตอนที่ 6: ทดสอบการใช้ tool "is_prime" บน Claude Desktop
