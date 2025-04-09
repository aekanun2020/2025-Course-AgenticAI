# RAG Python for Claude Desktop

ระบบ RAG (Retrieval-Augmented Generation) สำหรับ Claude Desktop ที่สร้างด้วยภาษา Python เป็นการแปลงมาจาก Node.js version

## คุณสมบัติ

- ใช้ Model Context Protocol (MCP) เพื่อเชื่อมต่อกับ Claude Desktop
- รองรับการค้นหาเอกสารด้วย semantic search ผ่าน vector embeddings
- รองรับการเพิ่มเอกสารจาก URL และไดเรกทอรี
- รองรับไฟล์ PDF และไฟล์ข้อความหลายประเภท (txt, md, js, ts, py, java, c, cpp, h, hpp)
- รองรับ embedding ทั้งจาก Ollama และ OpenAI

## การติดตั้ง

### ติดตั้งด้วย Conda

1. สร้าง environment ใหม่:

```bash
conda create -n ragpython python=3.10
conda activate ragpython
```

2. ติดตั้ง PyMuPDF และ dependencies ที่จำเป็น:

```bash
conda install -c conda-forge pymupdf
pip install -r requirements.txt
```

### การตั้งค่า

1. คัดลอกไฟล์ตัวอย่างการตั้งค่า:

```bash
cp .env.example .env
```

2. แก้ไขไฟล์ `.env` ตามความต้องการ:

```
# Ollama Configuration (ค่าเริ่มต้น)
OLLAMA_URL=http://localhost:11434
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text

# Qdrant Configuration
QDRANT_URL=http://127.0.0.1:6333

# หากต้องการใช้ OpenAI embeddings ให้แก้ไขดังนี้
# EMBEDDING_PROVIDER=openai
# EMBEDDING_MODEL=text-embedding-3-small
# OPENAI_API_KEY=your-openai-api-key
```

### การติดตั้ง Qdrant

1. ติดตั้ง Qdrant ด้วย Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### การติดตั้ง Ollama (หากใช้ Ollama embeddings)

1. ติดตั้ง Ollama จาก [ollama.ai](https://ollama.ai/)

2. ดาวน์โหลดโมเดล embedding:

```bash
ollama pull nomic-embed-text
```

## การตั้งค่า Claude Desktop

1. เปิด Claude Desktop

2. ไปที่การตั้งค่า (Settings) > ความสามารถเพิ่มเติม (Advanced Features)

3. เปิดใช้งาน Model Context Protocol (MCP)

4. เลือก "รัน MCP server ภายนอก" (Run external MCP server)

5. ตั้งค่าคำสั่งเริ่มต้น (Startup command) เป็น:

```
python /Users/grizzlymacbookpro/Desktop/test/ragpython/main.py
```

(ปรับเส้นทางตามที่คุณเก็บโค้ด)

## การใช้งาน

1. เริ่มต้น server:

```bash
python main.py
```

2. เปิด Claude Desktop ที่ตั้งค่าไว้ให้ใช้ MCP server ภายนอก

3. ใช้เครื่องมือที่มีให้ใน Claude Desktop:
   - `add_documentation` - เพิ่มเอกสารจาก URL
   - `search_documentation` - ค้นหาข้อมูลในเอกสาร
   - `list_sources` - แสดงรายการแหล่งข้อมูลที่มีอยู่
   - `add_directory` - เพิ่มไฟล์ทั้งหมดในไดเรกทอรี

## ตัวอย่างการใช้งาน

### เพิ่มเอกสารจาก URL

```
@add_documentation({"url": "https://docs.python.org/3/tutorial/index.html"})
```

### ค้นหาข้อมูล

```
@search_documentation({"query": "Python list comprehension", "limit": 5})
```

### แสดงรายการแหล่งข้อมูล

```
@list_sources({})
```

### เพิ่มไฟล์จากไดเรกทอรี

```
@add_directory({"path": "/path/to/your/documents"})
```

## ข้อจำกัด

- รองรับเฉพาะไฟล์ PDF และไฟล์ข้อความบางประเภท
- ไม่รองรับ pagination สำหรับคอลเลกชันขนาดใหญ่
- ไม่มีการจัดการสิทธิ์การเข้าถึง

## ข้อเสนอแนะการพัฒนาในอนาคต

- เพิ่มการรองรับไฟล์ประเภทอื่น (docx, xlsx, pptx)
- เพิ่มฟีเจอร์ Prompts และ Resources ตาม MCP specification
- ปรับปรุงประสิทธิภาพการประมวลผลไฟล์ขนาดใหญ่
- เพิ่มการรองรับ pagination

## ลิขสิทธิ์

© 2025 - ใช้ตามต้องการ
