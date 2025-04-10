# MySQL MCP Server

MCP (Model Context Protocol) server ที่เชื่อมต่อกับฐานข้อมูล MySQL

## การติดตั้ง

### การตั้งค่า Conda Environment

```bash
# สร้าง conda environment
conda env create -f environment.yml

# เปิดใช้งาน environment
conda activate mcp-mysql
```

### การตั้งค่าการเชื่อมต่อกับฐานข้อมูล

คัดลอกไฟล์ `.env` และปรับแต่งค่าตามการตั้งค่าฐานข้อมูลของคุณ:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=your_database
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
```

## การใช้งาน

### การเริ่มต้นเซิร์ฟเวอร์

```bash
python server.py
```

### เชื่อมต่อกับ Claude Desktop

1. แก้ไขไฟล์ `claude_desktop_config.json` (อยู่ที่ `~/Library/Application Support/Claude/claude_desktop_config.json` บน macOS หรือ `%APPDATA%\Claude\claude_desktop_config.json` บน Windows):

```json
{
  "mcpServers": {
    "mysql": {
      "command": "conda",
      "args": ["run", "-n", "mcp-mysql", "python", "/path/to/new_mcp_mysql/server.py"]
    }
  }
}
```

2. รีสตาร์ท Claude Desktop เพื่อโหลดการตั้งค่าใหม่

## ความสามารถ

MySQL MCP Server มีเครื่องมือต่อไปนี้:

1. **execute_query**: ใช้สำหรับรันคำสั่ง SQL ที่อ่านข้อมูลเท่านั้น (SELECT, SHOW, DESCRIBE)
2. **preview_table**: ดูตัวอย่างข้อมูลในตาราง
3. **get_database_info**: ดูข้อมูลโครงสร้างของฐานข้อมูล
4. **refresh_db_cache**: รีเฟรชข้อมูลแคชของโครงสร้างฐานข้อมูล

## ข้อจำกัด

- รันได้เฉพาะคำสั่ง SQL ที่อ่านข้อมูลเท่านั้น (SELECT, SHOW, DESCRIBE)
- ไม่สามารถแก้ไขข้อมูลหรือโครงสร้างฐานข้อมูลได้
