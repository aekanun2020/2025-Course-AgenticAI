#!/usr/bin/env python3
import json
import sys
import os
from dotenv import load_dotenv
import asyncio
import logging
import mysql.connector
from mysql.connector import Error
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from pydantic import AnyUrl
import re

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mysql_mcp_server")

app = Server("mysql_mcp_server")

class DBConfig:
    def __init__(self):
        self.config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "database": os.getenv("MYSQL_DATABASE"),
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD")
        }
        self.connection = None

    def get_connection(self):
        try:
            if not self.connection:
                self.connection = mysql.connector.connect(
                    host=self.config["host"],
                    port=self.config["port"],
                    database=self.config["database"],
                    user=self.config["user"],
                    password=self.config["password"]
                )
            return self.connection
        except Error as e:
            self.connection = None
            logger.error(f"Error connecting to MySQL: {e}")
            raise

class SQLValidator:
    @staticmethod
    def is_read_only_query(query: str) -> bool:
        # ทำความสะอาด query
        clean_query = query.strip().upper()
        
        # รายการคำสั่งที่อนุญาต
        allowed_statements = [
            'SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC'
        ]
        
        # รายการคำสั่งที่ไม่อนุญาต
        forbidden_statements = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
            'ALTER', 'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE'
        ]
        
        # ตรวจสอบว่าเริ่มต้นด้วยคำสั่งที่อนุญาตหรือไม่
        starts_with_allowed = any(clean_query.startswith(stmt) for stmt in allowed_statements)
        if not starts_with_allowed:
            return False
            
        # ตรวจสอบว่ามีคำสั่งต้องห้ามหรือไม่
        contains_forbidden = any(stmt in clean_query for stmt in forbidden_statements)
        if contains_forbidden:
            return False
            
        # ตรวจสอบเพิ่มเติมสำหรับ SQL Injection
        has_dangerous_chars = re.search(r';\s*\w+', clean_query)  # ตรวจหา semicolon ที่ตามด้วยคำสั่ง
        if has_dangerous_chars:
            return False
            
        return True

db = DBConfig()
sql_validator = SQLValidator()

@app.list_resources()
async def list_resources() -> list[Resource]:
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
            (db.config["database"],)
        )
        tables = cursor.fetchall()
        cursor.close()
        
        return [
            Resource(
                uri=f"mysql://{table[0]}/data",
                name=f"Table: {table[0]}",
                mimeType="application/json",
                description=f"Data in table {table[0]}"
            )
            for table in tables
        ]
    except Exception as e:
        logger.error(f"Failed to list resources: {str(e)}")
        return []

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    uri_str = str(uri)
    if not uri_str.startswith("mysql://"):
        raise ValueError(f"Invalid URI scheme: {uri_str}")
        
    table = uri_str[8:].split('/')[0]
    query = f"SELECT * FROM `{table}` LIMIT 100"
    
    if not sql_validator.is_read_only_query(query):
        raise ValueError("Only SELECT queries are allowed")
        
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        result = [",".join(map(lambda x: str(x) if x is not None else "NULL", row)) for row in rows]
        return "\n".join([",".join(columns)] + result)
    except Exception as e:
        logger.error(f"Error reading table {table}: {str(e)}")
        raise RuntimeError(f"Database error: {str(e)}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="execute_query",
            description="Execute a read-only SQL query and return the results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute (must be SELECT only)"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="preview_table",
            description="Get a preview of the data in a table.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to preview"},
                    "limit": {"type": "integer", "description": "Maximum number of rows to return (default: 10)"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="get_database_info",
            description="Get general information about the database.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="refresh_db_cache",
            description="Refresh the database schema cache.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "execute_query":
        return await execute_query(arguments)
    elif name == "preview_table":
        return await preview_table(arguments)
    elif name == "get_database_info":
        return await get_database_info()
    elif name == "refresh_db_cache":
        return await refresh_db_cache()
    else:
        raise ValueError(f"Unknown tool: {name}")

async def execute_query(arguments: dict) -> list[TextContent]:
    query = arguments.get("query")
    if not query:
        return [TextContent(type="text", text="Error: Query is required")]

    # ตรวจสอบว่าเป็น read-only query
    if not sql_validator.is_read_only_query(query):
        return [TextContent(type="text", text="Error: Only SELECT queries are allowed")]

    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        cursor.close()
        
        if not columns:
            return [TextContent(type="text", text="Query executed successfully. No results returned.")]
        
        # Format the output as a nice table
        result = []
        result.append(" | ".join(columns))
        result.append("-" * len(" | ".join(columns)))
        
        for row in rows:
            result.append(" | ".join(str(val) if val is not None else "NULL" for val in row))
        
        return [TextContent(type="text", text="\n".join(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def preview_table(arguments: dict) -> list[TextContent]:
    table_name = arguments.get("table_name")
    limit = arguments.get("limit", 10)
    
    if not table_name:
        return [TextContent(type="text", text="Error: Table name is required")]
    
    try:
        query = f"SELECT * FROM `{table_name}` LIMIT {limit}"
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        if not rows:
            return [TextContent(type="text", text=f"Table '{table_name}' is empty or does not exist")]
        
        # Format the output as a nice table
        result = []
        result.append(" | ".join(columns))
        result.append("-" * len(" | ".join(columns)))
        
        for row in rows:
            result.append(" | ".join(str(val) if val is not None else "NULL" for val in row))
        
        return [TextContent(type="text", text="\n".join(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error previewing table: {str(e)}")]

async def get_database_info() -> list[TextContent]:
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
            (db.config["database"],)
        )
        tables = cursor.fetchall()
        
        # Build database info
        db_info = [f"Database: {db.config['database']}"]
        db_info.append(f"Number of tables: {len(tables)}")
        db_info.append("\nTables:")
        
        # Get details for each table
        for table in tables:
            table_name = table[0]
            
            # Get column information
            cursor.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
                """,
                (db.config["database"], table_name)
            )
            columns = cursor.fetchall()
            
            # Get table row count (approximate)
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` LIMIT 1000")
            row_count = cursor.fetchone()[0]
            count_msg = f"{row_count}+" if row_count >= 1000 else str(row_count)
            
            db_info.append(f"- {table_name}: {len(columns)} columns, ~{count_msg} rows")
            
            # Add column details
            db_info.append("  Columns:")
            for col in columns:
                nullable = "NULL" if col[3] == "YES" else "NOT NULL"
                key = f"PRIMARY KEY" if col[4] == "PRI" else f"{col[4]}" if col[4] else ""
                default = f"DEFAULT {col[5]}" if col[5] is not None else ""
                extra = col[6]
                
                db_info.append(f"  - {col[0]}: {col[2]} {nullable} {key} {default} {extra}")
            
            db_info.append("")  # Empty line between tables
        
        cursor.close()
        return [TextContent(type="text", text="\n".join(db_info))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting database info: {str(e)}")]

# Placeholder for cache
db_schema_cache = None

async def refresh_db_cache() -> list[TextContent]:
    global db_schema_cache
    db_schema_cache = None  # Reset cache
    return [TextContent(type="text", text="Database schema cache refreshed successfully.")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
