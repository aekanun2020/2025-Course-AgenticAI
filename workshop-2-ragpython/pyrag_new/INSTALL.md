# ขั้นตอนการติดตั้ง RAGDocs สำหรับ Claude Desktop

เอกสารนี้จะอธิบายขั้นตอนการติดตั้ง RAGDocs เพื่อใช้งานร่วมกับ Claude Desktop

## 1. ติดตั้งแพ็กเกจที่จำเป็น

```bash
# สร้าง virtual environment (แนะนำ)
python -m venv venv

# เปิดใช้งาน virtual environment
# บน Windows
venv\Scripts\activate
# บน macOS/Linux
source venv/bin/activate

# ติดตั้งแพ็กเกจที่จำเป็น
pip install -r requirements.txt
```

## 2. ติดตั้ง RAGDocs แพ็กเกจ

```bash
# ติดตั้งแพ็กเกจ RAGDocs แบบพัฒนา
pip install -e .
```

## 3. ตั้งค่า Claude Desktop

1. เปิดไฟล์ค่าปรับแต่ง Claude Desktop ที่:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. เพิ่มค่าปรับแต่งต่อไปนี้ในส่วน `mcpServers`:

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
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_COLLECTION": "documentation",
        "EMBEDDING_PROVIDER": "ollama",
        "OLLAMA_URL": "http://localhost:11434"
      }
    }
  }
}
```

> **หมายเหตุ**: แก้ไข URL ให้ตรงกับที่อยู่ของ Qdrant และ Ollama ของคุณ

## 4. ตรวจสอบการทำงาน

1. รันเซิร์ฟเวอร์ด้วยตัวเอง (ทดสอบ):
   ```bash
   python -m ragdocs.server
   ```

   หากทำงานถูกต้อง คุณจะเห็นข้อความ "Starting RAGDocs FastMCP Server"

2. เริ่มต้น Claude Desktop และตรวจสอบว่าเห็นไอคอนเครื่องมือ (รูปค้อน) ที่มุมขวาล่างหรือไม่ หากเห็น แสดงว่าเซิร์ฟเวอร์ทำงานปกติ

## 5. หากพบปัญหา

### ตรวจสอบบันทึก Claude Desktop
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Windows
type "%APPDATA%\Claude\logs\mcp*.log"
```

### รันเซิร์ฟเวอร์ด้วย Debug Mode
```bash
python -m ragdocs.server --debug
```

### ตรวจสอบว่าติดตั้งแพ็กเกจครบหรือไม่
```bash
pip list | grep -E "mcp|qdrant|aiohttp"
```

## 6. สำหรับ Environment Variables อื่นๆ

- `EMBEDDING_PROVIDER`: เลือก "ollama" หรือ "openai"
- `EMBEDDING_MODEL`: โมเดลสำหรับสร้าง embeddings (ค่าเริ่มต้น: "nomic-embed-text")
- `OPENAI_API_KEY`: API key สำหรับ OpenAI (ถ้าใช้ OpenAI เป็น provider)
