# Anki Vocab App

Ứng dụng desktop giúp tạo bộ thẻ Anki từ danh sách từ vựng. Ứng dụng tự
tra nghĩa, câu ví dụ, bản dịch tiếng Việt và tạo audio; hình ảnh có thể
được thêm thủ công trong Anki.

## Tính năng

- Nhập từ trực tiếp hoặc từ file CSV.
- Tra dữ liệu từ điển và câu ví dụ trực tuyến.
- Tạo audio tiếng Anh và tiếng Việt bằng Edge TTS.
- Xuất mỗi lần chạy thành một file `.apkg` riêng.
- Lưu cache và dữ liệu ứng dụng ngoài repository.

## Yêu cầu

- Windows 10/11 (giao diện dùng Tkinter).
- Python 3.10 trở lên.
- Kết nối Internet khi cần tra dữ liệu hoặc tạo audio.

## Cài đặt từ source

Từ thư mục gốc project:

```powershell
py -m venv .venv
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
```

## Chạy ứng dụng

```powershell
& ".venv\Scripts\python.exe" -m anki_vocab_app
```

Sau khi cài editable, có thể dùng entrypoint:

```powershell
anki-vocab-app
```

## Kiểm thử

```powershell
& ".venv\Scripts\python.exe" -m pytest
```

## Build file EXE trên Windows

```powershell
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean AnkiVocabApp.spec
```

File build được tạo trong `dist/` và không được commit vào repository.

## Cách sử dụng

1. Mở ứng dụng.
2. Dán từ mới vào ô nhập, mỗi dòng một từ; hoặc chọn `Load CSV`.
3. Chọn `Generate Today's Deck`.
4. Import file `.apkg` được tạo vào Anki.

Mỗi file được nhập vào bộ thẻ `Anki Vocab App`. Dữ liệu runtime nằm tại:

- Deck: `%LOCALAPPDATA%\AnkiVocabApp\output`
- Audio: `%LOCALAPPDATA%\AnkiVocabApp\media\audio`
- Cache: `%LOCALAPPDATA%\AnkiVocabApp\cache`

Tên file deck có dạng:

```text
Vocabulary_YYYYMMDD_Action_YYYYMMDD_HHMMSS_hash.apkg
```

## Cấu trúc project

```text
src/
  anki_vocab_app/
    __main__.py       # python -m anki_vocab_app
    main.py           # giao diện Tkinter
    core.py           # luồng tạo deck
    anki_builder.py   # model và package Anki
    audio.py          # tạo audio
    dictionary.py     # tra từ điển và câu ví dụ
    translator.py     # dịch tiếng Việt
    validator.py      # đường dẫn và tiện ích dữ liệu
scripts/
  run_app.py          # launcher cho PyInstaller
tests/
  test_validator.py
pyproject.toml
requirements.txt
AnkiVocabApp.spec
```

## Đóng góp

Pull request và issue được hoan nghênh. Trước khi gửi pull request, hãy
chạy test và mô tả rõ thay đổi trong giao diện hoặc định dạng deck.
