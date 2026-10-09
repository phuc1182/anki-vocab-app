# Anki Vocab App

Ứng dụng desktop mã nguồn mở giúp tạo bộ thẻ Anki từ danh sách từ vựng
tiếng Anh. Ứng dụng tra dữ liệu từ điển local, tạo audio tiếng Anh và tiếng
Việt, sau đó xuất mỗi lần chạy thành một file `.apkg` riêng.

> Dự án hiện tập trung hỗ trợ Windows 10/11. Từ điển và dữ liệu dịch được tra
> offline. Chỉ audio Microsoft Edge TTS mới cần kết nối Internet.

## Tính năng

- Nhập từ trực tiếp hoặc nạp từ file CSV/TXT.
- Tra từ điển Anh–Việt SQLite offline làm nguồn chính, gồm IPA, loại từ,
  từng nghĩa tiếng Việt và ví dụ theo từng nghĩa.
- Dùng MDX, TAB và JSON tại máy người dùng làm fallback.
- Tạo audio bằng Microsoft Edge TTS.
- Tạo hai audio tiếng Anh của mỗi từ đồng thời sau khi tra cứu hoàn tất.
- Cache dữ liệu và audio để các lần chạy sau nhanh hơn.
- Xuất file `.apkg` tương thích với Anki.
- Cho phép đặt tên deck cha và tự tạo deck con cho các lần tạo tiếp theo.
- Cho phép người dùng tự thêm hình ảnh trong Anki.

## Dùng nhanh trên Windows

Người dùng không cần cài Python hoặc mở terminal:

1. Mở trang [GitHub Releases](https://github.com/phuc1182/anki-vocab-app/releases).
2. Tải `AnkiVocabApp.exe` từ phiên bản mới nhất.
3. Bấm đúp vào file để mở ứng dụng.



Windows Defender có thể cảnh báo với file EXE tự phát hành. Chỉ chọn
`More info` → `Run anyway` khi file được tải từ Releases chính thức của
repository này.

Từ điển offline và dữ liệu dịch được đóng gói sẵn trong ứng dụng. Internet
chỉ cần khi tạo audio bằng Microsoft Edge TTS.

## Yêu cầu khi chạy từ source

- Windows 10/11
- Python 3.10 trở lên
- Kết nối Internet khi tạo audio mới bằng Microsoft Edge TTS

## Cài đặt cho contributor

Mở PowerShell tại thư mục gốc project:

```powershell
python -m venv .venv
& ".venv\Scripts\python.exe" -m ensurepip --upgrade
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
```

Nếu máy có Python Launcher, có thể thay `python` bằng `py`. Nếu lệnh
`python` không hoạt động, hãy cài Python 3.10+ và bật tùy chọn
`Add Python to PATH`, sau đó mở lại PowerShell.

## Chạy ứng dụng từ source

```powershell
& ".venv\Scripts\python.exe" -m anki_vocab_app
```

Sau khi cài editable, entrypoint sau cũng hoạt động:

```powershell
anki-vocab-app
```

## Kiểm thử

```powershell
& ".venv\Scripts\python.exe" -m pytest
```

Trước khi mở pull request, hãy chạy test và kiểm tra thay đổi bằng:

```powershell
git diff --check
```

## Build Windows EXE

Build local:

```powershell
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "AnkiVocabApp.spec"
```

File kết quả nằm tại:

```text
dist/AnkiVocabApp.exe
```

`dist/` và `build/` là artefact sinh tự động, không commit vào repository.

### Tạo GitHub Release

Workflow [release-windows.yml](.github/workflows/release-windows.yml) sẽ
tự build và đính kèm EXE khi push tag dạng `v*`:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

## Cách sử dụng

1. Mở ứng dụng.
2. Nhập tên bộ thẻ Anki. Để trống sẽ dùng `Anki Vocab App`.
3. Dán danh sách từ, mỗi dòng một từ; hoặc chọn `Load CSV`.
4. Chọn `Generate Today's Deck`.
5. Chờ ứng dụng tạo xong file `.apkg`.
6. Mở Anki và import file vừa tạo.

Từ trùng nhau không phân biệt hoa thường sẽ chỉ được xử lý một lần. Từ đã
có cache hợp lệ sẽ được dùng lại. Nếu từ chưa có trong từ điển local, ứng dụng
sẽ dừng với lỗi rõ ràng thay vì âm thầm gọi dịch vụ online.

### Nạp từ điển local

Ứng dụng có một bộ dữ liệu mẫu nhỏ được đóng gói sẵn. Để dùng bộ từ điển
giống Query Word hoặc dữ liệu đã tải về, tạo file:

```text
%LOCALAPPDATA%\AnkiVocabApp\dictionary.json
```

File này là một JSON object, dùng từ làm key và bốn trường bắt buộc:

```json
{
  "serendipity": {
    "meaning": "The occurrence of a fortunate discovery by chance.",
    "pronounce": "ˌserənˈdipitē",
    "sentence": "Finding that old book was a happy serendipity.",
    "vietnamese": "sự tình cờ may mắn"
  }
}
```

File người dùng sẽ ghi đè dữ liệu mẫu khi trùng từ. Có thể dùng bất kỳ công cụ
nào để xuất dữ liệu từ điển đã tải sẵn về đúng định dạng này; ứng dụng không
đọc mạng và không tự tải dữ liệu.

### Dùng từ điển MDict

Cài `mdict-utils` khi chạy từ source:

```powershell
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
```

Đặt một file từ điển tại:

```text
%LOCALAPPDATA%\AnkiVocabApp\dictionary.mdx
```

Ứng dụng cũng hỗ trợ bộ Anh–Việt dạng `.tab` đã tải sẵn tại
`%LOCALAPPDATA%\AnkiVocabApp\dictionary.tab`. Khi file này tồn tại, app tự
xây chỉ mục SQLite một lần trong thư mục `cache`, sau đó các lần tra sau chỉ
đọc index local.

Ứng dụng ưu tiên file từ điển theo thứ tự `dictionary.mdx`, `dictionary.tab`,
rồi `dictionary.json`.

Khi tra từ, app sẽ đọc trực tiếp entry trong file MDX và cache tối đa 512
lookup gần nhất trong bộ nhớ. File `dictionary.json` vẫn được dùng để bổ sung
trường `vietnamese` (và có thể ghi đè trường MDX). Vì MDX thường là
English-English, mỗi từ MDX cần có bản dịch tiếng Việt tương ứng trong JSON:

```json
{
  "serendipity": {
    "vietnamese": "sự tình cờ may mắn"
  }
}
```

Entry MDX phải có nội dung nghĩa và bản dịch tiếng Việt trong JSON. Nếu app
không tìm thấy file MDX hoặc entry, nó sẽ báo lỗi thay vì quay lại tra online.

### Quy tắc đặt tên deck

- Lần đầu dùng một tên, file được tạo vào deck đúng tên đó. Ví dụ:
  `English Vocabulary`.
- Các lần sau dùng cùng tên, file được tạo vào deck con dạng:
  `English Vocabulary::YYYY-MM-DD HH:MM:SS hash`.
- Ứng dụng lưu lịch sử tên deck trong cache cục bộ. Ứng dụng không đọc trực
  tiếp collection của Anki, vì vậy nếu deck đã tồn tại trong Anki nhưng chưa
  từng được tạo bởi ứng dụng này, lần đầu chạy trên máy đó vẫn được xem là
  deck mới.

## Dữ liệu runtime

Trên Windows, dữ liệu runtime nằm ngoài repository:

```text
%LOCALAPPDATA%\AnkiVocabApp\
├── Anki Vocab App\   # Các file .apkg
├── media\audio\      # Các file audio
├── cache\            # Cache SQLite
└── input\            # Dữ liệu input mặc định
```

Database chính được đóng gói tại
`src/anki_vocab_app/data/dictionary_en_vi.db`. Ứng dụng đọc các bảng
`words`, `definitions`, `word_definitions` và `pronunciations` để lấy IPA,
loại từ, từng nghĩa tiếng Việt và ví dụ tương ứng.

Thứ tự nguồn từ điển là:

1. SQLite offline đi kèm ứng dụng.
2. MDX tại `%LOCALAPPDATA%\AnkiVocabApp\dictionary.mdx`.
3. TAB tại `%LOCALAPPDATA%\AnkiVocabApp\dictionary.tab`.
4. JSON tại `%LOCALAPPDATA%\AnkiVocabApp\dictionary.json`.

Database được lấy từ
[skypediacode/english-vietnamese-dictionary](https://github.com/skypediacode/english-vietnamese-dictionary)
và cấp phép theo **CC BY-SA 4.0**. Dữ liệu này ghi công các nguồn upstream
được liệt kê trong
[ATTRIBUTION.md](https://github.com/skypediacode/english-vietnamese-dictionary/blob/main/ATTRIBUTION.md).

## Giấy phép

Giấy phép được tách theo loại nội dung:

- **Mã nguồn ứng dụng:** [MIT License](LICENSE).
- **Database từ điển tích hợp:** [CC BY-SA 4.0](DATA-LICENSE.md).

MIT chỉ áp dụng cho mã nguồn gốc của ứng dụng, không áp dụng cho database
từ điển hoặc các dữ liệu upstream đi kèm. Khi phân phối lại ứng dụng có chứa
database, hãy giữ lại [`LICENSE`](LICENSE), [`DATA-LICENSE.md`](DATA-LICENSE.md)
và các thông tin ghi công bắt buộc.

Mỗi lần tạo deck sẽ sinh một file mới, ví dụ:

```text
Anki Vocab App/
├── Vocabulary_20261007_Action_101500_a1b2c3d4.apkg
└── Vocabulary_20261007_Action_103000_e5f6a7b8.apkg
```

Trong Anki, các deck được tổ chức theo dạng:

```text
Anki Vocab App::YYYY-MM-DD HH:MM:SS hash
```

## Cấu trúc repository

```text
src/anki_vocab_app/
├── __main__.py       # python -m anki_vocab_app
├── main.py           # giao diện Tkinter
├── core.py           # luồng tạo deck và cache
├── anki_builder.py   # model và package Anki
├── audio.py          # tạo audio và retry
├── dictionary.py     # tra từ điển local và câu ví dụ
├── local_dictionary.py # nạp dữ liệu JSON local
├── offline_dictionary.py # truy vấn SQLite Anh–Việt offline
├── mdx_dictionary.py # fallback MDict
├── tab_dictionary.py # fallback TAB
├── translator.py     # lấy tiếng Việt từ dữ liệu local
└── validator.py      # đường dẫn và tiện ích dữ liệu
src/anki_vocab_app/data/dictionary_en_vi.db # database offline chính
scripts/run_app.py    # launcher cho PyInstaller
tests/                # test tự động
pyproject.toml        # metadata và cấu hình project
AnkiVocabApp.spec     # cấu hình PyInstaller
```

## Đóng góp

Issue, bug report và pull request đều được hoan nghênh.

Khi báo lỗi, vui lòng cung cấp:

- Hệ điều hành và phiên bản Python hoặc phiên bản EXE.
- Các bước tái hiện lỗi.
- Nội dung lỗi trong cửa sổ ứng dụng hoặc log.
- Danh sách từ tối thiểu để tái hiện nếu lỗi liên quan đến một từ cụ thể.

Khi gửi pull request:

1. Tạo branch riêng cho thay đổi.
2. Giữ thay đổi tập trung vào một mục tiêu.
3. Chạy test và `git diff --check`.
4. Cập nhật README nếu thay đổi cách cài đặt hoặc sử dụng.

## License

Repository hiện chưa khai báo file `LICENSE`. Hãy bổ sung giấy phép trước
khi phân phối chính thức hoặc cho phép sử dụng lại code ở quy mô lớn.
