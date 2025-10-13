"""
Main entry point for the AutoData package.

This module implements the core workflow of the multi-agent system for
automated web data collection and processing of legal documents in Vietnamese.
"""

import sys
import os
import logging
from pathlib import Path
import asyncio
from typing import Dict, Any, Optional

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)

from autodata.core.auto import AutoData
from autodata.utils.cli import parse_arguments, validate_arguments


def debug_test_run():
    """Debug mode: test the full multi-agent workflow with a sample legal data collection task."""
    print("🧩 DEBUG MODE: Kiểm thử pipeline crawl và xử lý tài liệu pháp luật Việt Nam...")

    # Mô phỏng đối tượng arguments để test
    class TestArgs:
        # Đây là instruction thực tế của bạn
        instruction = (
            "Thu thập và xử lý dữ liệu liên quan đến 'Tài liệu thẩm định Dự án Luật Khoa học, "
            "Công nghệ và Đổi mới sáng tạo của Việt Nam năm 2025' "
            "từ trang web https://mst.gov.vn/van-ban-phap-luat/du-thao/2256.htm. "
            "Tải file PDF gốc, trích xuất từ khóa, sau đó tìm các bài viết hoặc bình luận "
            "của người dân về dự thảo luật này và lưu dữ liệu thành file CSV."
        )
        config = None
        log_level = "DEBUG"
        output = Path("autodata/test_output")
        verbose = True
        env_path = None

    try:
        args = TestArgs()
        validate_arguments(args)

        print(f"📘 Nhiệm vụ kiểm thử: {args.instruction}")
        print(f"⚙️ Mức log: {args.log_level}")
        print(f"📂 Thư mục kết quả: {args.output}")
        print(f"🔊 Verbose: {args.verbose}")
        print(f"🌍 File môi trường: {args.env_path or '.env (mặc định)'}")

        # Khởi tạo AutoData pipeline
        autodata = AutoData(
            config_path=args.config,
            log_level=args.log_level,
            output_dir=args.output,
            verbose=args.verbose,
            env_path=args.env_path,
        )

        print("🚀 Bắt đầu chạy AutoData (async)...")
        results = asyncio.run(autodata.arun(args.instruction))

        print("\n📊 Kết quả kiểm thử:")
        status = results.get("status", "unknown")
        print(f"Trạng thái: {status}")

        if status == "success":
            print("✅ Hoàn tất pipeline thành công!")
            print("Dữ liệu đã được lưu trong thư mục output.")
            print(results.get("results", "Không có kết quả chi tiết."))
        else:
            print(f"❌ Thất bại: {results.get('error', 'Lỗi không xác định')}")

    except Exception as e:
        print(f"💥 Lỗi trong quá trình debug: {e}")
        logger.exception("Debug test failed")


def main():
    """Main entry point for the AutoData CLI."""
    try:
        args = parse_arguments()
        validate_arguments(args)

        autodata = AutoData(
            config_path=args.config,
            log_level=args.log_level,
            output_dir=getattr(args, "output", None),
            verbose=getattr(args, "verbose", False),
            env_path=getattr(args, "env_path", None),
        )

        # ⚡ chạy async nếu có thể
        if hasattr(autodata, "arun"):
            results = asyncio.run(autodata.arun(args.instruction))
        else:
            results = autodata.run(args.instruction)

        # Hiển thị kết quả
        if results.get("status") == "success":
            print("🎯 Thu thập dữ liệu hoàn tất thành công!")
            print("\nKết quả:")
            print(results.get("results", "Không có dữ liệu trả về."))
        else:
            print(f"⚠️ Lỗi: {results.get('error', 'Không xác định')}")
            sys.exit(1)

    except ValueError as e:
        print(f"❌ Lỗi tham số: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Người dùng đã hủy tiến trình.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi: {e}")
        print(f"Đã xảy ra lỗi không mong đợi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 🔍 Chạy chế độ debug để test pipeline đầy đủ
    debug_test_run()
    # Nếu bạn muốn chạy qua CLI thật, chỉ cần comment dòng trên và bỏ comment dòng dưới:
    # main()
