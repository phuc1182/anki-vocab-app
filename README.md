# anki-vocab-app

App nhập từ mới, tự tạo audio, để người dùng tự thêm hình ảnh, và xuất file Anki `.apkg` riêng cho mỗi lần chạy.

## Chạy app

Từ thư mục gốc của project, chạy:

```powershell
& ".venv\Scripts\python.exe" backend\main.py
```

## Mở bằng file EXE

Bấm đúp vào [AnkiVocabApp.exe](AnkiVocabApp.exe) ở thư mục gốc của project.
Các file dữ liệu người dùng được lưu ngoài project tại `%LOCALAPPDATA%\AnkiVocabApp\`.
Vì vậy file output, audio và cache sẽ không bị push lên GitHub.

Để build lại trên Windows:

```powershell
& ".venv\Scripts\python.exe" -m pip install pyinstaller
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name AnkiVocabApp backend\main.py
Copy-Item "dist\AnkiVocabApp.exe" ".\AnkiVocabApp.exe" -Force
```

Nếu muốn chạy trực tiếp module giao diện:

```powershell
& ".venv\Scripts\python.exe" -m app.main
```

## Cách dùng hằng ngày

1. Mở app.
2. Dán từ mới vào ô nhập, mỗi dòng một từ.
3. Hoặc bấm `Load CSV` để chọn file danh sách từ ở bất kỳ vị trí nào.
4. Bấm `Generate Today's Deck`.
5. Chờ app tạo xong file `.apkg`.
6. Import file đó vào Anki.

Các file `.apkg` do app tạo sẽ luôn nhập vào bộ thẻ riêng `Anki Vocab App`.
Lần đầu Anki sẽ tạo bộ thẻ này; các lần sau sẽ tiếp tục thêm thẻ vào đúng bộ đó.

## File được tạo ra

- File deck: `%LOCALAPPDATA%\AnkiVocabApp\output`
- Audio: `%LOCALAPPDATA%\AnkiVocabApp\media\audio`
- Cache: `%LOCALAPPDATA%\AnkiVocabApp\cache`

Mỗi lần tạo sẽ sinh một file `.apkg` mới, không ghi đè file cũ. Tên file có dạng:

```text
Vocabulary_YYYYMMDD_Action_YYYYMMDD_HHMMSS_hash.apkg
```

## Cách nhập từ

Mỗi dòng là một từ.

Ví dụ:

```text
run
walk
blueprint
```

Bạn có thể dùng nút `Load CSV` để chọn file từ ở bất kỳ thư mục nào.

## Import vào Anki

1. Mở Anki.
2. Chọn `Import File`.
3. Chọn file `.apkg` mới trong [output](output).
4. Import xong là dùng được.

## Cấu trúc chính

```text
app/
  main.py
  core.py
  dictionary.py
  translator.py
  audio.py
  anki_builder.py
  validator.py
backend/
  main.py
input/
  words.csv
output/
media/
  audio/
  images/
cache/
requirements.txt
```

## Ghi chú

- Âm thanh được app tự sinh; trường ảnh trong Anki để trống để bạn tự thêm ảnh.
- Thẻ chỉ hiển thị từ, phát âm, câu ví dụ và nghĩa tiếng Việt; không hiển thị phần meaning tiếng Anh.
- Phát âm được lấy từ phiên âm IPA phù hợp nhất mà từ điển cung cấp và được làm mới khi có dữ liệu tốt hơn.
- Ví dụ tiếng Anh được ưu tiên lấy từ từ điển, sau đó tra Google Search và kho câu thật Tatoeba.
- Nếu không có mạng, phần tra từ điển có thể thiếu nghĩa hoặc ví dụ.
- Nếu muốn tạo deck theo ngày, chọn file danh sách từ bằng nút `Load CSV` rồi chạy lại.
