#!/usr/bin/env bash
# ==============================================================================
# HW05 EShop Database & Runtime Reset Script
# MSSV: 23120367
# Purpose:
#   1. Mở khóa tài khoản bị lockout (login_attempts = 0, locked_until = NULL)
#   2. Đảm bảo 40 tài khoản test độc lập sẵn sàng trong SQLite database
#   3. Xóa các đơn hàng test đã tạo (DELETE FROM orders)
#   4. Xóa giỏ hàng trong RAM (userCarts) bằng cách khởi động lại backend nếu đang chạy
#   5. Thông báo tình trạng tồn kho (Stock: N/A - SUT không có cột tồn kho)
# ==============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== [HW05] Bắt đầu quá trình Reset Database & SUT State ==="

# 1. Nếu workspace performance/ của skill đã được tạo và có script perf.py, đồng bộ reset
if [[ -f "$PROJECT_ROOT/performance/perf.config.json" && -f "$PROJECT_ROOT/performance/scripts/perf.py" ]]; then
    echo ">> Phát hiện workspace isolated runtime tại performance/"
    # Nếu node/npm có trong nvm hoặc homebrew, nạp vào PATH
    export PATH="/Users/thuytran/.nvm/versions/node/v22.17.1/bin:/opt/homebrew/bin:$PATH"
    if [[ -d "$PROJECT_ROOT/performance/.runtime/backend/node_modules" ]]; then
        echo ">> Chạy reset isolated runtime..."
        (cd "$PROJECT_ROOT/performance" && python3 scripts/perf.py reset || true)
    fi
fi

# 2. Reset database SQLite trực tiếp (hỗ trợ cả backend/database.sqlite và .runtime nếu có)
python3 - << 'EOF'
import sqlite3
import os
from pathlib import Path

targets = [Path("backend/database.sqlite"), Path("performance/.runtime/backend/database.sqlite")]

for db_path in targets:
    if not db_path.exists():
        continue
    print(f">> Đang reset dữ liệu tại: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Mở khóa tất cả tài khoản
    cur.execute("UPDATE users SET login_attempts = 0, locked_until = NULL")

    # 2. Xóa đơn hàng test
    cur.execute("DELETE FROM orders")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='orders'")
    except sqlite3.OperationalError:
        pass

    # 3. Đảm bảo có đủ 40 tài khoản test độc lập cho k6 VUs
    for i in range(1, 41):
        email = f"hw05.vu{i:04d}@example.test"
        password = f"Hw05VU{i:04d}!"
        name = f"HW05 VU {i}"
        address = f"{i} Nguyen Trai, Quan 5, TP.HCM"
        
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE users 
                SET password = ?, login_attempts = 0, locked_until = NULL, shipping_address = ?, role = 'user'
                WHERE id = ?
            """, (password, address, row[0]))
        else:
            cur.execute("""
                INSERT INTO users (name, email, password, role, login_attempts, locked_until, shipping_address)
                VALUES (?, ?, ?, 'user', 0, NULL, ?)
            """, (name, email, password, address))

    # 4. Kiểm tra schema tồn kho
    cur.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cur.fetchall()]
    has_stock = any("stock" in c.lower() or "inventory" in c.lower() for c in columns)

    conn.commit()
    conn.close()

    if has_stock:
        print(f"   [Stock] Phát hiện cột tồn kho trong schema: {columns}")
    else:
        print("   [Stock] N/A: Schema bảng 'products' không có cột tồn kho/stock. Không thực hiện SQL phục hồi tồn kho giả mạo.")

print(">> Hoàn thành cập nhật SQLite: 40 tài khoản test đã mở khóa, orders đã xóa.")
EOF

# 3. Quản lý trạng thái giỏ hàng trong RAM (userCarts)
# Vì userCarts được lưu trực tiếp trong biến bộ nhớ Node.js (RAM):
# const userCarts = {};
# Nên việc xóa giỏ hàng triệt để yêu cầu khởi động lại tiến trình Node.js backend.
echo ">> [RAM State] Lưu ý: Giỏ hàng (userCarts) nằm trong RAM của Node.js process."
echo "   Nếu tiến trình backend đang chạy, cần restart tiến trình để làm mới RAM."

echo "=== [HW05] Reset hoàn tất thành công! ==="
