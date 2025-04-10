# การใช้ RAGDocs กับ Conda

คู่มือนี้จะแนะนำวิธีการติดตั้งและใช้งาน RAGDocs โดยใช้ Conda เป็นตัวจัดการแพ็กเกจและสภาพแวดล้อม

## ข้อกำหนดก่อนเริ่มต้น

1. [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda หรือ Anaconda)
2. [Qdrant](https://qdrant.tech/) (vector database สำหรับเก็บ embeddings)
3. [Ollama](https://ollama.ai/) (สำหรับสร้าง embeddings แบบ local) หรือ API key ของ OpenAI

## ขั้นตอนการติดตั้ง

1. **ให้สิทธิ์และรันสคริปต์ติดตั้ง**

   ```bash
   chmod +x install_conda.sh
   ./install_conda.sh
   ```

   สคริปต์จะทำสิ่งต่อไปนี้:
   - ตรวจสอบการติดตั้ง Conda
   - สร้างหรือใช้ environment ที่มีอยู่ (ค่าเริ่มต้นชื่อ 'ragdocs')
   - ติดตั้งแพ็กเกจที่จำเป็น
   - แสดงคำแนะนำสำหรับการตั้งค่า Claude Desktop

2. **ตั้งค่า Claude Desktop**

   เปิดไฟล์ค่าปรับแต่ง Claude Desktop:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   เพิ่มการตั้งค่าต่อไปนี้ (แทนที่ `/path/to/conda/bin/python` ด้วย path จริงที่แสดงในสคริปต์ติดตั้ง):

   ```json
   {
     "mcpServers": {
       "ragdocs": {
         "command": "/path/to/conda/bin/python",
         "args": [
           "-m",
           "ragdocs.server"
         ],
         "env": {
           "QDRANT_URL": "http://localhost:6333",
           "EMBEDDING_PROVIDER": "ollama",
           "OLLAMA_URL": "http://localhost:11434"
         }
       }
     }
   }
   ```

## การรันเซิร์ฟเวอร์ด้วยตัวเอง

สคริปต์ติดตั้งสร้างไฟล์ `run_conda.sh` ที่จะเปิดใช้งาน Conda environment และรันเซิร์ฟเวอร์:

```bash
./run_conda.sh
```

หากต้องการรันด้วยตัวเอง:

```bash
# เปิดใช้งาน conda environment
conda activate ragdocs

# รันเซิร์ฟเวอร์
python -m ragdocs.server
```

## การแก้ไขปัญหาเฉพาะสำหรับ Conda

1. **ไม่พบคำสั่ง conda**
   ```bash
   # ตรวจสอบว่าติดตั้ง conda แล้ว
   which conda

   # หากใช้ Anaconda/Miniconda แต่ไม่มีคำสั่ง conda ให้เพิ่มในตัวแปร PATH
   export PATH="$HOME/miniconda3/bin:$PATH"  # แก้ไข path ตามการติดตั้งจริง
   ```

2. **พบปัญหากับ environment conda**
   ```bash
   # สร้าง environment ใหม่
   conda create -n ragdocs python=3.10

   # ดู environments ที่มีอยู่
   conda env list

   # ลบ environment ที่มีปัญหา
   conda env remove -n ragdocs
   ```

3. **Python ใน Claude Desktop ไม่ได้ใช้ Conda environment**
   
   ตรวจสอบให้แน่ใจว่าใช้ path เต็มของ Python ใน Conda environment ในการตั้งค่า Claude Desktop:
   
   ```bash
   # หา path เต็มของ Python ใน environment
   conda activate ragdocs
   which python
   # ใช้ path ที่ได้ในการตั้งค่า "command" ใน claude_desktop_config.json
   ```

4. **แพ็กเกจบางตัวไม่ติดตั้งใน Conda**
   
   บางแพ็กเกจอาจไม่มีใน Conda repositories ซึ่งจะติดตั้งด้วย pip แทน:
   
   ```bash
   conda activate ragdocs
   pip install แพ็กเกจที่ต้องการ
   ```

## การตั้งค่า Environment Variables กับ Conda

คุณสามารถตั้งค่า environment variables สำหรับ Conda environment ได้:

```bash
# ตั้งค่าเฉพาะการรันปัจจุบัน
EMBEDDING_PROVIDER=openai python -m ragdocs.server

# ตั้งค่าถาวรใน environment
conda activate ragdocs
conda env config vars set EMBEDDING_PROVIDER=openai
conda activate ragdocs  # เปิดใช้งานใหม่เพื่อโหลดค่าตัวแปร
```

## คำแนะนำเพิ่มเติม

- ใช้ `conda list` เพื่อดูแพ็กเกจที่ติดตั้งใน environment
- ตรวจสอบ dependencies ด้วย `conda list --explicit > environment.txt`
- สร้าง environment จากไฟล์ด้วย `conda env create -f environment.yml`
