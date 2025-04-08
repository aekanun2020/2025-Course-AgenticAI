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
