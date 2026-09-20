"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path
import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    sources = {
        "cv_1560_vpcp_mo_cua_du_lich.pdf": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/03/1560-kgvx.signed.pdf",
        "vb_908_cuc_du_lich.pdf": "https://vietnamtourism.gov.vn/docs/download/908",
        "nq_08_bo_chinh_tri_du_lich.pdf": "https://tulieuvankien.dangcongsan.vn/upload/2006988/20260827/nqtw26_signed_49491.pdf",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for filename, url in sources.items():
        file_path = DATA_DIR / filename
        if file_path.exists() and file_path.stat().st_size > 1024:
            print(f"Skipped (already exists): {filename} ({file_path.stat().st_size} bytes)")
            continue

        print(f"Downloading {filename} from {url}...")
        downloaded = False
        for attempt in range(1, 4):
            try:
                response = requests.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                file_path.write_bytes(response.content)
                print(f"Successfully saved {filename} ({len(response.content)} bytes)")
                downloaded = True
                break
            except Exception as err:
                print(f"Attempt {attempt}/3 failed for {filename}: {err}")
                if attempt < 3:
                    import time
                    time.sleep(2)
        if not downloaded:
            raise RuntimeError(f"Failed to download {filename} after 3 attempts.")


if __name__ == "__main__":
    setup_directory()
    download_documents()
