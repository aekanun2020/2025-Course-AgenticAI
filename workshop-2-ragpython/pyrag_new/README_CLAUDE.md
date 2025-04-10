# การติดตั้ง RAGDocs สำหรับ Claude Desktop

คู่มือนี้จะแนะนำวิธีการติดตั้ง RAGDocs เพื่อใช้งานกับ Claude Desktop

## ข้อกำหนดก่อนเริ่มต้น

1. Python 3.10 หรือสูงกว่า
2. [Qdrant](https://qdrant.tech/) (vector database สำหรับเก็บ embeddings)
3. [Ollama](https://ollama.ai/) (สำหรับสร้าง embeddings แบบ local) หรือ API key ของ OpenAI

## ขั้นตอนการติดตั้ง

1. **ดาวน์โหลดและติดตั้ง**

   ```bash
   # ดาวน์โหลดโค้ด (หรือใช้ zip file ที่ให้ไว้)
   git clone https://github.com/your-username/ragdocs.git
   cd ragdocs

   # ให้สิทธิ์รันไฟล์ติดตั้ง
   chmod +x install.sh

   # รันไฟล์ติดตั้ง
   ./install.sh
   ```

2. **ตั้งค่า Claude Desktop**

   เปิดไฟล์ค่าปรับแต่ง Claude Desktop ที่:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   เพิ่มการตั้งค่าต่อไปนี้:

   ```json
   {
     "mcpServers": {
       "ragdocs": {
         "command": "python",
         "args": [
           "-m",
           "ragdocs.server"
         ],
         "env": {
           "QDRANT_URL": "http://192.168.1.133:6333",
           "QDRANT_COLLECTION": "documentation",
           "EMBEDDING_PROVIDER": "ollama",
           "OLLAMA_URL": "http://192.168.1.133:11434",
           "OLLAMA_HOST": "http://192.168.1.133:11434"
         }
       }
     }
   }
   ```

   > **หมายเหตุ**: แก้ไข URL ให้ตรงกับที่อยู่ของ Qdrant และ Ollama ของคุณ

3. **เริ่มต้นใช้งาน**

   - รีสตาร์ท Claude Desktop
   - ตรวจสอบว่ามีไอคอนเครื่องมือ (รูปค้อน) ปรากฏที่มุมขวาล่างหรือไม่
   - หากไอคอนปรากฏแสดงว่าเซิร์ฟเวอร์ทำงานปกติ

## คำสั่งที่สามารถใช้กับ Claude

เมื่อติดตั้งเสร็จแล้ว คุณสามารถขอให้ Claude ทำสิ่งต่อไปนี้:

1. **เพิ่มเอกสารจาก URL**
   ```
   ช่วยเพิ่มเอกสารจาก URL นี้: https://example.com/docs
   ```

2. **ค้นหาข้อมูลในเอกสาร**
   ```
   ช่วยค้นหาข้อมูลเกี่ยวกับ "การติดตั้ง Python" ในเอกสารที่มีอยู่
   ```

3. **แสดงรายการแหล่งข้อมูล**
   ```
   แสดงรายการแหล่งข้อมูลเอกสารทั้งหมดที่มีอยู่
   ```

4. **เพิ่มไฟล์จากไดเร็กทอรี**
   ```
   ช่วยเพิ่มเอกสารจากไดเร็กทอรี: /path/to/documents
   ```

## การแก้ไขปัญหา

1. **ไม่เห็นไอคอนเครื่องมือใน Claude Desktop**
   - ตรวจสอบว่า Claude Desktop เวอร์ชันล่าสุด
   - ตรวจสอบไฟล์ค่าปรับแต่ง claude_desktop_config.json
   - ดูบันทึกใน ~/Library/Logs/Claude/mcp*.log (macOS) หรือ %APPDATA%\Claude\logs\mcp*.log (Windows)

2. **เซิร์ฟเวอร์ไม่ทำงาน**
   - ตรวจสอบว่า Qdrant และ Ollama ทำงานอยู่
   - รันเซิร์ฟเวอร์ด้วยคำสั่ง `python -m ragdocs.server --debug` เพื่อดูข้อผิดพลาด

3. **ปัญหาการเชื่อมต่อ Qdrant หรือ Ollama**
   - ตรวจสอบ URL และพอร์ตที่ถูกต้อง
   - ตรวจสอบว่าบริการทั้งสองทำงานอยู่

4. **ปัญหาการติดตั้งแพ็กเกจ**
   - รันคำสั่ง `pip install -r requirements.txt` อีกครั้ง
   - ตรวจสอบข้อผิดพลาดในการติดตั้ง

## ค่าปรับแต่งเพิ่มเติม

หากต้องการเปลี่ยนการตั้งค่าเพิ่มเติม คุณสามารถปรับแต่งค่าต่างๆ ได้ในส่วน `env` ของ claude_desktop_config.json:

```json
"env": {
  "QDRANT_URL": "http://localhost:6333",
  "EMBEDDING_PROVIDER": "openai",  // เปลี่ยนเป็น "openai" หากต้องการใช้ OpenAI
  "OPENAI_API_KEY": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "EMBEDDING_MODEL": "text-embedding-3-small"  // โมเดล OpenAI
}
```

## การอัพเดต

หากต้องการอัพเดตเป็นเวอร์ชันใหม่:

```bash
# ดึงโค้ดล่าสุด
git pull

# ติดตั้งอีกครั้ง
./install.sh
```
