"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Chủ đề:
    Chính sách phát triển du lịch Việt Nam.

Tài liệu:
    1. Công văn 1560/VPCP-KGVX về Chương trình phát triển
       du lịch Việt Nam giai đoạn 2021–2026.

    2. Quyết định 147/QĐ-TTg phê duyệt Chiến lược phát triển
       du lịch Việt Nam đến năm 2030.

    3. Nghị quyết 26-NQ/TW về phát triển du lịch Việt Nam
       trở thành ngành kinh tế mũi nhọn trong kỷ nguyên mới.

Các file gốc được lưu tại:
    data/landing/legal/
"""

from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "landing" / "legal"

# Giới hạn dung lượng mỗi tài liệu là 50 MB.
MAX_FILE_SIZE = 50 * 1024 * 1024

# Tên file không dấu, mô tả đúng nội dung tài liệu.
SOURCES = {
    "cong-van-1560-vpcp-kgvx-chuong-trinh-phat-trien-du-lich-2021-2026.pdf": (
        "https://datafiles.chinhphu.vn/cpp/files/vbpq/"
        "2022/03/1560-kgvx.signed.pdf"
    ),
    "quyet-dinh-147-qd-ttg-chien-luoc-phat-trien-du-lich-den-2030.pdf": (
        "https://vietnamtourism.gov.vn/docs/download/908"
    ),
    "nghi-quyet-26-nq-tw-phat-trien-du-lich-viet-nam.pdf": (
        "https://tulieuvankien.dangcongsan.vn/upload/"
        "2006988/20260827/nqtw26_signed_49491.pdf"
    ),
}


def setup_directory() -> None:
    """Tạo thư mục lưu các tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def create_http_session() -> requests.Session:
    """Tạo HTTP session có cơ chế thử lại khi lỗi mạng tạm thời."""
    retry_policy = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )

    adapter = HTTPAdapter(max_retries=retry_policy)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # User-Agent thông thường, không dùng để vượt WAF.
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (compatible; "
                "PolicyDocumentCollector/1.0; educational-purpose)"
            )
        }
    )

    return session


def validate_document(file_path: Path) -> None:
    """
    Kiểm tra chữ ký đầu file để tránh lưu nhầm trang HTML
    hoặc thông báo lỗi dưới tên .pdf/.docx.
    """
    with file_path.open("rb") as file:
        signature = file.read(4)

    suffix = file_path.suffix.lower()

    if suffix == ".pdf" and not signature.startswith(b"%PDF"):
        raise ValueError(
            f"{file_path.name} không phải file PDF hợp lệ. "
            "Website có thể đã trả về một trang HTML."
        )

    # DOCX thực chất là một tệp ZIP nên bắt đầu bằng PK.
    if suffix == ".docx" and not signature.startswith(b"PK"):
        raise ValueError(
            f"{file_path.name} không phải file DOCX hợp lệ."
        )


def download_file(
    session: requests.Session,
    filename: str,
    url: str,
) -> None:
    """Tải một tài liệu và lưu an toàn vào thư mục dữ liệu."""
    destination = DATA_DIR / filename
    temporary_file = destination.with_suffix(destination.suffix + ".part")

    if destination.exists():
        try:
            validate_document(destination)
            print(f"Skipped: {filename} (file da ton tai va hop le)")
            return
        except ValueError:
            print(f"Replacing invalid file: {filename}")

    try:
        print(f"Downloading: {filename}")

        with session.get(
            url,
            timeout=(10, 60),
            stream=True,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_FILE_SIZE:
                raise ValueError(
                    f"{filename} vượt quá giới hạn "
                    f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
                )

            downloaded_size = 0

            with temporary_file.open("wb") as output_file:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue

                    downloaded_size += len(chunk)

                    if downloaded_size > MAX_FILE_SIZE:
                        raise ValueError(
                            f"{filename} vượt quá giới hạn "
                            f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
                        )

                    output_file.write(chunk)

        validate_document(temporary_file)

        # Chỉ thay file đích sau khi tài liệu đã tải và kiểm tra thành công.
        temporary_file.replace(destination)

        size_mb = destination.stat().st_size / (1024 * 1024)
        print(f"Saved: {destination} ({size_mb:.2f} MB)")

    except Exception:
        # Xóa file tải dở nếu có lỗi.
        temporary_file.unlink(missing_ok=True)
        raise


def download_documents() -> None:
    """Tải ít nhất 3 tài liệu PDF từ các nguồn công khai."""
    session = create_http_session()
    successful_downloads = 0
    errors: list[str] = []

    try:
        for filename, url in SOURCES.items():
            try:
                download_file(session, filename, url)
                successful_downloads += 1
            except (requests.RequestException, OSError, ValueError) as error:
                errors.append(f"{filename}: {error}")
                print(f"Failed: {filename}")
                print(f"Reason: {error}")
    finally:
        session.close()

    print(
        f"\nResult: {successful_downloads}/{len(SOURCES)} "
        "documents are available."
    )

    if errors:
        error_details = "\n".join(f"- {error}" for error in errors)
        raise RuntimeError(
            "Không thể thu thập đầy đủ tài liệu:\n"
            f"{error_details}\n"
            "Hãy tải thủ công từ trang nguồn nếu website đang chặn yêu cầu."
        )

    print("Task 1 completed successfully.")


def main() -> None:
    """Khởi tạo thư mục và tiến hành tải tài liệu."""
    setup_directory()
    download_documents()


if __name__ == "__main__":
    main()